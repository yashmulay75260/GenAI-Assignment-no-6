"""
Yahoo Finance data-access layer.

These functions are passed directly to Agno agents as `tools=[...]`. Agno inspects each
function's signature, type hints, and docstring to build the tool schema the LLM sees —
so keep signatures simple (str/int/float args) and docstrings descriptive.

Every function returns a JSON-serializable dict and never raises: on failure it returns
an {"error": ...} payload so a single bad ticker can't crash an agent run.
"""
from __future__ import annotations

import datetime as dt
from typing import Any

import pandas as pd
import yfinance as yf

from config import (
    BENCHMARK_TICKER,
    NEWS_ITEM_LIMIT,
    NEWS_TIERS,
    PRICE_HISTORY_INTERVAL,
    PRICE_HISTORY_PERIOD,
)


def _safe_ticker(symbol: str) -> yf.Ticker:
    return yf.Ticker(symbol.strip().upper())


def get_price_history(symbol: str, period: str = PRICE_HISTORY_PERIOD) -> dict[str, Any]:
    """Fetch OHLCV price history for a ticker over the given period (default 6 months).

    Args:
        symbol: Stock ticker, e.g. "AAPL".
        period: yfinance period string, e.g. "6mo", "1y", "1mo".

    Returns:
        dict with dates, close prices, and volume, or an error message.
    """
    try:
        t = _safe_ticker(symbol)
        hist = t.history(period=period, interval=PRICE_HISTORY_INTERVAL, auto_adjust=True)
        if hist.empty:
            return {"error": f"No price history found for {symbol}"}
        return {
            "symbol": symbol.upper(),
            "dates": [d.strftime("%Y-%m-%d") for d in hist.index],
            "close": [round(float(v), 4) for v in hist["Close"].tolist()],
            "volume": [int(v) for v in hist["Volume"].tolist()],
        }
    except Exception as e:  # noqa: BLE001
        return {"error": f"Failed to fetch price history for {symbol}: {e}"}


def get_six_month_change(symbol: str) -> dict[str, Any]:
    """Compute the 6-month percentage price change for a ticker, plus start/end prices.

    Args:
        symbol: Stock ticker, e.g. "AAPL".

    Returns:
        dict with pct_change_6mo, start_price, end_price, or an error message.
    """
    try:
        t = _safe_ticker(symbol)
        hist = t.history(period="6mo", auto_adjust=True)
        if hist.empty or len(hist) < 2:
            return {"error": f"Not enough price history for {symbol}"}
        start_price = float(hist["Close"].iloc[0])
        end_price = float(hist["Close"].iloc[-1])
        pct_change = ((end_price - start_price) / start_price) * 100
        return {
            "symbol": symbol.upper(),
            "start_price": round(start_price, 2),
            "end_price": round(end_price, 2),
            "pct_change_6mo": round(pct_change, 2),
        }
    except Exception as e:  # noqa: BLE001
        return {"error": f"Failed to compute 6mo change for {symbol}: {e}"}


def get_relative_performance(symbols: list[str], benchmark: str = BENCHMARK_TICKER) -> dict[str, Any]:
    """Rank a list of tickers by 6-month performance relative to a benchmark (default SPY).

    Args:
        symbols: List of ticker strings to compare.
        benchmark: Benchmark ticker to compare against, default "SPY".

    Returns:
        dict with benchmark_pct_change and a ranked list of {symbol, pct_change_6mo,
        relative_to_benchmark} sorted best-to-worst.
    """
    try:
        bench = get_six_month_change(benchmark)
        bench_pct = bench.get("pct_change_6mo")
        rows = []
        for s in symbols:
            r = get_six_month_change(s)
            if "error" in r:
                rows.append({"symbol": s.upper(), "error": r["error"]})
                continue
            rel = None
            if bench_pct is not None:
                rel = round(r["pct_change_6mo"] - bench_pct, 2)
            rows.append(
                {
                    "symbol": r["symbol"],
                    "pct_change_6mo": r["pct_change_6mo"],
                    "relative_to_benchmark": rel,
                }
            )
        rows_sorted = sorted(
            rows, key=lambda x: x.get("pct_change_6mo", float("-inf")), reverse=True
        )
        return {
            "benchmark": benchmark.upper(),
            "benchmark_pct_change_6mo": bench_pct,
            "ranking": rows_sorted,
        }
    except Exception as e:  # noqa: BLE001
        return {"error": f"Failed to compute relative performance: {e}"}


