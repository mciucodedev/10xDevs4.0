---
starter_id: django
package_manager: uv
project_name: gdzienasniadanie-pl
hints:
  language_family: python
  team_size: solo
  deployment_target: fly
  ci_provider: github-actions
  ci_default_flow: auto-deploy-on-merge
  bootstrapper_confidence: verified
  path_taken: standard
  quality_override: false
  self_check_answers: null
  has_auth: true
  has_payments: false
  has_realtime: false
  has_ai: false
  has_background_jobs: false
---

## Why this stack

A solo, Python-fluent developer who is new to web work is building a map-based breakfast finder with login, ratings, saved lists and an admin who edits places, on about 5-6 after-hours hours a week toward a 6 December deadline. Django is the recommended default for a Python web app and bootstrapper has run it end to end, so scaffolding should be smooth. Its built-in login, admin screen and database layer cover FR-006, FR-011 and FR-012 without extra assembly, which suits the short first slice. Django does not enforce explicit types by default, so the project's instruction file should require type hints and a type checker. Deployment defaults to Fly with GitHub Actions and auto-deploy on merge, the starter's standard shape.
