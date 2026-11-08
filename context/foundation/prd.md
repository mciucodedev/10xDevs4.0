---
project: "gdzienasniadanie.pl"
version: 1
status: draft
created: 2026-10-22
context_type: greenfield
product_type: web-app
target_scale:
  users: large
  # TODO: target_scale.qps — see Open Questions
  # TODO: target_scale.data_volume — see Open Questions
timeline_budget:
  mvp_weeks: 3
  hard_deadline: 2026-12-06
  after_hours_only: true
---

## Vision & Problem Statement

Choosing where to have breakfast out in Kraków means combining Google Maps, Instagram and foodie blogs. Generic map filters cannot express what matters (sweet breakfast, vegan/vegetarian, open hours that fit the plan), information is sometimes outdated or unreliable, and there is no way to compare places or keep a shortlist. The result is time spent across scattered sources and decision paralysis.

Insight: local curation. Kraków is the MVP city, with the option to extend to other cities later (possibly tourists in Poland, not yet defined).

## User & Persona

Primary: a Kraków local, the author and their friends, who regularly choose a place for breakfast out. They currently use Google Maps, Instagram and foodie blogs.

### Secondary persona

Visitors to Kraków. Possible future audience: tourists in Poland (unspecified).

## Success Criteria

First flow as described: open the site on a Sunday morning, see a map of Kraków with pinned places and filters at the side, filter, choose the best place, and mark it as "today I'm going to visit this place". (Pricing was listed among the filters in this flow and was later deferred; see Non-Goals.)

### Primary
- "I'm able to pick the best possible place for me to eat breakfast on my terms."
- # TODO: measurable target for the Primary outcome — see Open Questions

### Secondary
- Pricing and menu comparison.

### Guardrails
- Privacy, legal and security measures are applied to be safe and clear.
- # TODO: measurable form of the Guardrail — see Open Questions

## User Stories

### US-01: Visitor picks a breakfast place on a Sunday morning

- **Given** a visitor on the map of Kraków with seeded places
- **When** they set filters (open now, food type, minimum rating) in the side panel
- **Then** the map shows only matching places, and they can open one to see its details and decide

#### Acceptance Criteria
- Filters combine; the map updates to the matching set
- A filter combination with no matches shows an explanatory empty state
- # TODO: further acceptance criteria and additional user stories — see Open Questions

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

## Non-Functional Requirements

- The product remains usable on the latest two major versions of mainstream mobile and desktop browsers.
- Opening hours shown for any place are no older than 90 days.
- Privacy, legal and security measures are applied to be safe and clear (Guardrail; measurable specifics pending, see Open Questions).

## Business Logic

The app shows only the places that meet the visitor's chosen criteria, ordered by closeness to a chosen point.

Inputs are the criteria the visitor sets (open now or opening hours, food type, minimum aggregate rating), each place's aggregate rating (many users' ratings combined into one score, with the number of ratings visible), and a reference point the visitor chooses (their location or a pin on the map). The output is the set of qualifying places, shown on the map and ordered by distance from the reference point.

Location is the key driver: a good commute and the freedom to choose visually. Door-to-door transit time (tram, etc.) is outside the MVP.

## Access Control

Registered login for users (sign-in method not yet decided; sign-up/sign-in details deferred).

- Anonymous visitor: can browse the map and use filters; cannot rate, save or submit.
- Registered user: can rate places and keep a saved list. Submitting new places is limited to logged-in users who meet a ratings threshold (threshold not yet defined; submissions publish directly).
- Admin: can edit and remove published places, including user-submitted ones.

An unauthenticated visitor who attempts a gated action (rating, saving, submitting) is prompted to log in.

## Non-Goals

Functional:
- Transit-aware travel time (tram etc.): the MVP orders by distance from a reference point only.
- Pricing filter and menu comparison: deferred beyond the MVP.
- Instagram discovery or scraping of new places: new places arrive only through logged-in user submissions (an optional Instagram link on a submission stays).
- Cities other than Kraków: city stays in the data model, only Kraków is offered.
- Marking a place as "I'm going here today" (FR-009): nice-to-have, after the MVP.
- An approval queue for submitted places: submissions publish directly.

Non-functional:
- Native mobile app: web only, phone use through the browser.
- Offline use.
- Full accessibility conformance (e.g. WCAG AA) beyond baseline.
- Multi-language interface.

## Open Questions

1. **What is the ratings threshold that unlocks submitting a place (e.g. a minimum number of places the user has rated)?** — Owner: user. Block: no. (FR-010)
2. **How are opening hours kept current for seeded and submitted places?** — Owner: user. (FR-002; NFR sets a 90-day maximum age)
3. **Which breakfast categories are in the MVP beyond sweet / vegan / vegetarian, and who tags a place?** — Owner: user. (FR-003)
4. **What exactly does the place details view show vs. linking out to Google Maps?** — Owner: user. (FR-005)
5. **What is the rating scale, and how are early ratings handled at cold start?** — Owner: user. (FR-007)
6. **How should the privacy/legal/security guardrail be made measurable** (e.g. data-protection obligations for accounts, terms of use of the place-data sources, security of login)? — Owner: user. Missing measurable form of the Guardrail and NFR.
7. **Is distance ordering (FR-013) by straight-line distance acceptable in the MVP, given that choosing visually on the map is also a priority?** — Owner: user. Resolve when scoping the first milestone.
8. **Publishing submissions directly: is reactive abuse handling acceptable?** — Mitigation named by the user: logged-in users with a ratings threshold. Owner: user. (FR-010, FR-011)
9. **What are the target `qps` and `data_volume` ballparks?** — Not asked during shaping; maximum users stated as about 5,000. Owner: user.
10. **What is a measurable target for the Primary success criterion?** — The user's wording has no numeric target. Owner: user.
11. **Which further acceptance criteria and user stories are needed?** — Only US-01 was written, from the described flow. Owner: user.
12. **What sign-in method will be used?** — Deferred in shaping. Owner: user, resolved at stack selection.
13. **Quality cross-check carry-over:** all required elements were present; the user accepted finishing with questions 1, 2, 3, 5 and 6 above still open.
