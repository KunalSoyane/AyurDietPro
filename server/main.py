import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from database import close_db, init_db
from routes import auth_routes, diet_routes, food_routes, patient_routes, report_routes
from routes import admin_routes
from seed_data import seed_defaults

_initialized = False
_init_lock = asyncio.Lock()


async def ensure_initialized() -> None:
    """Idempotent DB bootstrap.

    Runs via lifespan on uvicorn/docker, and lazily via middleware on
    serverless platforms (e.g. Vercel) that never emit lifespan events.
    """
    global _initialized
    if _initialized:
        return
    async with _init_lock:
        if _initialized:
            return
        await init_db()
        await seed_defaults()
        _initialized = True


@asynccontextmanager
async def lifespan(app: FastAPI):
    await ensure_initialized()
    yield
    await close_db()


app = FastAPI(title="AyurDiet Pro API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=(
        r"https://([a-z0-9-]+\.)*onrender\.com"
        r"|https://([a-z0-9-]+\.)*vercel\.app"
        r"|http://(localhost|127\.0\.0\.1):\d+"
    ),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def ensure_db_ready(request: Request, call_next):
    await ensure_initialized()
    return await call_next(request)


@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/")
def health_check():
    return {"status": "healthy", "message": "AyurDiet Pro API is running"}

app.include_router(auth_routes.router)
app.include_router(patient_routes.router)
app.include_router(food_routes.router)
app.include_router(diet_routes.router)
app.include_router(report_routes.router)
app.include_router(admin_routes.router)

# Serve compiled frontend static assets in production hosting
dist_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../client/dist"))
if os.path.exists(dist_path):
    # Mount assets directory for optimized static file serving
    assets_path = os.path.join(dist_path, "assets")
    if os.path.exists(assets_path):
        app.mount("/assets", StaticFiles(directory=assets_path), name="assets")

    @app.get("/{fallback_path:path}")
    def serve_frontend(fallback_path: str):
        # Allow requests to API routes, health, docs, and openapi schema to fall through
        if (
            fallback_path == "api"
            or fallback_path.startswith("api/")
            or fallback_path == "health"
            or fallback_path.startswith("docs")
            or fallback_path.startswith("redoc")
            or fallback_path.startswith("openapi.json")
        ):
            raise HTTPException(status_code=404, detail="Not Found")

        # Guard against path traversal (e.g. encoded "../") escaping dist/
        file_path = os.path.realpath(os.path.join(dist_path, fallback_path))
        if os.path.commonpath([file_path, dist_path]) != dist_path:
            raise HTTPException(status_code=404, detail="Not Found")

        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)

        index_file = os.path.join(dist_path, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)

        raise HTTPException(
            status_code=404,
            detail="Frontend build files found, but index.html is missing. Run npm run build in client/.",
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


