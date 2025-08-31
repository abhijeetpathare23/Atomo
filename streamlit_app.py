import os, time
from datetime import datetime

import streamlit as st
from PIL import Image
import plotly.express as px
import pandas as pd

from dotenv import load_dotenv
from src.agent import load_cfg, run_pipeline
from src.report import save_tables, save_chart, save_md_summary

# ---------- Page & Brand ----------
LOGO_PATH = "assets/atomo_logo.jpg"
PAGE_TITLE = "Atomo — Share of Voice & Insights"

def _set_page_config():
    try:
        icon = Image.open(LOGO_PATH)
        st.set_page_config(page_title=PAGE_TITLE, page_icon=icon, layout="wide")
    except Exception:
        st.set_page_config(page_title=PAGE_TITLE, layout="wide")

_set_page_config()

# CSS for polish
st.markdown("""
<style>
.hero {text-align:center; margin-top: -20px;}
.small-muted {color:#6b7280; font-size:0.95rem}
.kpi {padding:14px 16px; background:#ffffff; border:1px solid #eee; border-radius:14px; box-shadow:0 1px 6px rgba(0,0,0,.04);}
</style>
""", unsafe_allow_html=True)

# ---------- Sidebar ----------
with st.sidebar:
    try:
        st.image(LOGO_PATH, use_container_width=True)
    except Exception:
        st.write("*Atomo*")
    st.markdown("### Controls")
    cfg_path = st.text_input("Config file", "config.yaml")
    auto_run = st.toggle("Auto-run on load", value=True)
    run_btn = st.button("Run SoV Analysis")
    refresh_btn = st.button("🔄 Force Refresh")

# ---------- Hero ----------
st.markdown("<div class='hero'>", unsafe_allow_html=True)
try:
    st.image(LOGO_PATH, width=140)
except Exception:
    pass
st.markdown("<h1>Atomo</h1>", unsafe_allow_html=True)
st.markdown("<p class='small-muted'>Decoding voices, powering Atomberg</p>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)
st.divider()

# ---------- Cache helpers ----------
@st.cache_data(show_spinner=False)
def run_cached_pipeline(cfg_path: str, cache_buster: float):
    cfg = load_cfg(cfg_path)
    agg, df = run_pipeline(cfg)
    return agg, df, cfg

def get_cfg_mtime(cfg_path):
    try:
        return os.path.getmtime(cfg_path)
    except Exception:
        return time.time()

# Force refresh wipes cache + reruns
if refresh_btn:
    st.cache_data.clear()
    st.rerun()

# ---------- Run pipeline ----------
should_run = run_btn or (auto_run and "has_run_once" not in st.session_state)
if should_run:
    st.session_state["has_run_once"] = True
    with st.spinner("Collecting data and analyzing…"):
        try:
            load_dotenv()
            mtime = get_cfg_mtime(cfg_path)  # bust cache if config changes
            agg, df, cfg = run_cached_pipeline(cfg_path, cache_buster=mtime)
        except Exception as e:
            st.error("Runtime error during pipeline execution.")
            st.exception(e)
            st.stop()

    # Save outputs
    outdir = cfg["project"]["output_dir"]
    os.makedirs(outdir, exist_ok=True)
    try:
        items_path, agg_path = save_tables(outdir, df, agg)
        chart_path = save_chart(outdir, agg, title=cfg["project"]["name"])
        md_path = save_md_summary(outdir, cfg["project"]["name"], agg)
    except Exception as e:
        st.warning("Completed analysis, but failed saving some outputs.")
        st.exception(e)

    # ---------- Dashboard ----------
    brand = cfg["brand_of_interest"]

    # KPI cards
    col1, col2, col3 = st.columns(3)
    row = agg[agg["brand"] == brand].head(1)
    if not row.empty:
        r = row.iloc[0]
        comp = agg[agg["brand"] != brand].sort_values("sov_pct", ascending=False).head(1)
        comp_name = comp.iloc[0]["brand"] if not comp.empty else "—"
        comp_sov = comp.iloc[0]["sov_pct"] if not comp.empty else 0.0
        col1.metric("Atomberg SoV", f"{r['sov_pct']:.1f}%", f"vs {comp_name} {comp_sov:.1f}%")
        col2.metric("Pos. Sentiment", f"{(r['pos_share']*100):.0f}%")
        col3.metric("Mentions", int(r["mentions"]))
    else:
        col1.metric("Atomberg SoV", "—")
        col2.metric("Pos. Sentiment", "—")
        col3.metric("Mentions", "—")

    # Bar chart
    fig = px.bar(
        agg,
        x="brand", y="sov_pct",
        text=agg["sov_pct"].map(lambda v: f"{v:.1f}%"),
        title="Share of Voice (%)"
    )
    fig.update_traces(textposition="outside")
    st.plotly_chart(fig, use_container_width=True)

    # Tabs
    tab1, tab2, tab3 = st.tabs(["🔍 Insights", "💡 Recommendations", "🗂 Data"])
    with tab1:
        st.write("Insights coming from analysis…")
        st.dataframe(agg, use_container_width=True)
    with tab2:
        st.markdown("""
        ### Priority Actions
        - 🎥 Comparison videos vs top competitor  
        - 🧮 Energy Savings Calculator landing page  
        - 🗣 Alexa/IoT quick-start shorts  
        - 🤫 Quiet Mode explainer content  
        """)
        if os.path.exists(md_path):
            with open(md_path, "rb") as f:
                st.download_button("📥 Download Summary", f, file_name="ATOMO_SUMMARY.md")
    with tab3:
        st.dataframe(df.head(200), use_container_width=True)
        colA, colB = st.columns(2)
        if os.path.exists(items_path):
            with open(items_path, "rb") as f:
                colA.download_button("Download items.csv", f, file_name="items.csv")
        if os.path.exists(agg_path):
            with open(agg_path, "rb") as f:
                colB.download_button("Download sov_aggregate.csv", f, file_name="sov_aggregate.csv")
else:
    st.info("Press *Run SoV Analysis* (or enable Auto-run).")