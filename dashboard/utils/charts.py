"""
Reusable Plotly chart helpers for the DBD dashboard.
Enhanced with richer visualizations: area charts, gauges, funnels, heatmaps, etc.
"""

from __future__ import annotations

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# Consistent dark theme matching Streamlit config
PLOTLY_TEMPLATE = "plotly_dark"
COLOR_PALETTE = [
    "#e63946", "#457b9d", "#a8dadc", "#1d3557",
    "#f1faee", "#e9c46a", "#2a9d8f", "#e76f51",
    "#264653", "#f4a261",
]
BG_COLOR = "rgba(0,0,0,0)"  # transparent to inherit Streamlit theme


def _base_layout(fig: go.Figure, title: str, **kwargs) -> go.Figure:
    """Apply consistent layout to all charts."""
    fig.update_layout(
        title=dict(text=title, font=dict(size=16)),
        template=PLOTLY_TEMPLATE,
        plot_bgcolor=BG_COLOR,
        paper_bgcolor=BG_COLOR,
        margin=dict(l=40, r=20, t=50, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        **kwargs,
    )
    return fig


def line_chart(
    df: pd.DataFrame,
    x: str,
    y: str | list[str],
    title: str,
    y_label: str = "",
) -> go.Figure:
    """Create a styled line chart."""
    if isinstance(y, list):
        fig = go.Figure()
        for i, col in enumerate(y):
            fig.add_trace(go.Scatter(
                x=df[x], y=df[col], mode="lines",
                name=col.replace("_", " ").title(),
                line=dict(color=COLOR_PALETTE[i % len(COLOR_PALETTE)], width=2),
            ))
    else:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df[x], y=df[y], mode="lines",
            name=y.replace("_", " ").title(),
            line=dict(color=COLOR_PALETTE[0], width=2),
        ))
    _base_layout(fig, title, yaxis_title=y_label)
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(255,255,255,0.08)")
    return fig


def area_chart(
    df: pd.DataFrame,
    x: str,
    y: str | list[str],
    title: str,
    y_label: str = "",
    stacked: bool = False,
) -> go.Figure:
    """Create a styled area chart with optional stacking."""
    fig = go.Figure()
    cols = y if isinstance(y, list) else [y]
    for i, col in enumerate(cols):
        fig.add_trace(go.Scatter(
            x=df[x], y=df[col], mode="lines",
            name=col.replace("_", " ").title(),
            fill="tonexty" if (stacked and i > 0) else "tozeroy",
            line=dict(color=COLOR_PALETTE[i % len(COLOR_PALETTE)], width=1.5),
            stackgroup="one" if stacked else None,
        ))
    _base_layout(fig, title, yaxis_title=y_label)
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(255,255,255,0.08)")
    return fig


def bar_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    color: str | None = None,
    horizontal: bool = False,
    text_auto: bool = True,
) -> go.Figure:
    """Create a styled bar chart."""
    orientation = "h" if horizontal else "v"
    fig = px.bar(
        df,
        x=x if not horizontal else y,
        y=y if not horizontal else x,
        color=color,
        title=title,
        template=PLOTLY_TEMPLATE,
        color_discrete_sequence=COLOR_PALETTE,
        orientation=orientation,
        text_auto=".2%" if text_auto else False,
    )
    _base_layout(fig, title)
    fig.update_traces(textposition="outside" if not horizontal else "auto")
    return fig


def pie_chart(
    df: pd.DataFrame,
    values: str,
    names: str,
    title: str,
    hole: float = 0.45,
) -> go.Figure:
    """Create a styled donut/pie chart."""
    fig = px.pie(
        df, values=values, names=names, title=title,
        hole=hole, template=PLOTLY_TEMPLATE,
        color_discrete_sequence=COLOR_PALETTE,
    )
    fig.update_traces(
        textinfo="percent+label",
        textposition="outside",
        pull=[0.03] * len(df),
    )
    _base_layout(fig, title)
    return fig


def histogram(df: pd.DataFrame, x: str, title: str, nbins: int = 30) -> go.Figure:
    """Create a styled histogram."""
    fig = px.histogram(
        df, x=x, title=title, nbins=nbins,
        template=PLOTLY_TEMPLATE, color_discrete_sequence=COLOR_PALETTE,
    )
    _base_layout(fig, title)
    return fig


def gauge_chart(
    value: float,
    title: str,
    suffix: str = "%",
    min_val: float = 0,
    max_val: float = 100,
    thresholds: list[dict] | None = None,
) -> go.Figure:
    """Create a gauge indicator chart."""
    if thresholds is None:
        thresholds = [
            {"range": [min_val, max_val * 0.33], "color": "#e63946"},
            {"range": [max_val * 0.33, max_val * 0.66], "color": "#e9c46a"},
            {"range": [max_val * 0.66, max_val], "color": "#2a9d8f"},
        ]
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={"text": title, "font": {"size": 14}},
        number={"suffix": suffix, "font": {"size": 28}},
        gauge={
            "axis": {"range": [min_val, max_val], "tickwidth": 1},
            "bar": {"color": "#457b9d"},
            "steps": thresholds,
            "threshold": {
                "line": {"color": "white", "width": 2},
                "thickness": 0.75,
                "value": value,
            },
        },
    ))
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        paper_bgcolor=BG_COLOR,
        plot_bgcolor=BG_COLOR,
        margin=dict(l=30, r=30, t=50, b=20),
        height=220,
    )
    return fig


def funnel_chart(
    stages: list[str],
    values: list[float],
    title: str,
) -> go.Figure:
    """Create a conversion funnel chart."""
    fig = go.Figure(go.Funnel(
        y=stages,
        x=values,
        textinfo="value+percent initial",
        marker=dict(color=COLOR_PALETTE[:len(stages)]),
        connector={"line": {"color": "rgba(255,255,255,0.2)", "width": 1}},
    ))
    _base_layout(fig, title)
    fig.update_layout(funnelmode="stack")
    return fig


def heatmap_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    z: str,
    title: str,
    color_scale: str = "RdYlGn",
) -> go.Figure:
    """Create a heatmap from a DataFrame."""
    pivot = df.pivot_table(values=z, index=y, columns=x, aggfunc="mean")
    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        colorscale=color_scale,
        text=pivot.values.round(3),
        texttemplate="%{text}",
        textfont={"size": 10},
    ))
    _base_layout(fig, title)
    fig.update_layout(height=400)
    return fig


def waterfall_chart(
    categories: list[str],
    values: list[float],
    title: str,
) -> go.Figure:
    """Create a waterfall chart for revenue breakdown."""
    measures = ["relative"] * len(categories)
    measures.append("total")
    categories.append("Total")
    values.append(sum(values))

    fig = go.Figure(go.Waterfall(
        orientation="v",
        x=categories,
        y=values,
        measure=measures,
        connector={"line": {"color": "rgba(255,255,255,0.2)"}},
        increasing={"marker": {"color": "#2a9d8f"}},
        decreasing={"marker": {"color": "#e63946"}},
        totals={"marker": {"color": "#457b9d"}},
        textposition="outside",
        text=[f"${v:,.0f}" for v in values],
    ))
    _base_layout(fig, title, yaxis_title="USD")
    return fig


def kpi_metric(label: str, value: str | float, delta: str | float | None = None) -> dict:
    """Return a dict for st.metric display."""
    return {"label": label, "value": value, "delta": delta}
