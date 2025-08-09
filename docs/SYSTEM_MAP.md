# System Map

- Yandex Alice → Webhook (`/api/v1/yandex/webhook`) → Dialog Handler → Services (horoscope, natal, lunar, compatibility) → Redis/PostgreSQL.
- Web Frontend → REST (`/api/astrology/*`, `/api/lunar/*`).
- Observability: health endpoint `/health`, logs, performance monitors.

Environments: dev (Docker Compose), prod (Docker Compose or orchestrator).