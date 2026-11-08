---
bootstrapped_at: 2026-10-21T22:31:58Z
starter_id: django
starter_name: Django
project_name: gdzienasniadanie-pl
language_family: python
package_manager: uv
cwd_strategy: native-cwd
bootstrapper_confidence: verified
phase_3_status: ok
audit_command: pip-audit
---

## Hand-off

```yaml
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
```

A solo, Python-fluent developer who is new to web work is building a map-based breakfast finder with login, ratings, saved lists and an admin who edits places, on about 5-6 after-hours hours a week toward a 6 December deadline. Django is the recommended default for a Python web app and bootstrapper has run it end to end, so scaffolding should be smooth. Its built-in login, admin screen and database layer cover FR-006, FR-011 and FR-012 without extra assembly, which suits the short first slice. Django does not enforce explicit types by default, so the project's instruction file should require type hints and a type checker. Deployment defaults to Fly with GitHub Actions and auto-deploy on merge, the starter's standard shape.

## Pre-scaffold verification

| Signal      | Value         | Severity | Notes                                                        |
| ----------- | ------------- | -------- | ------------------------------------------------------------ |
| npm package | not run       | n/a      | Python starter; no npm package applies                       |
| GitHub repo | not run       | n/a      | card docs_url (docs.djangoproject.com) is not a GitHub URL; no recency signal available |

## Scaffold log

**Resolved invocation**: `uv init --bare --name gdzienasniadanie-pl && uv add django && uv run django-admin startproject config .`
**Strategy**: native-cwd
**Deviations from the card template** (`django-admin startproject {name} .`): the template with `{name}=.` is not a valid Django invocation, and `gdzienasniadanie-pl` is not a valid Python package name. The settings package was named `config`, and the project environment was created with uv (`uv init --bare`, `uv add django`) instead of `pip install django`. `uv` was installed with Homebrew (uv 0.13.4) at the user's approval.
**Exit code**: 0
**Pre-flight files-to-touch**: pyproject.toml, uv.lock, .venv/, manage.py, config/ (none existed beforehand)
**Files written by CLI**: pyproject.toml, uv.lock, .venv/, manage.py, config/{__init__,asgi,settings,urls,wsgi}.py
**Pre-existing files preserved**: .10x-cli.json, .agents/, .claude/, CLAUDE.md, context/, lessons/, skills-lock.json
**Installed**: Django 6.1.2 (asgiref 3.12.1, sqlparse 0.6.0); `requires-python = ">=3.14"` in pyproject.toml

## Post-scaffold audit

**Tool**: pip-audit (run on request via `uvx pip-audit -r <uv export --no-hashes --no-emit-project output>`)
**Summary**: 0 CRITICAL, 0 HIGH, 0 MODERATE, 0 LOW
**Direct vs transitive**: not distinguished by this tool
**Audited**: asgiref 3.12.1, django 6.1.2, sqlparse 0.6.0 (tzdata 2026.5 is Windows-only and was not installed here)
**Result**: No known vulnerabilities found. Clean tree.

The first pass at the end of the scaffold step did not run the audit because `pip-audit` was not installed. The user then approved running it through `uvx`, and this section replaces that note.

## Hints recorded but not acted on

| Hint                    | Value               |
| ----------------------- | ------------------- |
| bootstrapper_confidence | verified            |
| quality_override        | false               |
| path_taken              | standard            |
| self_check_answers      | null                |
| team_size               | solo                |
| deployment_target       | fly                 |
| ci_provider             | github-actions      |
| ci_default_flow         | auto-deploy-on-merge |
| has_auth                | true                |
| has_payments            | false               |
| has_realtime            | false               |
| has_ai                  | false               |
| has_background_jobs     | false               |

## Next steps

Next: a future skill will set up agent context (CLAUDE.md, AGENTS.md). For now, your project is scaffolded and verified — happy hacking.

Useful manual steps in the meantime:
- `git init` (if you have not already) to start your own repo history, and add a `.gitignore` covering `.venv/` and `db.sqlite3` (the scaffold did not create one).
- Review any `.scaffold` siblings the conflict policy created and decide which version of each file to keep (none were created).
- Re-run the dependency audit when dependencies change, for example `uv export --no-hashes --no-emit-project -o requirements.txt && uvx pip-audit -r requirements.txt`.
- Django does not enforce explicit types by default: add type hints and a type checker, and put that rule in your project instruction file.
