from __future__ import annotations
import os, time
from typing import List
from googleapiclient.discovery import build
from .base import BaseCollector, Item
from src.utils import clean_text

class YouTubeCollector(BaseCollector):
    platform_name = "youtube"

    def _init_(self, cfg: dict):
        super()._init_(cfg)
        api_key = os.getenv("YOUTUBE_API_KEY")
        if not api_key:
            raise RuntimeError("YOUTUBE_API_KEY missing. Add it to .env")
        self.yt = build("youtube", "v3", developerKey=api_key)

    def search(self, query: str) -> List[Item]:
        n = self.cfg["platforms"]["youtube"]["top_n"]
        sleep = self.cfg.get("throttling", {}).get("per_request_sleep_sec", 0.5)

        sr = self.yt.search().list(
            q=query, part="snippet", type="video", maxResults=min(n, 50)
        ).execute()

        video_ids = [x["id"]["videoId"] for x in sr.get("items", [])][:n]
        if not video_ids:
            return []

        stats = self.yt.videos().list(
            id=",".join(video_ids), part="statistics,snippet"
        ).execute().get("items", [])

        out: List[Item] = []
        for v in stats:
            vid = v["id"]
            s = v.get("statistics", {})
            snip = v.get("snippet", {})
            title = snip.get("title", "")
            desc = snip.get("description", "")
            author = snip.get("channelTitle")
            ts = snip.get("publishedAt")

            views = float(s.get("viewCount", 0))
            likes = float(s.get("likeCount", 0)) if "likeCount" in s else 0.0
            comments = float(s.get("commentCount", 0))

            out.append(Item(
                platform=self.platform_name,
                url=f"https://www.youtube.com/watch?v={vid}",
                title=clean_text(title),
                text=clean_text(desc),
                author=author,
                ts=ts,
                metrics={"views": views, "likes": likes, "comments": comments},
                raw=v
            ))
            time.sleep(sleep)
        return out