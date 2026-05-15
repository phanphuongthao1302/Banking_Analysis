import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(
    page_title="Business Performance",
    page_icon = "💰", 
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

# ── Header ───────────────────────────────────────────────────────────────
st.title("💰 Business Performance")
st.caption(
    "Track branch performance, transaction behavior, channel efficiency,"
    "and product contribution across the banking network."
)

# ── Filters ───────────────────────────────────────────────────────────────────
fc1, fc2, fc3 = st.columns(3)
with fc1:
    cities = ["All"] + sorted(df["branch_city"].unique())
    sel_city = st.selectbox("city", cities)
with fc2:
    qtrs = ["All"] + sorted(df["quarter"].unique())
    sel_q = st.selectbox("quarter", qtrs)
with fc3:
    types = ["All"] + sorted(df["transaction_type"].unique())
    sel_t = st.selectbox("transaction_type", types)

dff = df.copy()
if sel_city != "All": dff = dff[dff["branch_city"] == sel_city]
if sel_q    != "All": dff = dff[dff["quarter"] == sel_q]
if sel_t    != "All": dff = dff[dff["transaction_type"] == sel_t]

# ── KPIs ──────────────────────────────────────────────────────────────────────
k1,k2,k3,k4 = st.columns(4)
with k1: st.metric("Filtered Volume",  fmt(dff["amount"].sum()))
with k2: st.metric("Transactions",     f"{len(dff):,}")
with k3: st.metric("Avg Transaction",  fmt(dff["amount"].mean()))
with k4: st.metric("Active Customers", f"{dff['customer_id'].nunique():,}")

# ── City performance ──────────────────────────────────────────────────────────
st.markdown("### Branch City Performance")

city_df = dff.groupby("branch_city").agg(
    volume=("amount", "sum"),
    count=("transaction_id", "count"),
    avg_amt=("amount", "mean"),
    customers=("customer_id", "nunique"),
).sort_values("volume", ascending=False).reset_index()

city_df["share"] = city_df["volume"] / city_df["volume"].sum() * 100

ca, cb = st.columns([3, 2])

with ca:
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=city_df["branch_city"],
        y=city_df["volume"],
        name="Volume",
        marker=dict(
            color=[BLUE if i == 0 else "#e5e7eb" for i in range(len(city_df))]
        ),
    ))

    fig.add_trace(go.Scatter(
        x=city_df["branch_city"],
        y=city_df["avg_amt"],
        name="Avg Transaction",
        yaxis="y2",
        mode="lines+markers",
        line=dict(color=AMBER, width=2, dash="dot"),
        marker=dict(size=7, color=AMBER),
    ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#ffffff",
        height=280,

        title=dict(
            text="Volume & average transaction by city",
            x=0,
            font=dict(size=15)
        ),

        xaxis=dict(
            showgrid=False,
            tickfont=dict(size=10)
        ),

        yaxis=dict(
            title="Volume",
            showgrid=True,
            gridcolor="#f3f4f6"
        ),

        yaxis2=dict(
            title="Avg Transaction",
            overlaying="y",
            side="right",
            showgrid=False
        ),

        legend=dict(
            orientation="h",
            y=1.1
        )
    )

    st.plotly_chart(fig, use_container_width=True)

with cb:

    st.markdown(
        'Top 5 Cities'
    )

    top5 = city_df.head(5).copy()

    top5["Revenue"] = top5["volume"].apply(fmt)

    top5["Avg Transaction"] = top5["avg_amt"].apply(fmt)

    top5["Share %"] = top5["share"].round(1).astype(str) + "%"

    top5 = top5.rename(columns={
        "branch_city": "City",
        "count": "Transactions",
        "customers": "Customers"
    })

    st.dataframe(
        top5[[
            "City",
            "Revenue",
            "Transactions",
            "Customers",
            "Avg Transaction",
            "Share %"
        ]],
        use_container_width=True,
        hide_index=True
    )

st.markdown("""
Barcelona leads overall transaction volume, while Malaga and Murcia maintain similarly strong customer activity. 
Average transaction values remain stable across cities, indicating balanced operational performance throughout the network.
""")

# ── Fee Revenue ───────────────────────────────────────────────────────────────
st.markdown('### Fee Revenue & Channel Trends')

cd, ce = st.columns(2)

with cd:

    fee_m = dff.groupby("month").agg(
        cc=("credit_card_fees", "sum"),
        insurance=("insurance_fees", "sum"),
        late=("late_payment_amount", "sum")
    ).reset_index()

    fig_fee = go.Figure()

    fig_fee.add_trace(go.Scatter(
        x=fee_m["month"],
        y=fee_m["cc"],
        stackgroup="one",
        name="Credit Card"
    ))

    fig_fee.add_trace(go.Scatter(
        x=fee_m["month"],
        y=fee_m["insurance"],
        stackgroup="one",
        name="Insurance"
    ))

    fig_fee.add_trace(go.Scatter(
        x=fee_m["month"],
        y=fee_m["late"],
        stackgroup="one",
        name="Late Payment"
    ))

    fig_fee.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#ffffff",
        height=270,

        title=dict(
            text="Stacked fee revenue by month",
            x=0
        ),

        xaxis=dict(showgrid=False),

        yaxis=dict(
            showgrid=True,
            gridcolor="#f3f4f6"
        )
    )

    st.plotly_chart(fig_fee, use_container_width=True)

