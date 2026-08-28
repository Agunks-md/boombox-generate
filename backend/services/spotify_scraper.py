import re
import logging
import requests
from bs4 import BeautifulSoup

log = logging.getLogger(__name__)

SPOTIFY_OPEN_URL_RE = re.compile(
    r"https?://open\.spotify\.com/(track|album|playlist)/([A-Za-z0-9]+)"
)

def _spotify_to_yt_query(spotify_url: str) -> str:
    """
    Scrape the Spotify open-graph page to obtain track title + artist,
    then build a YouTube search query string.

    Returns e.g.  "ytsearch1:Shape of You Ed Sheeran"
    """
    log.info("[Spotify] Resolving Spotify URL: %s", spotify_url)

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
    }

    try:
        resp = requests.get(spotify_url, headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        og_title = soup.find("meta", property="og:title")
        og_desc  = soup.find("meta", property="og:description")

        title  = og_title["content"].strip()  if og_title  else ""
        desc   = og_desc["content"].strip()   if og_desc   else ""

        artist = desc.split("·")[0].strip() if "·" in desc else ""

        if title and artist:
            query = f"{title} {artist}"
        elif title:
            query = title
        else:
            raise ValueError("Could not extract title from Spotify page.")

        log.info("[Spotify] Resolved query: '%s'", query)
        return f"ytsearch1:{query}"

    except Exception as exc:
        log.warning("[Spotify] Scraping failed (%s), attempting URL regex fallback.", exc)
        m = SPOTIFY_OPEN_URL_RE.search(spotify_url)
        if m:
            return f"ytsearch1:spotify {m.group(1)} {m.group(2)}"
        raise RuntimeError(f"Tidak dapat me-resolve URL Spotify: {exc}") from exc
