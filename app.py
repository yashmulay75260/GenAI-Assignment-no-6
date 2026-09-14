"""Investment Swarm — Streamlit front end."""
import streamlit as st

from charts import build_normalized_performance_chart, build_six_month_bar_chart
from config import GOOGLE_API_KEY, THEME
from swarm import run_investment_swarm

st.set_page_config(
    page_title="Investment Swarm | AI Market Intelligence",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom "Financial" Green/Gray dark theme
# ---------------------------------------------------------------------------
st.markdown(
    f"""
    <style>
        .stApp {{
            background-color: {THEME['bg']};
            color: {THEME['text']};
            font-family: {THEME['font']};
        }}
        section[data-testid="stSidebar"] {{
            background-color: {THEME['panel']};
            border-right: 1px solid {THEME['border']};
        }}
        div[data-testid="stMetric"] {{
            background-color: {THEME['panel']};
            border: 1px solid {THEME['border']};
            border-radius: 10px;
            padding: 14px 16px;
        }}
        div[data-testid="stMetricValue"] {{
            color: {THEME['accent_green']};
        }}
        .stButton > button {{
            background-color: {THEME['accent_green']};
            color: #06120e;
            font-weight: 700;
            border: none;
            border-radius: 8px;
            padding: 0.6em 1.4em;
        }}
        .stButton > button:hover {{
            background-color: #00e6ab;
            color: #06120e;
        }}
        .swarm-header {{
            display: flex;
            align-items: baseline;
            gap: 12px;
            border-bottom: 1px solid {THEME['border']};
            padding-bottom: 10px;
            margin-bottom: 18px;
        }}
        .swarm-header h1 {{
            color: {THEME['text']};
            font-size: 1.9rem;
            margin: 0;
        }}
        .swarm-badge {{
            background-color: {THEME['accent_green_dim']};
            color: {THEME['accent_green']};
            border-radius: 6px;
            padding: 3px 10px;
            font-size: 0.75rem;
            font-weight: 600;
            letter-spacing: 0.03em;
        }}
        .agent-pill {{
            display: inline-block;
            background-color: {THEME['panel']};
            border: 1px solid {THEME['border']};
            color: {THEME['muted']};
            border-radius: 20px;
            padding: 4px 12px;
            margin: 3px 4px 3px 0;
            font-size: 0.8rem;
        }}
        .report-box {{
            background-color: {THEME['panel']};
            border: 1px solid {THEME['border']};
            border-radius: 12px;
            padding: 24px 28px;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="swarm-header">
        <h1>📈 Investment Swarm</h1>
        <span class="swarm-badge">AI MULTI-AGENT MARKET INTELLIGENCE</span>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <span class="agent-pill">🧠 Market Analyst</span>
    <span class="agent-pill">🔎 Company Researcher</span>
    <span class="agent-pill">⚖️ Stock Strategist</span>
    <span class="agent-pill">🧾 Team Lead</span>
    """,
    unsafe_allow_html=True,
)
st.write("")

with st.sidebar:
    st.header("Configuration")
    tickers_input = st.text_input(
        "Tickers (comma-separated)",
        value="AAPL, MSFT, NVDA, AMD",
        help="e.g. AAPL, MSFT, NVDA",
    )
    benchmark = st.text_input("Benchmark ticker", value="SPY")
    st.divider()
    run_clicked = st.button("🚀 Run Swarm Analysis", use_container_width=True)
    st.divider()
    st.caption(
        "This tool is for informational purposes only and is not financial advice. "
        "Market data via Yahoo Finance (yfinance); may be delayed or incomplete."
    )
    if not GOOGLE_API_KEY:
        st.warning("GOOGLE_API_KEY is not set. Add it to your .env file before running the swarm.")

tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]

if not tickers:
    st.info("Enter at least one ticker in the sidebar to begin.")
else:
    st.subheader("Visual Comparison")
    col1, col2 = st.columns(2)
    try:
        with col1:
            st.plotly_chart(
                build_normalized_performance_chart(tickers), use_container_width=True
            )
        with col2:
            st.plotly_chart(
                build_six_month_bar_chart(tickers, benchmark=benchmark), use_container_width=True
            )
    except Exception as e:  # noqa: BLE001
        st.error(f"Couldn't build charts: {e}")

if run_clicked:
    if not GOOGLE_API_KEY:
        st.error("Set GOOGLE_API_KEY in your .env file before running the swarm.")
    elif not tickers:
        st.error("Enter at least one valid ticker.")
    else:
        with st.spinner("Swarm is analyzing — delegating to Market Analyst, Company Researcher, and Stock Strategist..."):
            try:
                report_md = run_investment_swarm(tickers)
                st.session_state["last_report"] = report_md
            except Exception as e:  # noqa: BLE001
                st.error(f"Swarm run failed: {e}")

if "last_report" in st.session_state:
    st.subheader("Investor Report")
    st.markdown(st.session_state["last_report"])
    st.download_button(
        "⬇️ Download report (Markdown)",
        data=st.session_state["last_report"],
        file_name="investment_swarm_report.md",
        mime="text/markdown",
    )
