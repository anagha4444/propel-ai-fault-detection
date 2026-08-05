from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers.simulator import router as simulator_router
from app.api.routers.telemetry import router as telemetry_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.websocket.manager import websocket_endpoint

configure_logging()
settings = get_settings()

app = FastAPI(
    title=settings.app_name.title(),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(telemetry_router, prefix=settings.api_prefix)
app.include_router(simulator_router, prefix=settings.api_prefix)
app.add_websocket_route("/ws", websocket_endpoint)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
