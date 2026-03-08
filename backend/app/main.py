import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure required directories exist
    os.makedirs("data", exist_ok=True)

    # Initialize database tables
    from app.db.database import init_db
    init_db()

    yield


app = FastAPI(
    title="Skill-Bridge Career Navigator API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers (imported here to avoid circular imports at module level)
from app.api.v1.routes import health, sessions, roadmap  # noqa: E402

app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(sessions.router, prefix="/api/v1", tags=["sessions"])
app.include_router(roadmap.router, prefix="/api/v1", tags=["roadmap"])
