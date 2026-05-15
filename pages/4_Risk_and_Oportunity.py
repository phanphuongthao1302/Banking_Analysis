import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(
    page_title="Risk and Opportunity",
    page_icon = "⚠️", 
    layout="wide")


BLUE, GREEN, AMBER, RED, PURPLE, TEAL = "#2563eb","#16a34a","#d97706","#dc2626","#7c3aed","#0891b2"
SEQ = [BLUE, GREEN, AMBER, PURPLE, TEAL, RED]

def fmt(n, prefix="$"):
    if abs(n) >= 1e6: return f"{prefix}{n/1e6:.2f}M"
    if abs(n) >= 1e3: return f"{prefix}{n/1e3:.1f}K"
    return f"{prefix}{n:,.0f}"

def base_layout(height=300):
    return dict(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#ffffff",
        font=dict(family="Inter, sans-serif", color="#6b7280", size=11),
        margin=dict(l=4, r=4, t=32, b=4), height=height,
        hoverlabel=dict(bgcolor="#ffffff", bordercolor="#e8eaed",
                        font=dict(family="Inter", color="#111827", size=12)),
        xaxis=dict(showgrid=False, zeroline=False, tickfont=dict(color="#9ca3af",size=10), linecolor="#e8eaed"),
        yaxis=dict(showgrid=True, gridcolor="#f3f4f6", zeroline=False, tickfont=dict(color="#9ca3af",size=10)),
    )

def title_kw(text):
    return dict(title=dict(text=text, font=dict(color="#6b7280",size=11,family="Inter"),
                            x=0, xanchor="left", pad=dict(l=0,b=8)))

# ── Data ──────────────────────────────────────────────────────────────────────
@st.cache_data
def load(uploaded=None):
    df = pd.read_csv("Banking_Data.csv")
    return df

    d0 = df["transaction_date"].min().date()
    d1 = df["transaction_date"].max().date()    

def _clean(df):

    # ── Date cleaning ────────────────────────────────────────
    if "transaction_date" in df.columns:

        df["transaction_date"] = pd.to_datetime(
            df["transaction_date"],
            errors="coerce"
        )

        df["quarter"] = (
            df["transaction_date"]
            .dt.to_period("Q")
            .astype(str)
        )

        df["day_of_week"] = (
            df["transaction_date"]
            .dt.day_name()
        )

        df["hour"] = (
            df["transaction_date"]
            .dt.hour
        )

        df["month"] = (
            df["transaction_date"]
            .dt.to_period("M")
            .astype(str)
        )
    return df

df = load()
df = _clean(df)

# ── Risk Scoring ─────────────────────────────────────────────────────────
df["risk_flag"] = np.where(
    (df["late_payment_amount"] > 0)
    & (df["customer_score"] < 550),
    "High Risk",
    np.where(
        (df["customer_score"] < 650),
        "Medium Risk",
        "Low Risk"
    )
)

# ── Header ───────────────────────────────────────────────────────────────
st.title("⚠️ Risk & Opportunity")
st.caption(
    "Fraud signals, customer risk exposure, and upsell opportunities in one operational view"
)
# ── KPI Row ──────────────────────────────────────────────────────────────
high_risk_customers = (
    df[df["risk_flag"] == "High Risk"]
    ["customer_id"]
    .nunique()
)

late_payment_total = df["late_payment_amount"].sum()

premium_customers = (
    df[df["customer_segment"].isin(["High Income Segment"])]
    ["customer_id"]
    .nunique()
)

recommended_offer_rate = (
    df["recommended_offer"]
    .notna()
    .mean() * 100
)
k1, k2, k3, k4 = st.columns(4)

with k1:
    st.metric(
        "High Risk Customers",
        f"{high_risk_customers:,}"
    )

with k2:
    st.metric(
        "Late Payment Exposure",
        fmt(late_payment_total)
    )

with k3:
    st.metric(
        "High Income Segment",
        f"{premium_customers:,}"
    )
with k4:
    st.metric(
        "Offer Coverage",
        f"{recommended_offer_rate:.1f}%"
    )

# ── Risk vs Opportunity ──────────────────────────────────────────────────
left, right = st.columns(2)

with left:

    risk_df = (
        df.groupby("risk_flag")
        .agg(
            customers=("customer_id", "nunique"),
            exposure=("late_payment_amount", "sum")
        )
        .reset_index()
    )

    colors = [RED, AMBER, GREEN]
    fig_risk = go.Figure(
        go.Bar(
            x=risk_df["risk_flag"],
            y=risk_df["customers"],
            marker_color=colors,
            text=[f"{x:,}" for x in risk_df["customers"]],
            textposition="inside"
        )
    )

    fig_risk.update_layout(
        **base_layout(320),
        title="Customer Risk Distribution",
        showlegend=False
    )

    st.plotly_chart(fig_risk, use_container_width=True)
