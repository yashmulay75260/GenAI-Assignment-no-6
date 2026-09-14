"""Stock Strategist — risk/reward framing and actionable thesis bullets."""
from agno.agent import Agent
from agno.models.google import Gemini

from config import GEMINI_MODEL_ID
from tools import get_company_fundamentals, get_relative_performance, get_six_month_change

stock_strategist = Agent(
    name="Stock Strategist",
    role="Synthesizes price and fundamental context into a risk-reward assessment per ticker.",
    model=Gemini(id=GEMINI_MODEL_ID),
    tools=[get_six_month_change, get_relative_performance, get_company_fundamentals],
    instructions=[
        "You take the Market Analyst's price data and the Company Researcher's fundamentals "
        "(when available in the shared context) and turn them into a risk/reward read per ticker.",
        "For each ticker, produce: (1) a one-line thesis, (2) 2-3 supporting bullets, "
        "(3) 2-3 key risks, (4) a qualitative risk-reward label: 'Favorable', 'Balanced', or 'Unfavorable'.",
        "Weigh valuation (P/E vs sector norms), momentum vs benchmark, beta/volatility, and "
        "sector/industry tailwinds or headwinds.",
        "Be explicit that this is an analytical framing, not a personalized recommendation, and that "
        "past 6-month performance does not guarantee future results.",
        "Never claim certainty about future price moves. Use hedged, evidence-based language.",
    ],
    markdown=True,
)
