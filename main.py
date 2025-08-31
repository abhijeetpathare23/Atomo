import os
from dotenv import load_dotenv
from src.agent import load_cfg, run_pipeline
from src.report import save_tables, save_chart, save_md_summary

def main():
    load_dotenv()
    cfg = load_cfg("config.yaml")
    agg, df = run_pipeline(cfg)
    outdir = cfg["project"]["output_dir"]
    os.makedirs(outdir, exist_ok=True)
    items_path, agg_path = save_tables(outdir, df, agg)
    chart_path = save_chart(outdir, agg, title=cfg["project"]["name"])
    md_path = save_md_summary(outdir, cfg["project"]["name"], agg)

    print("=== DONE ===")
    print(f"Per-item CSV: {items_path}")
    print(f"SoV aggregate CSV: {agg_path}")
    print(f"Chart: {chart_path}")
    print(f"Summary: {md_path}")

if __name__ == "_main_":
    main()