"""Central configuration: API keys, model settings, and theme constants."""
import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GEMINI_MODEL_ID = os.getenv("GEMINI_MODEL_ID", "gemini-2.0-flash")

# --- Analysis parameters -----------------------------------------------
PRICE_HISTORY_PERIOD = "6mo"      # matches the "6-month horizon" requirement
PRICE_HISTORY_INTERVAL = "1d"
BENCHMARK_TICKER = "SPY"          # used for relative performance comparisons
NEWS_ITEM_LIMIT = 15              # raw headlines pulled per ticker before tiering
NEWS_TIERS = {
    1: "Last 24 hours",
    2: "Last 3 days",
    3: "Last 7 days",
    4: "Last 30 days",
    5: "Older",
}

# --- UI theme: "Financial" Green/Gray, dark mode -------------------------
THEME = {
    "bg": "#0e1117",
    "panel": "#161b22",
    "border": "#2a2f38",
    "text": "#e6e6e6",
    "muted": "#9aa4b2",
    "accent_green": "#00c896",
    "accent_green_dim": "#0e5c47",
    "accent_red": "#ff5c5c",
    "accent_gray": "#3a4048",
    "font": "'Inter', 'Segoe UI', sans-serif",
}

PLOTLY_TEMPLATE = "plotly_dark"
