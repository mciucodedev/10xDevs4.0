---
project: "gdzienasniadanie.pl"
context_type: greenfield
created: 2026-10-19
updated: 2026-10-20
checkpoint:
  current_phase: 8
  phases_completed: [1, 2, 3, 4, 5, 6, 7]
  gray_areas_resolved:
    - topic: "pain category"
      decision: "scattered sources; filters can't express what matters; unreliable/outdated info; decision paralysis"
    - topic: "insight"
      decision: "local curation"
    - topic: "primary persona scope"
      decision: "Kraków local (user and friends); visitors secondary"
    - topic: "access model"
      decision: "registered login for users; anonymous browsing; admin role edits and removes places (approval queue dropped in Phase 4)"
    - topic: "MVP size"
      decision: "user judged the first flow shippable in about 3 weeks of after-hours work; no scope-down"
    - topic: "rank meaning"
      decision: "aggregate score across users (star-like, not necessarily 1-5 as in Google Maps)"
    - topic: "pricing"
      decision: "pricing filter and pricing/menu comparison are out of the MVP"
    - topic: "Instagram discovery"
      decision: "out of the MVP; an optional Instagram link on a submitted place stays in"
    - topic: "submission approval"
      decision: "submissions are published directly; admin removes or edits bad entries (overrides the earlier approval-queue adjustment)"
    - topic: "place seeding"
      decision: "initial 30-50 places loaded by import script; no create-place admin UI in MVP"
  frs_drafted: 13
  quality_check_status: accepted
---

# Shape notes

## Seed idea (verbatim)

Breakfast finder for Kraków: a map of breakfast places with filters (open hours, sweet breakfast, vegan/vegetarian), user ranking of places and a saved list. Accepted adjustments: seed with a curated set of 30–50 places from Google Places/OSM, plus a user submission form with admin approval; city stored in the data model for later expansion. Unresolved: what "rank" means (personal vs. aggregate vs. scored), how breakfast attributes are tagged, and whether Instagram discovery is in or out of the MVP.

## Vision & Problem Statement

Choosing where to have breakfast out in Kraków means combining Google Maps, Instagram and foodie blogs. Generic map filters cannot express what matters (sweet breakfast, vegan/vegetarian, open hours that fit the plan), information is sometimes outdated or unreliable, and there is no way to compare places or keep a shortlist. The result is time spent across scattered sources and decision paralysis.

