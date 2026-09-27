from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute

from app.api import auth, event_types, health, hosts, me, schedule
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
        # The Host's session is a cookie, which cross-origin requests only carry with this.
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

api = APIRouter(prefix="/api")
api.include_router(health.router)
api.include_router(auth.router)
api.include_router(me.router)
api.include_router(event_types.router)
api.include_router(schedule.router)
api.include_router(hosts.router)
app.include_router(api)
