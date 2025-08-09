# Developer Setup

Preferred: Docker Compose

- Copy `.env.example` → `.env` and set DB/Redis vars.
- Dev: `docker-compose -f docker-compose.dev.yml up`
- Prod-like: `docker-compose up -d`

Local (optional):
- Python 3.12, `pip install -e ".[minimal,dev]"`
- Run: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`

Testing: `pytest`
Lint/Types: `black`, `isort`, `flake8`, `mypy`.