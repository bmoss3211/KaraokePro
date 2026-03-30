"""FastAPI application setup."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os

from app.models.database import init_db
from app.services.song_index import song_index
from config import load_config


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    config = load_config()
    if config["song_folders"]:
        song_index.scan(config["song_folders"], config["song_extensions"])
    yield
    # Shutdown (nothing to clean up)


app = FastAPI(title="KaraokePro", lifespan=lifespan)

app.mount(
    "/static",
    StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")),
    name="static",
)

# Import and register routes
from app.routes.queue_routes import router as queue_router
from app.routes.song_routes import router as song_router
from app.routes.session_routes import router as session_router
from app.routes.page_routes import router as page_router

app.include_router(queue_router, prefix="/api")
app.include_router(song_router, prefix="/api")
app.include_router(session_router, prefix="/api")
app.include_router(page_router)
