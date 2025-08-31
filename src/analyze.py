from __future__ import annotations
import math
import re
from typing import List, Dict, Tuple
import pandas as pd

# ---------------- Sentiment utils (robust) ----------------

def get_vader():
    """
    Try to return a real VADER analyzer. If anything fails, return a no-op
    analyzer that yields compound=0.0 so we never crash.
    """
    try:
        from nltk import data, download
        from nltk.sentiment import vader
        try:
            # Ensure resource exists; download if missing
            data.find("sentiment/vader_lexicon.zip")
        except LookupError:
            download("vader_lexicon", quiet=True)
        return vader.SentimentIntensityAnalyzer()
    except Exception:
        class _NullAnalyzer:
            def polarity_scores(self, _text: str):
                return {"compound": 0.0}
        return _NullAnalyzer()

def score_sentiment(analyzer, text: str) -> float:
    try:
        s = analyzer.polarity_scores(text or "")
        return float(s.get("compound", 0.0))
    except Exception:
        return 0.0

# ---------------- Mention counting ----------------

def re_escape(s: str) -> str:
    return re.escape(s)

def mention_counts(text: str, brands: List[str]) -> Dict[str, int]:
    text_l = (text or "").lower()
    out: Dict[str, int] = {}
    for b in brands:
        patt = r"\b" + re_escape(b.lower()) + r"\b"
        out[b] = len(re.findall(patt, text_l))
    return out

# ---------------- Build per-item dataframe ----------------

def build_df(items, brands_all: List[str]) -> pd.DataFrame:
    an = get_vader()
    rows = []
    for it in items:
        m = mention_counts(f"{it.title} {it.text}", brands_all)
        sent = score_sentiment(an, (it.text or it.title or ""))
        row = {
            "platform": it.platform,
            "url": it.url,
            "title": it.title,
            "author": it.author,
            "ts": it.ts,
            "text_len": len(it.text or ""),
            "sentiment": sent,  # <- ALWAYS present
        }
        # mentions
        for k, v in m.items():
            row[f"m_{k}"] = v
        # metrics
        for k, v in (it.metrics or {}).items():
            row[f"metric_{k}"] = v
        rows.append(row)

    df = pd.DataFrame(rows)
    # Ensure required columns exist even if items list is empty
    if "sentiment" not in df.columns:
        df["sentiment"] = 0.0
    return df

# ---------------- Normalize helper ----------------

def normalize(series: pd.Series) -> pd.Series:
    if series.empty:
        return series
    mx = series.max()
    if mx <= 0:
        return series * 0
    return series / mx

# ---------------- SoV computation ----------------

def compute_sov(
    df: pd.DataFrame,
    brand: str,
    competitors: List[str],
    weights: Dict[str, float]
) -> Tuple[pd.DataFrame, pd.DataFrame]:

    # Defensive guards
    if "sentiment" not in df.columns:
        df["sentiment"] = 0.0

    brands = [brand] + competitors

    # Engagement proxy by platform
    eng = []
    for _, r in df.iterrows():
        if r.get("platform") == "google":
            e = r.get("metric_rank_weight", 0.0)
        elif r.get("platform") == "youtube":
            e = r.get("metric_views", 0.0) + 5*r.get("metric_likes", 0.0) + 3*r.get("metric_comments", 0.0)
        elif r.get("platform") == "x":
            e = r.get("metric_likes", 0.0) + 3*r.get("metric_retweets", 0.0) + 2*r.get("metric_replies", 0.0) + 2*r.get("metric_quotes", 0.0)
        else:
            e = 0.0
        eng.append(e)
    df["engagement"] = eng

    # Ensure mention columns exist even if zero
    for b in brands:
        col = f"m_{b}"
        if col not in df.columns:
            df[col] = 0

    # Per-brand aggregates (with sentiment fallback)
    rows = []
    for b in brands:
        col = f"m_{b}"
        mentions = float(df[col].sum())
        mask = df[col] > 0
        engagement = float(df.loc[mask, "engagement"].sum())
        sent_series = df.loc[mask, "sentiment"] if "sentiment" in df.columns else pd.Series([], dtype=float)
        pos = int((sent_series > 0.05).sum())
        total_m = int(mask.sum())
        pos_share = (pos / total_m) if total_m > 0 else 0.0
        rows.append({"brand": b, "mentions": mentions, "engagement": engagement, "pos_share": pos_share})

    agg = pd.DataFrame(rows)
    agg["norm_mentions"] = normalize(agg["mentions"])
    agg["norm_engagement"] = normalize(agg["engagement"])
    agg["sov_score"] = (
        float(weights.get("w_mentions", 0.5)) * agg["norm_mentions"] +
        float(weights.get("w_engagement", 0.35)) * agg["norm_engagement"] +
        float(weights.get("w_sentiment", 0.15)) * agg["pos_share"]
    )
    total = float(agg["sov_score"].sum())
    agg["sov_pct"] = (100.0 * agg["sov_score"] / total) if total > 0 else 0.0
    return agg.sort_values("sov_pct", ascending=False), df