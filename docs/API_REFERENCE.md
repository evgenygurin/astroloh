# API Reference (Core)

- GET `/` – service info
- GET `/health` – health
- POST `/api/v1/yandex/webhook` – Yandex Dialogs
- Astrology (`/api/astrology`):
  - POST `/natal-chart`
  - GET `/horoscope/{sign}/{type}` (daily|weekly|monthly)
  - POST `/compatibility`
- Lunar (`/api/lunar/*`) – phases and calendar

Auth: token-based (see `app/api/auth.py`).