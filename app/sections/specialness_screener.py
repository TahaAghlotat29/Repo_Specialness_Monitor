"""
Specialness Screener — Bond-by-bond specialness risk score and watchlist.
"""



import plotly.graph_objects as go   
import streamlit as st
import pandas as pd
from src.analytics.specialness_score import load_specialness_score

def render():
    st.title("Specialness Screener")
    st.markdown(
        "**Bond-level specialness risk scoring based on free float scarcity, issue size, age, and maturity bucket.**"
    )
    st.markdown("---")

    st.sidebar.header("Scoring weights")

    w_ff = st.sidebar.slider("Free float scarcity", 0.0, 1.0, 0.40, 0.05)
    w_sz = st.sidebar.slider("Issue size", 0.0, 1.0, 0.20, 0.05)
    w_ag = st.sidebar.slider("Age", 0.0, 1.0, 0.25, 0.05)
    w_mb = st.sidebar.slider("Maturity bucket", 0.0, 1.0, 0.15, 0.05)

    total_w = w_ff + w_sz + w_ag + w_mb

    if abs(total_w - 1.0) > 0.01:
        st.sidebar.warning(f"⚠️ Weights sum to {total_w:.2f}. Normalizing to 1.0 for scoring")
        # Normalize
        if total_w > 0:
            w_ff, w_sz, w_ag, w_mb = (
                w_ff / total_w, w_sz / total_w, w_ag / total_w, w_mb / total_w
            )

    st.sidebar.markdown("---")
    st.sidebar.header("QT scenario simulator")

    qt_shock_pct = st.sidebar.slider(
        "Additional QT shock (%)",
        min_value=-30,
        max_value=30,
        value=0,
        step=5,
        help="+10% means ECB reduces its holdings by an additional 10% vs current levels",
    )

    if qt_shock_pct != 0:
        st.sidebar.caption(f"{qt_shock_pct:+d}% QT shock")

    # Data
    # ---------------------------------------------------------------------

    df = load_specialness_score().copy()


    if qt_shock_pct != 0:
        shock_factor = 1 - (qt_shock_pct / 100)

        mask = df["free_float_pct"] < 90.0  
        original_ecb_ratio = (100 - df.loc[mask, "free_float_pct"]) / 100
        new_ecb_ratio = (original_ecb_ratio * shock_factor).clip(lower=0, upper=1)
        df.loc[mask, "free_float_pct"] = ((1 - new_ecb_ratio) * 100).round(1)

        raw = (100 - df["free_float_pct"]) / 60 * 100
        df["score_free_float"] = raw.clip(lower=0, upper=100).round(1)

    df["specialness_score"] = (
        w_ff * df["score_free_float"]
        + w_sz * df["score_size"]
        + w_ag * df["score_age"]
        + w_mb * df["score_maturity"]
    ).round(1)

    df["risk_tier"] = pd.cut(
        df["specialness_score"],
        bins=[0, 30, 60, 80, 100],
        labels=["Low", "Moderate", "High", "Very High"],
        include_lowest=True,
    )

    df = df.sort_values("specialness_score", ascending=False).reset_index(drop=True)


    # KPIs 
    # ---------------------------------------------------------------------
    tier_counts = df["risk_tier"].value_counts()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Very High risk", int(tier_counts.get("Very High", 0)))
    with col2:
        st.metric("High risk", int(tier_counts.get("High", 0)))
    with col3:
        st.metric("Moderate risk", int(tier_counts.get("Moderate", 0)))
    with col4:
        st.metric("Low risk", int(tier_counts.get("Low", 0)))

    st.markdown("---")


    # Filters
    # ---------------------------------------------------------------------
    col_f1, col_f2 = st.columns([1, 1])

    with col_f1:
        country_filter = st.multiselect(
            "Filter by country",
            options=sorted(df["country"].unique()),
            default=sorted(df["country"].unique()),
        )

    with col_f2:
        issuer_type_filter = st.multiselect(
            "Filter by issuer type",
            options=sorted(df["issuer_type"].unique()),
            default=sorted(df["issuer_type"].unique()),
        )

    df_filtered = df[
        df["country"].isin(country_filter) & df["issuer_type"].isin(issuer_type_filter)
    ].copy()


    # Chart 
    # ---------------------------------------------------------------------

    st.subheader("Specialness risk ")

    def _tier_color(score):
        if score >= 80:
            return "#B22222"   
        if score >= 60:
            return "#D97706"   
        if score >= 30:
            return "#0F6644"   
        return "#7FAF92"       


    df_plot = df_filtered.sort_values("specialness_score", ascending=True)
    colors = [_tier_color(s) for s in df_plot["specialness_score"]]

    fig_heat = go.Figure()
    fig_heat.add_bar(
        x=df_plot["specialness_score"],
        y=df_plot["bloomberg_ticker"],
        orientation="h",
        marker=dict(
            color=colors,
            line=dict(color="#1A1A1A", width=0.8),
        ),
        text=df_plot["specialness_score"].round(1),
        textposition="outside",
        hovertemplate=(
            "<b>%{y}</b><br>"
            "ISIN: %{customdata[0]}<br>"
            "Country: %{customdata[1]}<br>"
            "Score: %{x:.1f}<br>"
            "Free float: %{customdata[2]:.1f}%<br>"
            "<extra></extra>"
        ),
        customdata=df_plot[["isin", "country", "free_float_pct"]].values,
    )
    fig_heat.update_layout(
        xaxis_title="Specialness score",
        yaxis_title="",
        xaxis=dict(range=[0, 100]),
        margin=dict(t=20, b=20, l=20, r=40),
        height=max(300, 30 * len(df_plot)),
        showlegend=False,
    )
    st.plotly_chart(fig_heat, use_container_width=True)


    # Table — Top 10 watchlist
    # ---------------------------------------------------------------------
    st.subheader("Top 10 watchlist")

    top10 = df_filtered.head(10)[
        [
            "bloomberg_ticker",
            "isin",
            "issuer",
            "country",
            "maturity_bucket",
            "free_float_pct",
            "outstanding_eur_bn",
            "specialness_score",
            "risk_tier",
        ]
    ].rename(
        columns={
            "bloomberg_ticker": "Ticker",
            "isin": "ISIN",
            "issuer": "Issuer",
            "country": "Country",
            "maturity_bucket": "Bucket",
            "free_float_pct": "Free float (%)",
            "outstanding_eur_bn": "Outstanding (€ bn)",
            "specialness_score": "Score",
            "risk_tier": "Tier",
        }
    )
    st.dataframe(top10, use_container_width=True, hide_index=True)

    st.markdown("---")



    # Bond comparator 
    # ---------------------------------------------------------------------

    st.subheader("Bond comparator")
    st.caption("Select two bonds to compare their specialness score breakdown side by side")

    col_sel1, col_sel2 = st.columns(2)

    with col_sel1:
        bond_a_ticker = st.selectbox(
            "Bond A",
            options=df_filtered["bloomberg_ticker"].tolist(),
            index=0,
        )

    with col_sel2:
        bond_b_ticker = st.selectbox(
            "Bond B",
            options=df_filtered["bloomberg_ticker"].tolist(),
            index=min(1, len(df_filtered) - 1),
        )

    bond_a = df_filtered[df_filtered["bloomberg_ticker"] == bond_a_ticker].iloc[0]
    bond_b = df_filtered[df_filtered["bloomberg_ticker"] == bond_b_ticker].iloc[0]


    def _bond_summary(bond):

        """Return a short summary markdown block for a bond"""

        return f"""
        **{bond['bloomberg_ticker']}**  
        *{bond['isin']}*  

        - **Issuer:** {bond['issuer']}  
        - **Country:** {bond['country']}  
        - **Maturity:** {bond['maturity_date'].strftime('%Y-%m-%d')}  
        - **Outstanding:** {bond['outstanding_eur_bn']:.1f} bn €  
        - **Free float:** {bond['free_float_pct']:.1f} %  
        - **Score:** **{bond['specialness_score']:.1f}** / 100  
        - **Tier:** {bond['risk_tier']}
        """


    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(_bond_summary(bond_a))
    with col_b:
        st.markdown(_bond_summary(bond_b))


    features_a = [
        bond_a["score_free_float"] * w_ff,
        bond_a["score_size"] * w_sz,
        bond_a["score_age"] * w_ag,
        bond_a["score_maturity"] * w_mb,
    ]
    features_b = [
        bond_b["score_free_float"] * w_ff,
        bond_b["score_size"] * w_sz,
        bond_b["score_age"] * w_ag,
        bond_b["score_maturity"] * w_mb,
    ]
    feature_labels = [
        f"Free float ({w_ff:.0%})",
        f"Size ({w_sz:.0%})",
        f"Age ({w_ag:.0%})",
        f"Maturity ({w_mb:.0%})",
    ]

    fig_cmp = go.Figure()
    fig_cmp.add_bar(
        x=feature_labels,
        y=features_a,
        name=bond_a["bloomberg_ticker"],
        marker=dict(
            color="rgba(15, 102, 68, 0.75)",
            line=dict(color="#0F6644", width=1.5),
        ),
    )
    fig_cmp.add_bar(
        x=feature_labels,
        y=features_b,
        name=bond_b["bloomberg_ticker"],
        marker=dict(
            color="rgba(26, 26, 26, 0.65)",
            line=dict(color="#1A1A1A", width=1.5),
        ),
    )
    fig_cmp.update_layout(
        title="Feature contribution comparison ",
        yaxis_title="Weighted contribution",
        xaxis_title="",
        barmode="group",
        legend=dict(orientation="h", y=-0.15),
        margin=dict(t=40, b=20),
        height=400,
    )
    st.plotly_chart(fig_cmp, use_container_width=True)


    st.markdown("---")