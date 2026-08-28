import uuid
import time
import logging
from pathlib import Path

import yt_dlp
import imageio_ffmpeg

log = logging.getLogger(__name__)

log.info("[FFmpeg] Getting FFmpeg binary path via imageio_ffmpeg...")
FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()
log.info("[FFmpeg] Binary path: %s", FFMPEG_PATH)

# DOWNLOAD_DIR is in backend/downloads
DOWNLOAD_DIR = Path(__file__).parent.parent / "downloads"
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

_TEMP_EXTS = {".mp3", ".webm", ".m4a", ".opus", ".ogg", ".part", ".tmp", ".ytdl"}

def cleanup_downloads() -> None:
    removed, skipped = 0, 0
    for item in DOWNLOAD_DIR.iterdir():
        if item.is_file() and item.suffix.lower() in _TEMP_EXTS:
            try:
                item.unlink()
                removed += 1
                log.debug("[Cleanup] Removed stale file: %s", item.name)
            except OSError as exc:
                log.warning("[Cleanup] Could not remove %s: %s", item.name, exc)
                skipped += 1
    if removed or skipped:
        log.info("[Startup Cleanup] Removed %d stale file(s), skipped %d.", removed, skipped)
    else:
        log.info("[Startup Cleanup] downloads/ is clean.")

def _build_ydl_opts(output_path: str) -> dict:
    _cookies = str(Path(__file__).parent.parent / "cookies.txt")
    _has_cookies = Path(_cookies).exists()

    opts: dict = {
        "format": "bestaudio/best/ba/b",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "ffmpeg_location": FFMPEG_PATH,
        "outtmpl": output_path,
        "socket_timeout": 30,
        "retries": 3,
        "fragment_retries": 3,
        "quiet": False,
        "no_warnings": False,
        "noplaylist": True,
        "geo_bypass": True,
        "age_limit": None,
        "extractor_args": {
            "youtube": {"skip": ["dash", "hls"]},
        },
    }

    if _has_cookies:
        opts["cookiefile"] = _cookies
        log.info("[yt-dlp] Using cookies.txt: %s", _cookies)
    else:
        log.debug("[yt-dlp] cookies.txt not found at %s – proceeding without cookies.", _cookies)

    return opts

def download_as_mp3(source_url: str, platform: str) -> tuple[Path, str]:
    unique_id  = uuid.uuid4().hex[:12]
    out_template = str(DOWNLOAD_DIR / unique_id)
    
    if platform == "search" and not source_url.startswith("ytsearch"):
        source_url = f"ytsearch1:{source_url}"

    log.info("[yt-dlp] Downloading | platform=%s | url=%s", platform, source_url)
    start = time.perf_counter()

    opts = _build_ydl_opts(out_template)

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(source_url, download=True)
            title = info.get("title") if info else None
            if info and "entries" in info and info["entries"]:
                title = info["entries"][0].get("title", title)
            if not title:
                title = "Unknown Title"
    except yt_dlp.utils.DownloadError as exc:
        raise RuntimeError(f"yt-dlp gagal mengunduh: {exc}") from exc

    elapsed = time.perf_counter() - start

    mp3_path = Path(out_template + ".mp3")
    if not mp3_path.exists():
        candidates = list(DOWNLOAD_DIR.glob(f"{unique_id}*.mp3"))
        if not candidates:
            raise RuntimeError("File .mp3 tidak ditemukan setelah download selesai.")
        mp3_path = candidates[0]

    log.info("[yt-dlp] Done in %.1fs → %s (%.2f MB)", elapsed, mp3_path.name, mp3_path.stat().st_size / 1_048_576)
    return mp3_path, title