with ce:

    ch_m = dff.groupby(
        ["month", "channel"]
    )["amount"].sum().reset_index()

    fig_ch = go.Figure()

    for ch in ch_m["channel"].unique():

        sub = ch_m[ch_m["channel"] == ch]

        fig_ch.add_trace(go.Scatter(
            x=sub["month"],
            y=sub["amount"],
            mode="lines+markers",
            name=ch
        ))

    fig_ch.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#ffffff",
        height=270,

        title=dict(
            text="Volume by channel",
            x=0
        ),

        xaxis=dict(showgrid=False),

        yaxis=dict(
            showgrid=True,
            gridcolor="#f3f4f6"
        )
    )

    st.plotly_chart(fig_ch, use_container_width=True)

st.markdown("""
Fee revenue is still heavily dependent on late payment activity, highlighting both revenue opportunity 
and potential customer credit stress. Meanwhile, sustained Mobile channel leadership confirms that 
customer engagement is increasingly concentrated in digital banking platforms.
""")

# ── Waterfall ─────────────────────────────────────────────────────────────────
st.markdown("### Product Category Contribution")

prod = (
    dff.groupby("product_category")["amount"]
    .sum()
    .sort_values(ascending=True)
    .reset_index()
)

max_val = prod["amount"].max()

fig_prod = go.Figure()

fig_prod.add_trace(go.Bar(
    x=prod["amount"],
    y=prod["product_category"],
    orientation="h",

    marker=dict(
        color=[
            BLUE if v == max_val else "#e5e7eb"
            for v in prod["amount"]
        ]
    ),

    text=[
        fmt(v) if v > max_val * 0.25 else None
        for v in prod["amount"]
    ],

    textposition="inside",

    insidetextanchor="middle",

    textfont=dict(
        color="white",
        size=11
    )
))

layout = base_layout(280)

layout["xaxis"].update({
    "visible": False
})

layout["yaxis"].update({
    "showgrid": False,
    "tickfont": dict(
        color="#374151",
        size=11
    )
})

fig_prod.update_layout(
    **layout,
    showlegend=False
)

st.plotly_chart(fig_prod, use_container_width=True)

st.markdown("""
Mortgage products generate the highest transaction volume, contributing over $30M
and clearly outperforming all other banking product categories. Loan and Credit Card
products also represent major revenue drivers, indicating strong customer demand for
borrowing and credit-based services.

Lower contribution from Savings and Checking Accounts suggests these products function
primarily as transactional or retention products rather than core revenue generators.
Opportunity exists to increase cross-selling from deposit products into higher-margin
lending and mortgage offerings.
""")