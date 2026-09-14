"""
Assembles the four-agent swarm into an Agno `Team` and exposes a single
`run_investment_swarm(tickers)` entry point for the Streamlit UI.
"""
from __future__ import annotations

from agno.models.google import Gemini
from agno.team.team import Team

from agents import TEAM_LEAD_INSTRUCTIONS, company_researcher, market_analyst, stock_strategist
from config import GEMINI_MODEL_ID


def build_investment_team() -> Team:
    """Construct the coordinating Team. Rebuilt per-run so agent memory never leaks across runs."""
    return Team(
        name="Investment Swarm",
        mode="coordinate",  # Team Lead plans, delegates to members, then synthesizes
        model=Gemini(id=GEMINI_MODEL_ID),
        members=[market_analyst, company_researcher, stock_strategist],
        instructions=TEAM_LEAD_INSTRUCTIONS,
        markdown=True,
        show_tool_calls=True,
        enable_agentic_context=True,  # members see prior members' findings during coordination
    )


def run_investment_swarm(tickers: list[str]) -> str:
    """
    Run the full swarm on a list of tickers and return the final markdown report as a string.

    Args:
        tickers: e.g. ["AAPL", "MSFT", "NVDA"]

    Returns:
        Final aggregated markdown report produced by the Team Lead.
    """
    if not tickers:
        raise ValueError("At least one ticker is required.")

    clean = [t.strip().upper() for t in tickers if t.strip()]
    ticker_list = ", ".join(clean)

    prompt = (
        f"Produce a full investor report for the following tickers: {ticker_list}.\n\n"
        "Delegate to the Market Analyst for price action and 6-month relative performance, "
        "to the Company Researcher for fundamentals and tiered news, and to the Stock Strategist "
        "for risk-reward framing. Then synthesize everything into the final ranked report format "
        "described in your instructions."
    )

    team = build_investment_team()
    response = team.run(prompt)

    # Agno's RunResponse exposes the final text at `.content`
    content = getattr(response, "content", None)
    return content if content else str(response)
