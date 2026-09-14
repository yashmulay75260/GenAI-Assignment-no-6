"""Company Researcher — fundamentals, business summaries, tiered news."""
from agno.agent import Agent
from agno.models.google import Gemini

from config import GEMINI_MODEL_ID
from tools import get_company_fundamentals, get_tiered_news

company_researcher = Agent(
    name="Company Researcher",
    role="Digs into company fundamentals, business model, and recent news for each ticker.",
    model=Gemini(id=GEMINI_MODEL_ID),
    tools=[get_company_fundamentals, get_tiered_news],
    instructions=[
        "For every ticker, call get_company_fundamentals and summarize: sector, industry, "
        "market cap, P/E and forward P/E, margins, beta, and a 1-2 sentence plain-English "
        "description of what the business actually does (from the business summary).",
        "Call get_tiered_news for every ticker and organize findings by recency tier "
        "(tier 1 = last 24h ... tier 5 = older). Lead with the most recent, material items.",
        "Flag anything that looks like it could move the stock: earnings, guidance changes, "
        "litigation, executive departures, M&A, regulatory action.",
        "If fundamentals or news are missing/unavailable for a ticker, say so plainly instead of guessing.",
        "Do not make price predictions or buy/sell calls — stick to facts and context.",
    ],
    markdown=True,
)
