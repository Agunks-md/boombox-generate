import logging
from pathlib import Path
import requests

log = logging.getLogger(__name__)

def upload_to_catbox(mp3_path: Path) -> str:
    """
    Upload *mp3_path* to catbox.moe and return the direct MP3 download link.
    Catbox returns the direct URL as plain text.
    """
    log.info("[Catbox] Uploading %s (%.2f MB)…", mp3_path.name, mp3_path.stat().st_size / 1_048_576)

    try:
        with mp3_path.open("rb") as fh:
            files = {'fileToUpload': (mp3_path.name, fh, 'audio/mpeg')}
            payload = {'reqtype': 'fileupload'}

            resp = requests.post(
                'https://catbox.moe/user/api.php',
                files=files,
                data=payload,
                timeout=120,
            )
            resp.raise_for_status()

        link = resp.text.strip()
        if link.startswith("http"):
            log.info("[Catbox] Direct link found: %s", link)
            return link
            
        raise RuntimeError(
            f"Gagal mendapatkan link valid dari Catbox. "
            f"Respons awal: {link[:200]!r}"
        )

    except requests.RequestException as exc:
        raise RuntimeError(f"Gagal upload ke Catbox: {exc}") from exc
