# gdzienasniadanie.pl MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a Kraków breakfast-place map with combinable filters, distance ordering, accounts, ratings, saved list, user submissions and admin editing, deployed to Fly before 2026-12-06.

**Architecture:** Server-rendered Django (templates, no SPA). One map page loads Leaflet + OSM tiles and fetches filtered places from a JSON endpoint. Filtering, open-now and distance logic live in a pure-Python service module (SQLite, ~50 places, no PostGIS). Django auth and admin cover login and FR-011.

**Tech Stack:** Python >=3.14, Django >=6.1.2, SQLite (Postgres on Fly if needed), Leaflet 1.9.4 via CDN, vanilla JS, `uv`, mypy strict + django-stubs, Fly.io, GitHub Actions.

**Spec:** `context/foundation/prd.md` (supporting: `shape-notes.md`, `tech-stack.md`)

## Global Constraints

- All new functions carry parameter and return type hints; `uv run mypy .` reports zero errors before each commit.
- Apps are top-level siblings of `config/`, each registered in `INSTALLED_APPS`.
- Never write to `context/archive/`.
- Only Kraków offered; `Place.city` stays in the model (default `"Kraków"`).
- Opening hours shown for a place are no older than 90 days (NFR).
- Latest two major versions of mainstream mobile and desktop browsers; no offline, no i18n, no native app.
- Anonymous: browse + filter only. Rate/save/submit gated by login (redirect to login with `next`).
- Out of MVP: pricing/menu, transit time, Instagram scraping, approval queue, FR-009 "going today".
- Hard deadline 2026-12-06 (~24 after-hours hours left as of 2026-11-08): cut order if late is Task 10 → Task 9 → Task 8.

## Decisions Taken (PRD open questions; confirm or change before Task 1)

- (Confirmed 2026-11-08) Rating scale: integer 1–5, one rating per user per place (update replaces). Cold start: unrated places show "no ratings yet" and are hidden by the min-rating filter unless an "Include unrated" checkbox is ticked (`include_unrated=1`; default unticked).
- (Confirmed) Submit threshold 3; food types sweet/vegan/vegetarian; straight-line distance.
- (Confirmed) Sign-in: username + password, plus required unique email at registration; login accepts username OR email (custom auth backend `accounts.backends.EmailOrUsernameBackend`).
- Submit threshold: `settings.MIN_RATINGS_TO_SUBMIT = 3` places rated by the user.
- Food types fixed set: `sweet`, `vegan`, `vegetarian` (data model is a table, so more can be added in admin). Admin tags places.
- Distance: straight-line haversine. Default reference point: Kraków Rynek Główny (50.0614, 19.9366).
- Hours: weekly intervals per weekday in `Europe/Warsaw`; `hours_verified_at` date per place; admin edits refresh it.
- Sign-in: Django username/password (email optional), no social login.
- Details view: address, hours, food types, rating + count, Instagram link, "Open in Google Maps" link by coordinates.

## Review Focus

- Place open past midnight (e.g. 22:00–02:00) on the next day's early hours → still "open now" at 01:00.
- Place with no hours entered → excluded from open-now filter, not a crash.
- Filter combination with zero matches → explanatory empty state (US-01), map cleared.
- Rating a place twice → one rating, aggregate and count correct; unrated place has count 0, no division error.
- Reference point missing/garbage lat/lng in query string → 400 or fallback to default, never 500.

---

### Task 1: Settings hardening and test baseline

**Files:**
- Modify: `config/settings.py`
- Create: `config/tests.py`, `.env.example`

