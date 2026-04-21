"""
Repo Specialness Monitor 
"""

import sys
from pathlib import Path
import plotly.graph_objects as go
import streamlit as st
from streamlit_option_menu import option_menu
from app.sections import macro_overview, repo_tension_monitor, specialness_screener
from src.analytics.free_float import load_free_float
from src.analytics.specialness_score import load_specialness_score
from src.analytics.tension_signals import load_tension_signals
from src.ingestion.ecb_holdings import load_holdings

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# Page config 
# ---------------------------------------------------------------------
st.set_page_config(
    page_title="Repo Specialness Monitor",
    layout="wide",
    initial_sidebar_state="collapsed",
)

selected = option_menu(
    menu_title=None,
    options=["Home", "Macro Overview", "Repo Tension", "Specialness Screener"],
    icons=["house", "graph-up", "activity", "bullseye"],
    orientation="horizontal",
    default_index=0,
    styles={
        "container": {
            "padding": "0!important",
            "background-color": "#FFFFFF",
            "border-bottom": "2px solid #0F6644",
        },
        "icon": {"color": "#0F6644", "font-size": "16px"},
        "nav-link": {
            "font-size": "14px",
            "font-weight": "500",
            "text-align": "center",
            "margin": "0px",
            "padding": "12px 20px",
            "color": "#1A1A1A",
            "--hover-color": "#F5F6F5",
        },
        "nav-link-selected": {
            "background-color": "#0F6644",
            "color": "#FFFFFF",
            "font-weight": "600",
        },
    },
)



# Home page 
# ---------------------------------------------------------------------
def render_home():
    st.title("Repo Specialness Monitor")
    st.markdown(
        "**Tracking ECB Quantitative Tightening effects on EUR sovereign repo markets.**"
    )
    st.markdown("---")

    st.markdown(
        """
        The Eurosystem accumulated massive sovereign bond holdings via the **APP** and
        **PEPP** purchase programmes. As **quantitative tightening
        (QT)** unfolds, this collateral progressively returns to the market and reshapes the
        free float and specialness dynamics across the EUR repo universe.
        """
    )
    st.markdown("---")

    # -------------- KPIs --------------
    holdings = load_holdings()
    free_float = load_free_float()
    tension = load_tension_signals()
    scores = load_specialness_score()

    latest_date = holdings["date"].max()

    total_ez = holdings[holdings["date"] == latest_date]["holdings_eur_bn"].sum()

    total_by_date = holdings.groupby("date")["holdings_eur_bn"].sum()
    peak_ez = total_by_date.max()
    peak_date = total_by_date.idxmax()
    runoff_pct = (peak_ez - total_ez) / peak_ez * 100

    current_regime = tension.iloc[-1]["regime"]
    high_risk_count = scores[scores["risk_tier"].isin(["High", "Very High"])].shape[0]

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Eurozone holdings (now)", f"{total_ez:,.0f} bn €")
    with col2:
        st.metric("Peak holdings", f"{peak_ez:,.0f} bn €",
                  delta=f"-{runoff_pct:.1f}% since peak",
                  delta_color="inverse")
    with col3:
        st.metric("Market regime", current_regime)
    with col4:
        st.metric("Bonds at High risk", high_risk_count)

    st.markdown("---")

    st.subheader("Eurosystem sovereign holdings")

    total_ez_series = (
        holdings.groupby("date", as_index=False)["holdings_eur_bn"].sum()
    )

    fig = go.Figure()

    fig.add_scatter(
        x=total_ez_series["date"],
        y=total_ez_series["holdings_eur_bn"],
        mode="lines",
        line=dict(color="#0F6644", width=2.5),
        fill="tozeroy",
        fillcolor="rgba(15, 102, 68, 0.15)",
        name="Total Eurosystem holdings",
        hovertemplate="<b>%{x|%b %Y}</b><br>%{y:,.0f} bn €<extra></extra>",
    )

    fig.add_annotation(
        x=peak_date,
        y=peak_ez,
        text=f"<b>Peak QE</b><br>{peak_ez:,.0f} bn €",
        showarrow=True,
        arrowhead=2,
        arrowcolor="#1A1A1A",
        ax=0, ay=-50,
        font=dict(size=12, color="#1A1A1A"),
        bgcolor="rgba(255,255,255,0.9)",
        bordercolor="#1A1A1A",
        borderwidth=1,
    )

    fig.add_annotation(
        x=latest_date,
        y=total_ez,
        text=f"<b>Now</b><br>{total_ez:,.0f} bn €",
        showarrow=True,
        arrowhead=2,
        arrowcolor="#0F6644",
        ax=-40, ay=-40,
        font=dict(size=12, color="#0F6644"),
        bgcolor="rgba(255,255,255,0.9)",
        bordercolor="#0F6644",
        borderwidth=1,
    )

    fig.add_vrect(
        x0=peak_date,
        x1=latest_date,
        fillcolor="rgba(178, 34, 34, 0.08)",
        line_width=0,
        annotation_text="QT phase",
        annotation_position="top left",
        annotation_font=dict(size=11, color="#B22222"),
    )

    fig.update_layout(
        yaxis_title="Holdings (€ bn)",
        xaxis_title="",
        height=500,
        margin=dict(t=20, b=20),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    st.subheader("Explore further")
    st.markdown(
        """
        - **Macro Overview** — Country-level breakdown of Eurosystem holdings (DE, FR, IT, ES)
          and split between PSPP and PEPP programmes.
        - **Repo Tension** — €STR vs ECB Deposit Facility Rate, market regime classification,
          and historical episodes of collateral scarcity.
        - **Specialness Screener** — Bond-by-bond specialness risk scoring with adjustable
          weights, QT scenario simulator, and side-by-side bond comparator.
        """
    )

    st.markdown("---")
    st.caption(
        f"Data sources: ECB APP/PEPP, €STR, Deposit Facility Rate · "
        f"Latest observation: {latest_date.date()}  "
        
    )



if selected == "Home":
    render_home()
elif selected == "Macro Overview":
    macro_overview.render()
elif selected == "Repo Tension":
    repo_tension_monitor.render()
elif selected == "Specialness Screener":
    specialness_screener.render()