def get_company_fundamentals(symbol: str) -> dict[str, Any]:
    """Fetch key fundamentals and a business summary for a ticker.

    Args:
        symbol: Stock ticker, e.g. "AAPL".

    Returns:
        dict with sector, industry, market_cap, pe_ratio, forward_pe, dividend_yield,
        profit_margins, beta, business_summary, or an error message.
    """
    try:
        t = _safe_ticker(symbol)
        info = t.info or {}
        if not info or info.get("regularMarketPrice") is None and info.get("currentPrice") is None:
            # still proceed — some valid tickers legitimately lack these fields
            pass
        return {
            "symbol": symbol.upper(),
            "long_name": info.get("longName") or info.get("shortName"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "dividend_yield": info.get("dividendYield"),
            "profit_margins": info.get("profitMargins"),
            "beta": info.get("beta"),
            "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
            "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
            "business_summary": info.get("longBusinessSummary"),
        }
    except Exception as e:  # noqa: BLE001
        return {"error": f"Failed to fetch fundamentals for {symbol}: {e}"}


def get_tiered_news(symbol: str) -> dict[str, Any]:
    """Fetch recent news for a ticker and bucket it into 5 recency tiers.

    Tiers: 1) last 24h, 2) last 3 days, 3) last 7 days, 4) last 30 days, 5) older.

    Args:
        symbol: Stock ticker, e.g. "AAPL".

    Returns:
        dict mapping tier number -> list of {title, publisher, link, published} items.
    """
    try:
        t = _safe_ticker(symbol)
        raw_news = t.news or []
        now = dt.datetime.now(dt.timezone.utc)
        tiers: dict[int, list[dict[str, Any]]] = {i: [] for i in range(1, 6)}

        for item in raw_news[:NEWS_ITEM_LIMIT]:
            content = item.get("content", item)  # yfinance news schema has shifted over versions
            title = content.get("title") or item.get("title")
            publisher = (
                (content.get("provider") or {}).get("displayName")
                if isinstance(content.get("provider"), dict)
                else item.get("publisher")
            )
            link = (
                (content.get("canonicalUrl") or {}).get("url")
                if isinstance(content.get("canonicalUrl"), dict)
                else item.get("link")
            )
            pub_date_raw = content.get("pubDate") or item.get("providerPublishTime")

            published_dt = None
            if isinstance(pub_date_raw, (int, float)):
                published_dt = dt.datetime.fromtimestamp(pub_date_raw, tz=dt.timezone.utc)
            elif isinstance(pub_date_raw, str):
                try:
                    published_dt = dt.datetime.fromisoformat(pub_date_raw.replace("Z", "+00:00"))
                except ValueError:
                    published_dt = None

            if published_dt is None:
                tier = 5
                age_str = "unknown"
            else:
                age = now - published_dt
                age_str = published_dt.strftime("%Y-%m-%d %H:%M UTC")
                if age <= dt.timedelta(hours=24):
                    tier = 1
                elif age <= dt.timedelta(days=3):
                    tier = 2
                elif age <= dt.timedelta(days=7):
                    tier = 3
                elif age <= dt.timedelta(days=30):
                    tier = 4
                else:
                    tier = 5

            if title:
                tiers[tier].append(
                    {"title": title, "publisher": publisher, "link": link, "published": age_str}
                )

        return {
            "symbol": symbol.upper(),
            "tier_labels": NEWS_TIERS,
            "tiers": tiers,
        }
    except Exception as e:  # noqa: BLE001
        return {"error": f"Failed to fetch news for {symbol}: {e}"}


def build_price_dataframe(symbols: list[str], period: str = PRICE_HISTORY_PERIOD) -> pd.DataFrame:
    """Non-agent helper (used directly by the charting layer, not exposed as an LLM tool).

    Returns a DataFrame indexed by date with one normalized-to-100 column per symbol,
    so relative performance is directly comparable on one chart.
    """
    frames = {}
    for s in symbols:
        data = get_price_history(s, period=period)
        if "error" in data:
            continue
        series = pd.Series(data["close"], index=pd.to_datetime(data["dates"]), name=s.upper())
        frames[s.upper()] = (series / series.iloc[0]) * 100
    if not frames:
        return pd.DataFrame()
    df = pd.DataFrame(frames)
    return df