**Interfaces:**
- Produces: env-driven `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `TIME_ZONE="Europe/Warsaw"`, `LANGUAGE_CODE="pl"` is NOT set (English UI), `MIN_RATINGS_TO_SUBMIT: int`.

- [ ] **Step 1: Write failing test** `config.tests.SettingsTests.test_secret_key_comes_from_env` (set env `DJANGO_SECRET_KEY`, reload settings module, assert equality) and `test_timezone_is_warsaw`.
- [ ] **Step 2: Run** `uv run manage.py test config` → FAIL.
- [ ] **Step 3: Implement** reading `DJANGO_SECRET_KEY`, `DJANGO_DEBUG` (default False), `DJANGO_ALLOWED_HOSTS` (comma list), `DATABASE_PATH`; raise `ImproperlyConfigured` if no secret key and not DEBUG. Add `.env.example`.
- [ ] **Step 4: Run** tests + `uv run mypy .` → PASS, 0 errors.
- [ ] **Step 5: Commit** `chore: env-driven settings`.

### Task 2: Place, FoodType, OpeningInterval models + admin (FR-011, data for FR-001–005)

**Files:**
- Create: app `places` (`uv run manage.py startapp places`), `places/models.py`, `places/admin.py`, `places/tests/test_models.py`
- Modify: `config/settings.py` (INSTALLED_APPS)

**Interfaces:**
- Produces:
  - `FoodType(slug: SlugField unique, name: CharField)`
  - `Place(name, address, city="Kraków", latitude: FloatField, longitude: FloatField, instagram_url: URLField blank, food_types: M2M[FoodType], hours_verified_at: DateField null, created_by: FK[User] null, created_at)`
  - `OpeningInterval(place: FK related_name="intervals", weekday: int 0=Mon..6=Sun, opens: TimeField, closes: TimeField)`; `closes <= opens` means past midnight.

- [ ] **Step 1: Failing tests:** `test_place_str_is_name`, `test_interval_rejects_weekday_7` (full_clean raises), `test_city_defaults_to_krakow`.
- [ ] **Step 2: Run** `uv run manage.py test places` → FAIL.
- [ ] **Step 3: Implement** models, migrations, admin with `OpeningInterval` inline, `filter_horizontal` for food types, edit/delete enabled; admin `save_model` sets `hours_verified_at = today` when intervals changed (`save_related` hook). Data migration creating the three FoodTypes.
- [ ] **Step 4: Run** tests + mypy → PASS.
- [ ] **Step 5: Commit** `feat(places): models and admin`.

### Task 3: Filtering domain service (FR-002, 003, 004, 013)

**Files:**
- Create: `places/services.py`, `places/tests/test_services.py`

**Interfaces:**
- Consumes: Task 2 models.
- Produces:
  - `is_open_at(place: Place, moment: datetime) -> bool` (aware datetime, converted to Europe/Warsaw; handles past-midnight intervals from previous weekday)
  - `haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float`
  - `@dataclass(frozen=True) PlaceFilter(open_now_at: datetime | None, open_at: tuple[int, time] | None, food_types: frozenset[str], min_rating: float | None, include_unrated: bool, origin: tuple[float, float])`
  - `@dataclass(frozen=True) PlaceResult(place: Place, distance_km: float, avg_rating: float | None, rating_count: int)`
  - `search_places(f: PlaceFilter) -> list[PlaceResult]` sorted by `distance_km` ascending; food types combine as AND-any? → **place must have at least one selected type**; min_rating excludes unrated.

- [ ] **Step 1: Failing tests** (build places with `Place.objects.create`): `test_open_at_2300_interval_closing_0200_is_open_at_0100_next_day`, `test_place_without_intervals_not_open`, `test_closed_at_closing_minute` (closes exclusive), `test_haversine_rynek_to_wawel_about_0_5km` (0.4–0.7), `test_search_orders_by_distance`, `test_filters_combine_open_vegan_min_rating`, `test_min_rating_excludes_unrated_by_default`, `test_include_unrated_keeps_unrated_places`, `test_no_match_returns_empty_list`.
- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement.** Rating aggregate is read via annotation on `Avg`/`Count` of `ratings` related name defined in Task 8; until then annotate with constants `None`/`0` behind a single `_rating_annotations()` helper that Task 8 replaces. Prefetch intervals and food types to avoid N+1.
- [ ] **Step 4: Run** tests + mypy → PASS.
- [ ] **Step 5: Commit** `feat(places): filter and distance service`.

### Task 4: Seed import command (FR-012)

**Files:**
- Create: `places/management/commands/import_places.py`, `places/data/seed.json` (30–50 curated places, hand-collected from OSM/Google Maps; check source terms before committing data), `places/tests/test_import.py`

**Interfaces:**
- Produces: `uv run manage.py import_places [path]`; JSON items `{name, address, lat, lng, instagram?, food_types: [slug], hours: {"mon": [["08:00","14:00"]], ...}}`. Idempotent: upsert by `(name, address)`; sets `hours_verified_at=today`.

- [ ] **Step 1: Failing tests:** `test_import_creates_places_and_intervals`, `test_import_twice_does_not_duplicate`, `test_unknown_food_type_slug_raises_commanderror_and_rolls_back`.
- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement** inside `transaction.atomic`.
- [ ] **Step 4: Run** tests + mypy → PASS. Then run the command on dev DB with real seed.
- [ ] **Step 5: Commit** `feat(places): seed import`.

### Task 5: Map page and places JSON API (FR-001, 013, US-01)

**Files:**
- Create: `places/views.py`, `places/urls.py`, `places/templates/places/map.html`, `places/static/places/map.js`, `places/static/places/map.css`, `places/tests/test_views.py`
- Modify: `config/urls.py` (include places at `""`)

**Interfaces:**
- Consumes: `search_places`, `PlaceFilter`.
- Produces: `GET /` (map page, side panel with filters); `GET /api/places/?open_now=1&food=vegan&food=sweet&min_rating=4&include_unrated=1&lat=..&lng=..` → `{"results":[{"id","name","lat","lng","distance_km","avg_rating","rating_count","food_types":[...],"is_open":bool}], "count": int}`. Invalid `lat`/`lng`/`min_rating` → 400 `{"error": str}`. Missing lat/lng → default origin.

- [ ] **Step 1: Failing tests:** `test_api_returns_matching_places_sorted_by_distance`, `test_api_filters_combine`, `test_api_bad_lat_returns_400`, `test_api_no_matches_returns_empty_list_count_0`, `test_map_page_renders_200_for_anonymous`.
- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement** views and template. JS: Leaflet map centered on Rynek, markers rebuilt on every filter change (fetch), clicking the map sets the reference pin, "Use my location" via `navigator.geolocation` (denied → keep default, show message), list panel ordered by distance, empty state text "No places match these filters — try removing one." when `count == 0`. Use `escapeHTML` for all place text (user-submitted content, XSS).
- [ ] **Step 4: Run** tests + mypy; manually verify in the browser (Sunday-morning flow: open now + vegan + min rating).
- [ ] **Step 5: Commit** `feat(places): map page and API`.

### Task 6: Place details (FR-005)

**Files:**
- Create: `places/templates/places/detail.html`; Modify: `places/views.py`, `places/urls.py`; Test: `places/tests/test_views.py`

**Interfaces:**
- Produces: `GET /places/<int:pk>/` showing address, weekly hours, food types, rating + count, optional Instagram link (`rel="noopener nofollow"`), Google Maps link `https://www.google.com/maps?q=<lat>,<lng>`. Map popup links here.

