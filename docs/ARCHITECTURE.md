# Architecture Overview

- Backend: FastAPI (`app/main.py`) exposing unified API + Yandex Dialogs webhook.
- Services: astrology, natal chart, dialog handling, caching, personalization.
- Data: PostgreSQL (async), Redis cache.
- Integrations: Yandex Dialogs webhook (`/api/v1/yandex/webhook`), Telegram/Google (later).
- Frontend: React + TS.

Key Modules:
- `app/services/dialog_handler.py`: orchestration for intents and responses.
- `app/api/astrology.py`: REST endpoints for natal/horoscope/compatibility.
- `app/core/config.py`: settings and env.

Non-Goals for MVP: IoT, complex ML analytics.

Diagrams: see `docs/SYSTEM_MAP.md`.