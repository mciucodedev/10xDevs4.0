# Repository Guidelines

## Project: gdzienasniadanie.pl

Map-based breakfast finder for Kraków (login, ratings, saved lists, admin-edited places). Solo, after-hours project with a hard deadline of 2026-12-06. Scope and requirements: `@context/foundation/prd.md`; stack decision, rationale and deployment plan: `@context/foundation/tech-stack.md`; scaffold log: `@context/changes/bootstrap-verification/verification.md`.

## Tripwires

- Settings are env-driven (`DJANGO_SECRET_KEY` required unless `DJANGO_DEBUG=1`; see `.env.example`, a local `.env` is auto-loaded). Never commit `.env` or `db.sqlite3`.
- All new functions carry parameter and return type hints. `uv run mypy .` (strict, django-stubs, configured in `@pyproject.toml`) must report zero errors before finishing.
- Never write to `context/archive/`. `context/` is the 10xDevs workflow state (`foundation/`, `changes/`, `archive/`).
- `.claude/skills/` and `.agents/skills/` are CLI-managed (see `.claude/.10x-cli-manifest.json`); `lessons/` is course material, not product code.
- Apps are top-level siblings of `config/` (the project package); register each in `INSTALLED_APPS`.

## Commands

Versions and dependencies: `@pyproject.toml`. Package manager is `uv`.

```bash
uv sync                          # install deps into .venv
uv run manage.py runserver       # dev server
uv run manage.py migrate         # apply migrations
uv run manage.py startapp <name> # new app
uv run manage.py test            # all tests
uv run manage.py test <app>.tests.<TestCase>.<test_name>   # single test
uv run mypy .                    # type check
```

No linter or CI is configured yet.

## Architecture

- `places`: `Place`/`FoodType`/`OpeningInterval` models, `services.py` (pure open-now, distance and filter logic behind the map API `/api/places/`), seed import `import_places` (`places/data/seed.json`, from OpenStreetMap, ODbL).
- `engagement`: `Rating` (1-5, one per user per place) and `SavedPlace`; `accounts`: registration and login by username or email.
- Opening hours older than 90 days (or unverified) are excluded from the open-now/open-on filters.
- Deployed on Fly.io (`fly.toml`, `Dockerfile`; SQLite on a volume at `/data`, migrations run at container start). The map uses OSM tiles: keep the Referer (`SECURE_REFERRER_POLICY`) and the linked attribution.
