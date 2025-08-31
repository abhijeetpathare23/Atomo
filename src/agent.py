from __future__ import annotations
import yaml, os
from dataclasses import asdict
from typing import List
from src.collectors.base import Item
from src.collectors.google_serpapi import GoogleSerpAPICollector
from src.collectors.youtube_api import YouTubeCollector
from src.analyze import build_df, compute_sov

def load_cfg(path="config.yaml") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def run_pipeline(cfg: dict):
    keywords = cfg["keywords"]
    brand = cfg["brand_of_interest"]
    competitors = cfg["competitors"]
    weights = cfg["weights"]
    platforms_cfg = cfg["platforms"]

    items: List[Item] = []

    if platforms_cfg.get("google", {}).get("enabled"):
        g = GoogleSerpAPICollector(cfg)   
        for q in keywords:
            items.extend(g.search(q))

    if platforms_cfg["youtube"]["enabled"]:
        y = YouTubeCollector(cfg)
        for q in keywords:
            items.extend(y.search(q))


    brands_all = [brand] + competitors
    df = build_df(items, brands_all)
    agg, per_item_df = compute_sov(df, brand, competitors, weights)
    return agg, df