- [ ] **Step 1: Failing tests:** `test_detail_shows_hours_and_rating_count`, `test_detail_hides_instagram_when_blank`, `test_detail_404_unknown_place`.
- [ ] **Step 2–4:** run (FAIL), implement, run (PASS) + mypy.
- [ ] **Step 5: Commit** `feat(places): detail view`.

### Task 7: Accounts (FR-006) and login gating

**Files:**
- Create: app `accounts`, `accounts/forms.py` (`RegisterForm(UserCreationForm)`), `accounts/views.py`, `accounts/urls.py`, templates `registration/login.html`, `registration/register.html`, `accounts/tests.py`
- Modify: `config/urls.py` (`accounts/` incl. `django.contrib.auth.urls`), `config/settings.py` (`LOGIN_URL="login"`, `LOGIN_REDIRECT_URL="/"`)

**Interfaces:**
- Produces: `/accounts/register/`, `/accounts/login/`, `/accounts/logout/` (POST). Gated views use `@login_required`, redirecting to `/accounts/login/?next=...`.

- [ ] **Step 1: Failing tests:** `test_register_creates_user_and_logs_in`, `test_register_rejects_duplicate_username`, `test_register_requires_unique_email_case_insensitive`, `test_login_with_email`, `test_login_with_username`, `test_login_redirects_to_next`. `RegisterForm` adds required `email`; `EmailOrUsernameBackend.authenticate(request, username=None, password=None, **kw) -> User | None` registered in `AUTHENTICATION_BACKENDS` before `ModelBackend`.
- [ ] **Step 2–4:** run (FAIL), implement, run (PASS) + mypy. Keep Django's default password validators on.
- [ ] **Step 5: Commit** `feat(accounts): register and login`.

### Task 8: Ratings (FR-007)

**Files:**
- Create: app `engagement`, `engagement/models.py` (`Rating`), `engagement/views.py`, `engagement/urls.py`, `engagement/tests/test_ratings.py`
- Modify: `places/services.py` (replace `_rating_annotations()`), `detail.html`

**Interfaces:**
- Produces: `Rating(user FK, place FK related_name="ratings", value: PositiveSmallIntegerField 1..5, created_at, updated_at)`, `UniqueConstraint(user, place)`, `CheckConstraint 1<=value<=5`; `POST /places/<pk>/rate/` with `value` (login required) → upsert, redirect to detail.

- [ ] **Step 1: Failing tests:** `test_rate_requires_login`, `test_rating_twice_updates_single_row`, `test_value_6_rejected`, `test_aggregate_avg_and_count_on_detail`, `test_unrated_place_shows_no_ratings_yet`, `test_min_rating_filter_uses_real_ratings` (extends Task 3 service).
- [ ] **Step 2–4:** run (FAIL), implement with `update_or_create`, run (PASS) + mypy.
- [ ] **Step 5: Commit** `feat(engagement): ratings`.

### Task 9: Saved list (FR-008)

**Files:**
- Modify: `engagement/models.py` (`SavedPlace`), `engagement/views.py`, `engagement/urls.py`, `detail.html`; Create: `engagement/templates/engagement/saved.html`, `engagement/tests/test_saved.py`