with right:

    opp_df = (
        df.groupby("recommended_offer")
        .agg(
            customers=("customer_id", "nunique")
        )
        .sort_values("customers", ascending=False)
        .head(8)
        .reset_index()
    )

    max_val = opp_df["customers"].max()

    fig_offer = go.Figure(
        go.Bar(
            x=opp_df["recommended_offer"],
            y=opp_df["customers"],
            marker_color=[
                PURPLE if v == max_val else "#dbeafe"
                for v in opp_df["customers"]
            ], text=[f"{v:,}" for v in opp_df["customers"]],
            textposition="inside"
        )
    )
    layout = base_layout(320)
    
    layout["xaxis"].update({
    "tickangle": -20,
    "showgrid": False
}) 
    fig_offer.update_layout(
    **layout,
    title="Top Recommended Offers",
    showlegend=False
)

    st.plotly_chart(fig_offer, use_container_width=True)

st.markdown("""
**Customer Risk Distribution:** The majority of customers fall into the Medium Risk tier (6,455), while High Risk accounts for only 1,392 — the portfolio is relatively healthy but high-risk cases should be prioritised for immediate action.

**Top Recommended Offers:** Mid-tier Savings Booster dominates with 3,959 recommendations, indicating that most customers sit in the mid-income bracket and respond best to accessible savings products.""")


    # ── Risk Heatmap ─────────────────────────────────────────────────────────
st.subheader("Risk Exposure by Segment")

heat = (
    df.groupby(["customer_segment", "channel"])
    ["late_payment_amount"]
    .sum()
    .reset_index()
)

pivot = heat.pivot(
    index="customer_segment",
    columns="channel",
    values="late_payment_amount"
).fillna(0)
fig_heat = go.Figure(
    go.Heatmap(
        z=pivot.values,
        x=pivot.columns,
        y=pivot.index,
        colorscale="Reds",
        text=np.round(pivot.values, 0),
        texttemplate="%{text:,.0f}",
        hovertemplate="%{y}<br>%{x}<br>$%{z:,.0f}<extra></extra>"
    )
)

fig_heat.update_layout(
    **base_layout(300),
    title="Late Payment Exposure by Segment & Channel"
)

st.plotly_chart(fig_heat, use_container_width=True)

st.markdown("""The Middle Income Segment consistently shows the highest late payment 
exposure across all channels peaking at 3.6M via Branch 
making it the most urgent segment to target with payment reminder campaigns. 
The High Income Segment carries moderate exposure (~$2.3), while the Low Income Segment, despite expectations, records the lowest figures,
 likely due to smaller loan/credit amounts.""")
# ── Opportunity Table ────────────────────────────────────────────────────
st.subheader("Best Upsell Opportunities")

opp_table = (
    df.groupby(["customer_segment", "recommended_offer"])
    .agg(
        Customers=("customer_id", "nunique"),
        AvgIncome=("monthly_income", "mean"),
        AvgScore=("customer_score", "mean"),
        Volume=("amount", "sum")
    )
    .reset_index()
    .sort_values("Volume", ascending=False)
    .head(12)
)

opp_table["AvgIncome"] = opp_table["AvgIncome"].apply(fmt)
opp_table["Volume"] = opp_table["Volume"].apply(fmt)
opp_table["AvgScore"] = opp_table["AvgScore"].round(0)
st.dataframe(
    opp_table,
    use_container_width=True,
    hide_index=True
)
# ── Fraud Signals ────────────────────────────────────────────────────────
st.subheader("Potential Fraud Signals")

fraud_df = df[
    (df["amount"] > df["amount"].quantile(0.99))
    & (df["channel"] == "ATM")
].copy()

fraud_df = fraud_df[
    [
        "transaction_id",
        "customer_id",
        "transaction_type",
        "amount",
        "channel",
        "branch_city",
        "customer_score"
    ]
]

fraud_df["amount"] = fraud_df["amount"].apply(fmt)
st.dataframe(
    fraud_df.head(20),
    use_container_width=True,
    hide_index=True
)
# ── Executive Summary ────────────────────────────────────────────────────
st.subheader("Executive Summary")

st.info(
    f"""
    • High-risk customers are concentrated in low-score segments with recurring late payments.

    • ATM transactions contain the highest number of abnormal high-value withdrawals.

    • High Income clients generate the strongest upsell potential for investment and insurance products.

    • Recommended offers are heavily concentrated around a few high-performing products, creating opportunity for targeted campaigns.
    """
)
