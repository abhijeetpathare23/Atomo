import os
import pandas as pd
import matplotlib.pyplot as plt

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def save_tables(output_dir: str, per_item_df: pd.DataFrame, agg_df: pd.DataFrame):
    ensure_dir(output_dir)
    per_item_path = os.path.join(output_dir, "items.csv")
    agg_path = os.path.join(output_dir, "sov_aggregate.csv")
    per_item_df.to_csv(per_item_path, index=False)
    agg_df.to_csv(agg_path, index=False)
    return per_item_path, agg_path

def save_chart(output_dir: str, agg_df: pd.DataFrame, title: str):
    ensure_dir(output_dir)
    fig = plt.figure()
    plt.bar(agg_df["brand"], agg_df["sov_pct"])
    plt.title(title)
    plt.ylabel("Share of Voice (%)")
    plt.xticks(rotation=30, ha="right")
    path = os.path.join(output_dir, "sov_chart.png")
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path

def save_md_summary(output_dir: str, project_name: str, agg_df: pd.DataFrame, top_k=3):
    ensure_dir(output_dir)
    lines = [f"# {project_name}", "", "## Share of Voice Results", ""]
    for _, r in agg_df.iterrows():
        lines.append(f"- *{r['brand']}* — SoV: *{r['sov_pct']:.1f}%* "
                     f"(mentions={int(r['mentions'])}, pos_share={r['pos_share']:.2f})")
    lines.append("")
    lines.append("## Recommendations (auto)")
    # Simple heuristics
    leader = agg_df.iloc[0]
    lines.append(f"- {leader['brand']} leads the SoV. Double-down on keywords that co-occur with this brand in top results.")
    tail = agg_df.iloc[-1]
    lines.append(f"- {tail['brand']} has the lowest SoV. Create content targeting long-tail queries and platforms with high engagement multipliers.")
    path = os.path.join(output_dir, "SUMMARY.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path