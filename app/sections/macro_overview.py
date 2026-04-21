"""
Macro Overview — Eurosystem holdings trajectory and QT run-off.
"""


import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from src.ingestion.ecb_holdings import load_holdings





def render():
    st.title("Macro Overview")
    st.markdown(
        "**Eurosystem sovereign bond holdings and Quantitative Tightening trajectory.**"
    )
    st.markdown("---")

    # Data
    # ---------------------------------------------------------------------
    holdings = load_holdings()
    COUNTRIES = ["Germany", "France", "Italy", "Spain"]
    df = holdings[holdings["country"].isin(COUNTRIES)].copy()


    # KPI
    # ---------------------------------------------------------------------
    latest_date = df["date"].max()

    total_latest = df[df["date"] == latest_date]["holdings_eur_bn"].sum()
    total_by_date = df.groupby("date")["holdings_eur_bn"].sum()

    peak_total = total_by_date.max()
    peak_date = total_by_date.idxmax()

    runoff = peak_total - total_latest
    runoff_pct = runoff / peak_total * 100

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            label="Current holdings (DE/FR/IT/ES)",
            value=f"{total_latest:,.0f} bn €",
        )
    with col2:
        st.metric(
            label=f"Peak holdings ({peak_date.strftime('%b %Y')})",
            value=f"{peak_total:,.0f} bn €",
        )
    with col3:
        st.metric(
            label="Run-off since peak",
            value=f"{runoff:,.0f} bn €",
            delta=f"-{runoff_pct:.1f}%",
            delta_color="inverse",
        )

    st.markdown("---")


    # Chart 1 
    # ---------------------------------------------------------------------
    st.subheader("Total Eurosystem holdings by country")

    total_country = (
        df.groupby(["date", "country"], as_index=False)["holdings_eur_bn"].sum()
    )

    fig1 = px.area(
        total_country,
        x="date",
        y="holdings_eur_bn",
        color="country",
        labels={
            "date": "Date",
            "holdings_eur_bn": "Holdings (€ bn)",
            "country": "Country",
        },
        color_discrete_sequence=["#0F6644", "#4A8B6E", "#7FAF92", "#B5D4C2"],
    )
    fig1.update_layout(
        hovermode="x unified",
        legend=dict(orientation="h", y=-0.2),
        margin=dict(t=20, b=20),
        height=450,
    )
    st.plotly_chart(fig1, use_container_width=True)


    # Chart 2 — PSPP vs PEPP split 
    # ---------------------------------------------------------------------
    st.subheader("Current split PSPP/PEPP")

    latest = df[df["date"] == latest_date].copy()
    latest_pivot = latest.pivot_table(
        index="country",
        columns="programme",
        values="holdings_eur_bn",
        aggfunc="sum",
    ).reset_index()

    fig2 = go.Figure()
    fig2.add_bar(
        x=latest_pivot["country"],
        y=latest_pivot["PSPP"],
        name="PSPP",
        marker=dict(
            color="rgba(15, 102, 68, 0.75)",  
            line=dict(color="#0F6644", width=1.5),
        ),
    )
    fig2.add_bar(
        x=latest_pivot["country"],
        y=latest_pivot["PEPP"],
        name="PEPP",
        marker=dict(
            color="rgba(26, 26, 26, 0.65)",    
            line=dict(color="#1A1A1A", width=1.5),
        ),
    )
    fig2.update_layout(
        barmode="stack",
        xaxis_title="",
        yaxis_title="Holdings (€ bn)",
        legend=dict(orientation="h", y=-0.15),
        margin=dict(t=20, b=20),
        height=400,
    )
    st.plotly_chart(fig2, use_container_width=True)


    st.markdown("---")
    st.caption(
        f"Data sources: ECB APP (PSPP) and PEPP public sector securities · "
    )