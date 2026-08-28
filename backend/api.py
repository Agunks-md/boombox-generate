"""
================================================================
  Discord Bot – Backend API
  Stack  : Python 3.10+ · FastAPI · yt-dlp · requests
               · static-ffmpeg (auto-managed FFmpeg binary)
  Route  : POST /process
================================================================
"""

from __future__ import annotations

import os
import logging
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator

from services.downloader import download_as_mp3, cleanup_downloads
from services.spotify_scraper import _spotify_to_yt_query
from services.uploader import upload_to_catbox

# ─── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# ─── Lifespan (startup / shutdown) ──────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app_: FastAPI):  # noqa: ARG001
    log.info("[Startup] Scanning downloads/ for leftover temp files...")
    cleanup_downloads()
    yield
    # ---- shutdown (nothing to do) ----

# ─── App ───────────────────────────────────────────────────────────────────
app = FastAPI(
    title="BotJS URL Generator – Backend",
    description="Converts audio/video URLs to direct MP3 links via Top4Top.io",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1", "http://localhost"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

# ─── Models ────────────────────────────────────────────────────────────────────
PlatformType = Literal["youtube", "tiktok", "soundcloud", "spotify", "search"]

class ProcessRequest(BaseModel):
    type: PlatformType
    url: str

    @field_validator("url")
    @classmethod
    def url_must_not_be_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("URL tidak boleh kosong.")
        return v

class ProcessResponse(BaseModel):
    status: Literal["success", "error"]
    direct_link: str | None = None
    title: str | None = None
    message: str | None = None

# ─── Core Processor ────────────────────────────────────────────────────────────
def process_request(platform: str, url: str) -> tuple[str, str]:
    """
    Full pipeline: resolve → download → upload → cleanup.
    Returns (direct_link, title).
    """
    source_url = url

    # Step 1 – Spotify: resolve to YouTube search
    if platform == "spotify":
        source_url = _spotify_to_yt_query(url)

    # Step 2 – Download via yt-dlp
    mp3_path, title = download_as_mp3(source_url, platform)

    try:
        # Step 3 – Upload to Catbox
        direct_link = upload_to_catbox(mp3_path)
    finally:
        # Step 4 – Always clean up local file
        try:
            if mp3_path.exists():
                os.remove(mp3_path)
                log.info("[Cleanup] Deleted local file: %s", mp3_path.name)
        except OSError as e:
            log.warning("[Cleanup] Could not delete %s: %s", mp3_path.name, e)

    return direct_link, title

# ─── Route ─────────────────────────────────────────────────────────────────────
@app.post("/process", response_model=ProcessResponse)
async def process_endpoint(req: ProcessRequest):
    """
    Main endpoint consumed by the Node.js Discord bot.
    """
    log.info("[POST /process] type=%s url=%s", req.type, req.url)

    try:
        direct_link, title = process_request(req.type, req.url)
        return ProcessResponse(status="success", direct_link=direct_link, title=title)

    except RuntimeError as exc:
        log.error("[/process] RuntimeError: %s", exc)
        return ProcessResponse(status="error", message=str(exc))

    except Exception as exc:
        log.exception("[/process] Unexpected error")
        return ProcessResponse(status="error", message=f"Internal server error: {exc}")

# ─── Health Check ──────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok", "service": "BotJS URL Generator Backend"}

# ─── Entrypoint ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=False, log_level="info")
