# Deployment Guide

- Use Docker Compose. See `docs/DOCKER_DEPLOYMENT.md` for detailed commands.
- Expose webhook via ngrok for Yandex Dialogs testing. See `docs/NGROK_SETUP.md`.
- Set production env: `DEBUG=false`, strong `SECRET_KEY`, DB creds, Redis URL.