# Architecture

## Layers

- API: FastAPI entrypoint and routers
- Core: settings and logging
- Services: fault localization, telemetry pipeline, simulator
- Repositories: database persistence wrappers
- Models: SQLAlchemy entities
- WebSocket: live update fan-out
- Frontend: React dashboard with map and monitor panels

## Request flow

1. Telemetry is posted to the API router.
2. The pipeline service validates, normalizes, and stores it.
3. Localization can be triggered for relevant events.
4. WebSocket subscribers receive state snapshots for live display.
