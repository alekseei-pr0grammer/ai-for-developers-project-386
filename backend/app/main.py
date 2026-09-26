from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute

from app.api import health
from app.config import settings

# Bumped automatically by release-please (see release-please-config.json).
VERSION = "0.1.0"  # x-release-please-version


def operation_id(route: APIRoute) -> str:
    # Use the Python function name as the OpenAPI operationId, so the generated
    # TypeScript client gets readable names (get_health -> getHealth).
    return route.name


app = FastAPI(title="Calendar API", version=VERSION, generate_unique_id_function=operation_id)

if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

api = APIRouter(prefix="/api")
api.include_router(health.router)
app.include_router(api)
