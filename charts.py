"""High-end Plotly Graph Objects charts, dark themed to match the Streamlit UI."""
from __future__ import annotations

import plotly.graph_objects as go

from config import PLOTLY_TEMPLATE, THEME
from tools import build_price_dataframe, get_relative_performance

_LINE_PALETTE = [
    THEME["accent_green"],
    "#4da6ff",
    "#ffb84d",
    "#ff6ec7",
    "#c084fc",
    "#5eead4",
    "#f87171",
    "#a3e635",
]


def _base_layout(title: str) -> dict:
    return dict(
        template=PLOTLY_TEMPLATE,
        title=dict(text=title, font=dict(size=18, color=THEME["text"], family=THEME["font"])),
        paper_bgcolor=THEME["bg"],
        plot_bgcolor=THEME["bg"],
        font=dict(color=THEME["text"], family=THEME["font"]),
        legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", y=-0.2),
        margin=dict(l=40, r=20, t=60, b=40),
        hovermode="x unified",
    )


def build_normalized_performance_chart(tickers: list[str], period: str = "6mo") -> go.Figure:
    """Line chart: all tickers normalized to 100 at the start of the period, for direct comparison."""
    df = build_price_dataframe(tickers, period=period)
    fig = go.Figure()

    if df.empty:
        fig.update_layout(**_base_layout("No price data available"))
        return fig

    for i, col in enumerate(df.columns):
        color = _LINE_PALETTE[i % len(_LINE_PALETTE)]
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df[col],
                mode="lines",
                name=col,
                line=dict(color=color, width=2.2),
                hovertemplate=f"<b>{col}</b><br>%{{x|%Y-%m-%d}}<br>Index: %{{y:.1f}}<extra></extra>",
            )
        )

    fig.add_hline(y=100, line_dash="dot", line_color=THEME["muted"], opacity=0.5)
    fig.update_layout(**_base_layout(f"Relative Performance — Normalized to 100 ({period})"))
    fig.update_yaxes(title="Indexed Price (start = 100)", gridcolor=THEME["border"], zeroline=False)
    fig.update_xaxes(gridcolor=THEME["border"])
    return fig


def build_six_month_bar_chart(tickers: list[str], benchmark: str = "SPY") -> go.Figure:
    """Horizontal bar chart ranking tickers by 6-month % change vs. benchmark."""
    result = get_relative_performance(tickers, benchmark=benchmark)
    fig = go.Figure()

    ranking = result.get("ranking", [])
    valid = [r for r in ranking if "pct_change_6mo" in r]

    if not valid:
        fig.update_layout(**_base_layout("No performance data available"))
        return fig

    valid_sorted = sorted(valid, key=lambda r: r["pct_change_6mo"])
    symbols = [r["symbol"] for r in valid_sorted]
    changes = [r["pct_change_6mo"] for r in valid_sorted]
    colors = [THEME["accent_green"] if c >= 0 else THEME["accent_red"] for c in changes]

    fig.add_trace(
        go.Bar(
            x=changes,
            y=symbols,
            orientation="h",
            marker=dict(color=colors, line=dict(color=THEME["border"], width=1)),
            text=[f"{c:+.1f}%" for c in changes],
            textposition="outside",
            hovertemplate="<b>%{y}</b><br>6mo change: %{x:.2f}%<extra></extra>",
        )
    )

    bench_pct = result.get("benchmark_pct_change_6mo")
    if bench_pct is not None:
        fig.add_vline(
            x=bench_pct,
            line_dash="dash",
            line_color=THEME["muted"],
            annotation_text=f"{benchmark} {bench_pct:+.1f}%",
            annotation_font_color=THEME["muted"],
        )

    fig.update_layout(**_base_layout("6-Month % Change vs. Benchmark"))
    fig.update_xaxes(title="% Change", gridcolor=THEME["border"], zeroline=True, zerolinecolor=THEME["border"])
    fig.update_yaxes(gridcolor=THEME["border"])
    return fig
