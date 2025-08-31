import re, time, requests
from typing import Optional
from bs4 import BeautifulSoup

def clean_text(s: str) -> str:
    s = s or ""
    s = re.sub(r"\s+", " ", s).strip()
    return s

def safe_get(d: dict, *keys, default=None):
    cur = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur

def try_extract_text(url: str) -> Optional[str]:
    """Polite page text extraction via trafilatura when allowed."""
    try:
        import trafilatura
        downloaded = trafilatura.fetch_url(url, no_ssl=True, timeout=20)
        if downloaded:
            text = trafilatura.extract(downloaded, include_comments=False)
            return clean_text(text or "")
    except Exception:
        pass
    # fallback tiny snippet
    try:
        r = requests.get(url, timeout=15, headers={"User-Agent":"Mozilla/5.0"})
        if r.ok:
            soup = BeautifulSoup(r.text, "html.parser")
            return clean_text(soup.get_text(" ", strip=True)[:5000])
    except Exception:
        return None
    return None