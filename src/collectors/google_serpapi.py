from __future__ import annotations
import os, time, math, requests
from typing import List
from .base import BaseCollector, Item
from src.utils import clean_text, try_extract_text

SERPAPI_ENDPOINT = "https://serpapi.com/search.json"

class GoogleSerpAPICollector(BaseCollector):
    platform_name = "google"

    def __init__(self, cfg: dict):        
        super().__init__(cfg)
        self.api_key = os.getenv("SERPAPI_API_KEY")
        if not self.api_key:
            raise RuntimeError("SERPAPI_API_KEY missing. Add it to .env")

    def search(self, query: str) -> List[Item]:
        n = self.cfg["platforms"]["google"]["top_n"]
        fetch_page_text = self.cfg["platforms"]["google"].get("fetch_page_text", False)
        sleep = self.cfg.get("throttling", {}).get("per_request_sleep_sec", 0.5)

        params = {
            "engine": "google",
            "q": query,
            "num": min(n, 20),
            "api_key": self.api_key,
            "hl": "en",
            "gl": "in",
        }

        res = requests.get(SERPAPI_ENDPOINT, params=params, timeout=30)
        res.raise_for_status()
        data = res.json()
        organic = data.get("organic_results", [])[:n]

        out: List[Item] = []
        for i, r in enumerate(organic, start=1):
            url = r.get("link")
            title = r.get("title") or ""
            snippet = r.get("snippet") or ""
            text = snippet

            if fetch_page_text and url:
                fulltext = try_extract_text(url)
                if fulltext:
                    text = fulltext

            rank_weight = 1.0 / math.log2(i + 1.5)
            out.append(Item(
                platform=self.platform_name,
                url=url,
                title=clean_text(title),
                text=clean_text(text),
                author=None,
                ts=None,
                metrics={"rank_weight": rank_weight},
                raw=r
            ))
            time.sleep(sleep)
        return out