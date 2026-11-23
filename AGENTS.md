# AGENTS.md

This repository is a Python + Streamlit lead-generation and B2B prospecting app. Keep changes small, targeted, and consistent with the existing Spanish SaaS UX and multi-business workflow.

## Project map

- App entry: [app.py](app.py)
- Core logic package: [leadhunter/](leadhunter/)
- Frontend mockup: [frontend/](frontend/)
- Data and local DB: [data/](data/)
- Database migrations: [alembic/](alembic/)
- Docs and setup: [README.md](README.md)
- Secret/data ignore rules: [.gitignore](.gitignore)

## Run and test commands

Use the project-local virtual environment in `.venv`:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python -m streamlit run app.py
```

Useful checks:

```powershell
python test_smoke.py
python test_saas_security.py
python test_api.py
```

For Windows scheduling:

```powershell
run_scheduled.bat
```

## Architecture and conventions

- The UI and user flow are centered in [app.py](app.py), including auth, onboarding, workspace navigation, and export actions.
- The business logic lives under [leadhunter/](leadhunter/): database access, source discovery, AI interpretation, scoring, and message generation.
- The app is multi-tenant/multi-company: businesses are isolated by name and should stay separate in the database and lead queries.
- The project uses Spanish labels and marketing copy throughout the UI; keep new text consistent with the current product tone unless a task explicitly says otherwise.
- The package is intentionally data-sensitive: do not commit lead data, CSV exports, `.env` files, or local DB files. See [.gitignore](.gitignore).

## Important repository rules

- Do not add secrets or API keys to source-controlled files.
- Do not commit local data in [data/](data/); the repo is meant to keep those files out of git.
- Prefer small, surgical edits over large rewrites.
- If you change behavior in the UI, validate the related Python flow with the nearest smoke/test script.
- When a fix is visual-only, keep the current dark brand system and improve contrast rather than changing the overall design language.

## Good starting points for agents

- [README.md](README.md): setup, usage, and testing expectations
- [app.py](app.py): main interface and state flow
- [leadhunter/db.py](leadhunter/db.py): persistence and lead queries
- [leadhunter/pipeline.py](leadhunter/pipeline.py): search + analysis pipeline
- [leadhunter/scoring.py](leadhunter/scoring.py): lead scoring logic
- [leadhunter/messages.py](leadhunter/messages.py): outreach message templates

## Notes for AI coding agents

- Prefer matching existing patterns and naming styles instead of introducing new abstractions.
- Keep product output in Spanish unless a task explicitly requires another language.
- If a fix touches the Streamlit UI, check both syntax and runtime behavior using the local virtual environment rather than assuming the query is safe.
- For repo-specific pitfalls, assume there is no external API key setup required for the default local flow; the app should still run in a local dev environment with public sources and sample data.
