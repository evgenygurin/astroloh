# MVP Roadmap (4–6 weeks)

- Phase 1: Core Audit & Target Definition (Week 1)
  - Architecture map, core vs optional modules, risks
  - Product vision finalized
- Phase 2: MVP API & Webhook (Weeks 1–2)
  - Yandex webhook flows (horoscope, natal, compatibility, lunar)
  - REST endpoints parity, validation, RU localization
- Phase 3: Caching & Observability (Week 2)
  - Redis TTLs, performance alerts, health/metrics
- Phase 4: Frontend basic flows (Weeks 3–4)
  - Web pages: Natal, Horoscope, Lunar, Compatibility
  - API wiring, auth stub
- Phase 5: Docs & Ops (Weeks 4–5)
  - Full docs set, templates, deployment with Docker Compose/ngrok
- Phase 6: Stabilization & Launch (Week 6)
  - MVP checklist, acceptance, smoke tests

Dependencies: Docker Compose-first, webhook-first.