Insight (user's words): local curation. Kraków is the MVP city, with the option to extend to other cities later (possibly tourists in Poland, not yet defined).

## User & Persona

Primary: a Kraków local, the author and their friends, who regularly choose a place for breakfast out. Secondary (short): visitors to Kraków. Possible future audience: tourists in Poland (unspecified).

Sources used today: Google Maps, Instagram, foodie blogs.

## Access Control

Registered login for users (sign-in method not yet decided; sign-up/sign-in details deferred).

- Anonymous visitor: can browse the map and use filters; cannot rank, save or submit.
- Registered user: can rate places and keep a saved list. Submitting new places is limited to logged-in users who meet a ratings threshold (threshold not yet defined; submissions publish directly).
- Admin: can edit and remove published places, including user-submitted ones (revised in Phase 4: submissions are published directly, no approval queue).

Unauthenticated access to gated actions (ranking, saving, submitting) prompts login.

## Success Criteria

First flow (user's words): open the site on a Sunday morning, see a map of Kraków with pinned places and filters at the side (open hours / open now, type of food, pricing, ratings), filter, choose the best one, and mark it as "today I'm going to visit this place".

### Primary
- "I'm able to pick the best possible place for me to eat breakfast on my terms." (User's words; no numeric target given.)

### Secondary
- Pricing and menu comparison.

### Guardrails
- Privacy, legal and security measures are applied to be safe and clear. (User's words; specifics not yet defined, see Open Questions.)

## Timeline budget

mvp_weeks: 3 (user confirmed the first flow fits about 3 weeks of after-hours work; no timeline acknowledgment needed).

## Open Questions (running)

- What is the ratings threshold that unlocks submitting a place (e.g. a minimum number of places the user has rated)? Owner: user. (FR-010)

- How are opening hours kept current for seeded and submitted places? (FR-002)
- Which breakfast categories are in the MVP beyond sweet / vegan / vegetarian, and who tags a place? (FR-003)
- What exactly does the place details view show vs. linking out to Google Maps? (FR-005)
- Rating scale and early-rating strategy for the cold start. (FR-007)
- How should the privacy/legal/security guardrail be made measurable (e.g. data-protection obligations for accounts, terms of use of the place-data sources)?
- Distance ordering (FR-013) uses straight-line distance in the MVP; confirm that is acceptable vs. the map-only visual choice.
- Publishing submissions directly: abuse handling is reactive; the logged-in plus ratings-threshold gate is the user's mitigation. (FR-010, FR-011)

- (Resolved in Phase 4) Pricing is out of the MVP, including the filter; it returns later with menu comparison.
- Guardrails are stated generally. Which specifics apply (data protection for user accounts and lists, terms of use of place-data sources, security of login)? Owner: user.

## Functional Requirements

### Discovery
- FR-001: Visitor can view a map of Kraków with breakfast places pinned. Priority: must-have
  > Socrates: Counter-argument: none; stands as written.
- FR-002: Visitor can filter places by open now or by chosen opening hours. Priority: must-have
  > Socrates: Counter-argument considered: "opening hours data goes stale", which hurts trust in a core filter. Resolution: kept; how hours stay current is an open question.
- FR-003: Visitor can filter places by food type (sweet breakfast, vegan, vegetarian). Priority: must-have
  > Socrates: Counter-argument considered: "too narrow a set of categories" (gluten-free, brunch, coffee quality may matter too). Resolution: kept; the category set is an open question.
- FR-004: Visitor can filter places by minimum aggregate rating, and each place shows its rating count next to the score. Priority: must-have
  > Socrates: Counter-argument considered: "few ratings make the average misleading". Resolution: kept; rating count shown next to the score so users see how many votes stand behind it.
- FR-005: Visitor can open a place's details (address, opening hours, food types, aggregate rating, optional Instagram link). Priority: must-have
  > Socrates: Counter-argument considered: "duplicates what Google Maps already shows". Resolution: kept; scope of the details view is an open question (user did not resolve).

### Accounts and personal use
- FR-006: Visitor can register and log in. Priority: must-have
  > Socrates: Counter-argument considered: "accounts add security and privacy duties". Resolution: kept; ties to the Guardrails open question.
- FR-007: User can rate a place, and the place shows the aggregate rating across all users. Priority: must-have
  > Socrates: Counter-argument considered: "cold start, nobody rates early on". Resolution: kept; seeding strategy for early ratings is an open question.
- FR-008: User can save a place to a personal saved list and remove it. Priority: must-have
  > Socrates: Counter-argument considered: "overlaps with the rating". Resolution: kept; saved = want to go, rating = been there.
- FR-009: User can mark a place as "I'm going here today". Priority: nice-to-have
  > Socrates: Counter-argument considered: "nobody comes back to confirm". Resolution: stays nice-to-have.

### Contribution and administration
- FR-010: User who meets the ratings threshold can submit a new place (name, location, food types, optional Instagram link); it is published immediately. Priority: must-have
  > Socrates: Counter-argument: none; stands as written (publish-immediately applied through FR-011 resolution).
- FR-011: Admin can edit or remove any published place, including user-submitted ones. Priority: must-have
  > Socrates: Counter-argument considered: "approval step may be unnecessary at friend scale". Resolution: approval queue dropped; submissions publish directly and admin removes bad entries.
- FR-012: Admin can load the initial 30-50 places through an import, with no create-place admin screen. Priority: must-have
  > Socrates: Counter-argument considered: "seed could be loaded by script, with no admin UI". Resolution: accepted; seed by script, and editing happens on the place through FR-011.

### Location
- FR-013: Visitor can choose a reference point (their location or a pin on the map), and matching places are ordered by distance from it. Priority: must-have
  > Socrates: Counter-argument considered: "visual choice on the map already covers it" (user said choosing visually is among the most important parts). Resolution: not stated by the user; kept as written, to revisit when scoping the first milestone.

## User Stories

### US-01: Visitor picks a breakfast place on a Sunday morning

- **Given** a visitor on the map of Kraków with seeded places
- **When** they set filters (open now, food type, minimum rating) in the side panel
- **Then** the map shows only matching places, and they can open one to see its details and decide

#### Acceptance Criteria
- Filters combine; the map updates to the matching set
- A filter combination with no matches shows an explanatory empty state
- (Further criteria to be added; draft written from the user's described flow)

## Business Logic

The app shows only the places that meet the visitor's chosen criteria, ordered by closeness to a chosen point.

Inputs are the criteria the visitor sets (open now or opening hours, food type, minimum aggregate rating), each place's aggregate rating (many users' ratings combined into one score, with the number of ratings visible), and a reference point the visitor chooses (their location or a pin on the map). The output is the set of qualifying places, shown on the map and ordered by distance from the reference point.

Location is the key driver (user's words): a good commute and the freedom to choose visually. Door-to-door transit time (tram, etc.) is outside the MVP and recorded under Forward.

## Non-Functional Requirements

- The product remains usable on the latest two major versions of mainstream mobile and desktop browsers.
- Opening hours shown for any place are no older than 90 days.
- Privacy, legal and security measures are applied to be safe and clear (Guardrail; measurable specifics pending, see Open Questions).

## Forward: technical-roadmap

- Later: transit-aware travel time (tram etc.) from the reference point to each place (outside the MVP).
- Later: Instagram-based discovery of new places (outside the MVP; an optional Instagram link on a submitted place stays in).
- Later: pricing filter and menu comparison; additional cities (city kept in the data model).
- Seed source: Google Places / OpenStreetMap for the initial 30-50 places (user-stated; stack choice deferred).

## Product framing

- Product type: web app (website opened on phone or laptop).
- Target scale: users up to a maximum of about 5,000 (large); qps and data volume not asked.
- Scale probe (user): submissions limited to logged-in users with a ratings threshold; maximum about 5,000 users.
- Timeline: mvp_weeks 3; hard_deadline 2026-12-06 (user: realistic first deadline); after_hours_only: true (5-6 hours per week).

## Non-Goals

Functional:
- Transit-aware travel time (tram etc.): the MVP orders by distance from a reference point only.
- Pricing filter and menu comparison: deferred beyond the MVP.
- Instagram discovery or scraping of new places: new places arrive only through logged-in user submissions (an optional Instagram link on a submission stays).
- Cities other than Kraków: city stays in the data model, only Kraków is offered.

Non-functional:
- Native mobile app: web only, phone use through the browser.
- Offline use.
- Full accessibility conformance (e.g. WCAG AA) beyond baseline.
- Multi-language interface.

## Quality cross-check

All six greenfield elements present (Access Control, Business Logic, Project artifacts, Timeline-cost acknowledgment, Non-Goals; preserved behavior n/a). User chose "accept and finish" with these items left open (see Open Questions): ratings threshold for submitting a place, opening-hours freshness ownership, breakfast category set and tagging, a measurable privacy/legal/security guardrail, rating scale and cold-start strategy.
