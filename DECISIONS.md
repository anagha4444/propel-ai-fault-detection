# Decisions

- Chose FastAPI for the backend API and OpenAPI-first development.
- Used SQLAlchemy models for relational persistence and topology-related queries.
- Kept the simulator REST-driven to make fault injection deterministic for tests and demo runs.
- Used React + Leaflet for a lightweight interactive dashboard with no heavy UI framework.
- Added a simple WebSocket fan-out to support live telemetry and ticket updates.
