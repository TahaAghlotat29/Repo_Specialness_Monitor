"""
Repo Tension Monitor — €STR, DFR, and money market regime classification.
"""


import plotly.graph_objects as go
import streamlit as st
from src.analytics.tension_signals import load_tension_signals


def render():
    st.title("Repo Tension Monitor")
    st.markdown(
        "**Money market tension signals derived from €STR vs ECB Deposit Facility Rate.**"
    )
    st.markdown("---")


    # Data
    # ---------------------------------------------------------------------
    df = load_tension_signals()
    latest = df.iloc[-1]


    # KPIs
    # ---------------------------------------------------------------------

    last_year = df.tail(252)
    stress_days = last_year[
        last_year["regime"].isin(["Collateral scarcity", "Funding stress"])
    ].shape[0]

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="Current €STR − DFR spread",
            value=f"{latest['estr_dfr_spread_bp']:.1f} bp",
        )
    with col2:
        st.metric(
            label="Current regime",
            value=latest["regime"],
        )
    with col3:
        st.metric(
            label="Stress days (last 1Y)",
            value=f"{stress_days} / 252",
            help="Days classified as 'Collateral scarcity' or 'Funding stress' in the last 252 trading days",
        )

    st.markdown("---")


    # Chart 1 — €STR vs DFR
    # ---------------------------------------------------------------------
    st.subheader("€STR / ECB Deposit Facility Rate")

    fig1 = go.Figure()
    fig1.add_scatter(
        x=df["date"],
        y=df["dfr"],
        name="DFR",
        mode="lines",
        line=dict(color="#1A1A1A", width=2, dash="dash"),
    )
    fig1.add_scatter(
        x=df["date"],
        y=df["estr"],
        name="€STR",
        mode="lines",
        line=dict(color="#0F6644", width=2),
    )
    fig1.update_layout(
        hovermode="x unified",
        yaxis_title="Rate (%)",
        xaxis_title="",
        legend=dict(orientation="h", y=-0.15),
        margin=dict(t=20, b=20),
        height=400,
    )
    st.plotly_chart(fig1, use_container_width=True)


    # Spread by regime
    # ---------------------------------------------------------------------
    st.subheader("€STR − DFR spread by market regime")

    regime_colors = {
        "Collateral scarcity": "#B22222",       
        "Mild tension": "#D97706",              
        "Normal": "#0F6644",                    
        "Mild funding stress": "#6B7280",       
        "Funding stress": "#1A1A1A",            
        "Insufficient history": "#D1D5DB",      
    }

    fig2 = go.Figure()

    fig2.add_scatter(
        x=df["date"],
        y=df["estr_dfr_spread_bp"],
        mode="lines",
        line=dict(color="rgba(26, 26, 26, 0.2)", width=1),
        name="Spread",
        showlegend=False,
    )

    for regime, color in regime_colors.items():
        subset = df[df["regime"] == regime]
        if len(subset) > 0:
            fig2.add_scatter(
                x=subset["date"],
                y=subset["estr_dfr_spread_bp"],
                mode="markers",
                name=regime,
                marker=dict(color=color, size=4),
            )

    fig2.add_hline(y=0, line_dash="dot", line_color="#1A1A1A", opacity=0.4)

    fig2.update_layout(
        yaxis_title="Spread (bp)",
        xaxis_title="",
        legend=dict(orientation="h", y=-0.2),
        margin=dict(t=20, b=20),
        height=450,
        hovermode="closest",
    )
    st.plotly_chart(fig2, use_container_width=True)


    # Table — Tail events
    # ---------------------------------------------------------------------
    st.subheader("Tail events")
    st.caption( "Lowest €STR − DFR spread observations relative to the trailing 1Y distribution.")

    top_stress = df.nsmallest(10, "spread_zscore_1y")[
        ["date", "estr", "dfr", "estr_dfr_spread_bp", "spread_zscore_1y", "regime"]
    ].copy()
    top_stress["date"] = top_stress["date"].dt.strftime("%Y-%m-%d")
    top_stress = top_stress.rename(
        columns={
            "date": "Date",
            "estr": "€STR (%)",
            "dfr": "DFR (%)",
            "estr_dfr_spread_bp": "Spread (bp)",
            "spread_zscore_1y": "Z-score (1Y)",
            "regime": "Regime",
        }
    )
    st.dataframe(top_stress, use_container_width=True, hide_index=True)


    # Footer
    # ---------------------------------------------------------------------
    st.markdown("---")
    st.caption(
        f"Data source: ECB Data Portal €STR / DFR · "
        f"Latest observation: {df['date'].max().date()}"
    )