**Interfaces:**
- Produces: `SavedPlace(user, place, created_at)` unique pair; `POST /places/<pk>/save/` (toggle add), `POST /places/<pk>/unsave/`, `GET /saved/` (own list only, login required).

- [ ] **Step 1: Failing tests:** `test_save_requires_login`, `test_saving_twice_keeps_one_row`, `test_unsave_removes`, `test_saved_page_lists_only_own_places`.
- [ ] **Step 2–4:** run (FAIL), implement, run (PASS) + mypy.
- [ ] **Step 5: Commit** `feat(engagement): saved list`.

### Task 10: User place submission (FR-010)

**Files:**
- Create: `places/forms.py` (`PlaceSubmissionForm`), `places/templates/places/submit.html`; Modify: `places/views.py`, `places/urls.py`; Test: `places/tests/test_submit.py`

**Interfaces:**
- Consumes: `Rating` count per user, `settings.MIN_RATINGS_TO_SUBMIT`.
- Produces: `GET/POST /places/new/` (login required). Fields: name, address, lat/lng (picked by clicking a Leaflet map, also editable), food types, optional Instagram URL. Publishes immediately with `created_by=request.user`, no hours (so excluded from open-now until admin adds them). Under threshold → 403-style page explaining "rate N more places".

- [ ] **Step 1: Failing tests:** `test_submit_blocked_below_threshold`, `test_submit_publishes_immediately_at_threshold`, `test_submit_rejects_coordinates_outside_krakow_bbox` (lat 49.9–50.2, lng 19.7–20.2), `test_submit_rejects_non_http_instagram_url`.
- [ ] **Step 2–4:** run (FAIL), implement, run (PASS) + mypy.
- [ ] **Step 5: Commit** `feat(places): user submissions`.

### Task 11: Hours freshness (NFR 90 days)

**Files:**
- Modify: `places/models.py` (`Place.hours_are_stale(today: date) -> bool`), `places/admin.py` (list filter "hours older than 90 days"), `detail.html` ("hours last verified <date>" and warning when stale); Test: `places/tests/test_models.py`

**Interfaces:**
- Produces: stale = `hours_verified_at is None or today - hours_verified_at > 90 days`. API field `is_open` becomes `None` for stale places, and the open-now filter excludes them.

- [ ] **Step 1: Failing tests:** `test_stale_after_91_days`, `test_not_stale_at_90_days`, `test_none_verified_is_stale`, `test_open_now_filter_excludes_stale_places`.
- [ ] **Step 2–4:** run (FAIL), implement, run (PASS) + mypy.
- [ ] **Step 5: Commit** `feat(places): hours freshness`.

### Task 12: Guardrails, CI and Fly deploy

**Files:**
- Create: `Dockerfile`, `fly.toml`, `.github/workflows/ci.yml`, `.github/workflows/deploy.yml`, `templates/privacy.html` + route `/privacy/`
- Modify: `config/settings.py` (`SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_HSTS_SECONDS` when not DEBUG; WhiteNoise for static; `CSRF_TRUSTED_ORIGINS` from env), `pyproject.toml` (add `whitenoise`, `gunicorn`)

**Interfaces:**
- Produces: CI (`uv sync`, `uv run manage.py test`, `uv run mypy .`, `uv run manage.py check --deploy` with prod env) on PR; deploy to Fly on merge to main with a SQLite volume mounted at `DATABASE_PATH`; `release_command = "python manage.py migrate"`.

- [ ] **Step 1: Failing test:** `config.tests.test_privacy_page_is_public` (200, mentions what is stored: username, email, ratings, saved places, and how to delete the account by contacting the author).
- [ ] **Step 2–3:** run (FAIL), implement page and prod settings.
- [ ] **Step 4:** Run `DJANGO_DEBUG=0 uv run manage.py check --deploy` → no warnings; full tests + mypy PASS.
- [ ] **Step 5:** `fly launch --no-deploy`, create volume, set secrets (`DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`), first deploy by hand, run `import_places`, create superuser; then enable the auto-deploy workflow.
- [ ] **Step 6: Commit** `chore: ci and fly deployment`.

---

## Self-Review

- **Coverage:** FR-001/013 → T5; FR-002/003/004 → T3, T5; FR-005 → T6; FR-006 → T7; FR-007 → T8; FR-008 → T9; FR-010 → T10; FR-011 → T2 (admin edit/delete); FR-012 → T4; NFR hours → T11; Guardrail → T12 (partial: measurable form remains PRD open question 6); US-01 empty state → T5. FR-009 intentionally excluded.
- **Types:** `PlaceFilter`, `PlaceResult`, `search_places` defined in T3 and consumed unchanged in T5, T8, T11.
- **Risk:** T3's rating annotation placeholder is replaced in T8 (explicit in both tasks). Seed data licensing (T4) and PRD open questions 1, 2, 3, 5 are assumed per "Decisions Taken".
