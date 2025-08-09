# Product Vision

- Core idea: Multi-platform astrological assistant with primary Yandex Alice webhook integration providing accurate horoscopes, natal charts, compatibility, and lunar guidance.
- Target users: Russian-speaking audience using Yandex Alice and web app; later Telegram/Google Assistant.
- Unique value: Professional-grade astrology (Kerykeion), fast API, localized RU content, webhook-first reliability, Docker-first deploy.

## Problem
People want simple, trusted, and fast astrological guidance across voice and web.

## Solution
Unified FastAPI backend powering Yandex Alice webhook and web frontend with caching and RU-localized outputs.

## MVP Scope
- Yandex Dialogs webhook: daily/weekly horoscopes, natal chart, basic compatibility, lunar phase.
- REST endpoints for the same features.
- Redis cache, minimal monitoring.

## Non-MVP (Later)
- Advanced ML recommendations, IoT integrations, complex progressions UX.

## Success Metrics
- P95 API: <2s for Kerykeion ops; cache hit 60%.
- First-time user completes a query <30s.
- 3+ daily returning users within 2 weeks.