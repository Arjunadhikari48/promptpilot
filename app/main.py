from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from app.core.config import settings
from app.core.database import Base, engine

# Import models so SQLAlchemy registers tables
from app.models import user as _user_model  # noqa: F401
from app.models import prompt as _prompt_model  # noqa: F401

from app.api.v1 import auth, prompts, llm, versions

# Create tables (use Alembic in production)
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.APP_NAME, version="1.0.0")

STATIC_DIR = Path(__file__).resolve().parent / "static"

app.include_router(auth.router, prefix="/api/v1")
app.include_router(prompts.router, prefix="/api/v1")
app.include_router(llm.router, prefix="/api/v1")
app.include_router(versions.router, prefix="/api/v1")


@app.get("/health")
def health():
    return {"status": "ok", "app": settings.APP_NAME}


# ===== Serve frontend =====
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def serve_index():
    return FileResponse(STATIC_DIR / "index.html")
