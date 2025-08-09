# Security Model

- Secrets: `SECRET_KEY`, `ENCRYPTION_KEY` (auto-generated if absent; set in prod).
- Auth: JWT HS256, token expiry 30m.
- Data: encrypt PII at rest; comply with GDPR deletion/export.
- Webhook: validate Yandex headers/signatures where applicable; rate limiting.
- Transport: HTTPS via reverse proxy.