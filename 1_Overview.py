import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(
    page_title="Banking Analytics",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Palette & helpers ─────────────────────────────────────────────────────────
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
        xaxis=dict(showgrid=False, zeroline=False, tickfont=dict(color="#9ca3af", size=10),
                   linecolor="#e8eaed"),
        yaxis=dict(showgrid=True, gridcolor="#f3f4f6", zeroline=False,
                   tickfont=dict(color="#9ca3af", size=10)),
    )

def title_kw(text):
    return dict(title=dict(text=text,
                            font=dict(color="#6b7280", size=11, family="Inter"),
                            x=0, xanchor="left", pad=dict(l=0, b=8)))


# ── Data ──────────────────────────────────────────────────────────────────────
@st.cache_data
def load(uploaded=None):
    df = pd.read_csv("Banking_Data.csv")
    print(df.columns.tolist())
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
st.title("🏦 Banking Analytics")
st.caption(
    "Enterprise-level overview of transaction activity, customer growth, "
    "revenue performance, and operational banking trends."
)

# ── KPIs ──────────────────────────────────────────────────────────────────────
total_vol  = df["amount"].sum()
total_tx   = len(df)
avg_tx     = df["amount"].mean()
unique_cus = df["customer_id"].nunique()
fee_rev    = (df["credit_card_fees"] + df["insurance_fees"]).sum()
late_sum   = df["late_payment_amount"].sum()

monthly_vol = df.groupby("month")["amount"].sum().sort_index()
mom = (monthly_vol.iloc[-1]/monthly_vol.iloc[-2]-1)*100 if len(monthly_vol) >= 2 else 0

k1,k2,k3,k4,k5,k6 = st.columns(6)
with k1: st.metric("Total Volume",     fmt(total_vol),  f"{mom:+.1f}% MoM")
with k2: st.metric("Transactions",     f"{total_tx:,}")
with k3: st.metric("Avg Transaction",  fmt(avg_tx))
with k4: st.metric("Active Customers", f"{unique_cus:,}")
with k5: st.metric("Fee Revenue",      fmt(fee_rev))
with k6: st.metric("Late Payments",    fmt(late_sum))

# ── Insight strip ─────────────────────────────────────────────────────────────
top_city = df.groupby("branch_city")["amount"].sum().idxmax()
top_ch   = df.groupby("channel")["amount"].sum().idxmax()
top_seg  = df.groupby("customer_segment")["amount"].sum().idxmax()

i1,i2,i3 = st.columns(3)
with i1:
    st.markdown(
        f'<div class="callout"><b>{top_city}</b> leads all branch cities at '
        f'{df[df["branch_city"]==top_city]["amount"].sum()/total_vol*100:.1f}% of total volume.</div>',
        unsafe_allow_html=True)
with i2:
    st.markdown(
        f'<div class="callout amber"><b>{top_ch}</b> is the dominant channel '
        f'({df[df["channel"]==top_ch]["amount"].sum()/total_vol*100:.1f}% share). Digital-first confirmed.</div>',
        unsafe_allow_html=True)
with i3:
    st.markdown(
        f'<div class="callout green"><b>{top_seg}</b> segment drives the largest revenue share. '
        f'Focus retention and upsell here.</div>',
        unsafe_allow_html=True)

# ── Volume trend ──────────────────────────────────────────────────────────────
st.markdown('### Monthly Volume Trend')

mdf = df.groupby("month").agg(volume=("amount","sum"), count=("transaction_id","count")) \
        .reset_index().sort_values("month")
peak = mdf.loc[mdf["volume"].idxmax()]

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=mdf["month"], y=mdf["volume"], name="volume ($)",
    fill="tozeroy", fillcolor="rgba(37, 99, 235, 0.08)",
    line=dict(color=BLUE, width=2), mode="lines",
    hovertemplate="<b>%{x}</b><br>volume: $%{y:,.0f}<extra></extra>",
))
fig.add_trace(go.Bar(
    x=mdf["month"], y=mdf["count"], name="Transactions",
    yaxis="y2", marker_color="rgba(22, 163, 74, 0.25)", marker_line_width=0,
    hovertemplate="<b>%{x}</b><br>Count: %{y:,}<extra></extra>",
))
fig.add_annotation(
    x=peak["month"], y=peak["volume"],
    text=f"Peak  {fmt(peak['volume'])}",
    showarrow=True, arrowhead=2, arrowcolor="#9ca3af",
    font=dict(color="#6b7280", size=10), bgcolor="#ffffff",
    bordercolor="#e8eaed", borderwidth=1, borderpad=4,
    arrowwidth=1.2, ay=-36, ax=4,
)
layout = base_layout(320)

layout["yaxis"].update({
    "title": "Volume ($)"
})

layout["yaxis2"] = dict(
    overlaying="y",
    side="right",
    showgrid=False,
    zeroline=False,
    tickfont=dict(color="#9ca3af", size=10),
    title="Count"
)

fig.update_layout(
    **layout,
    **title_kw("Monthly transaction volume vs count"),
    legend=dict(
        orientation="h",
        y=1.1,
        font=dict(color="#9ca3af", size=10)
    ),
    barmode="overlay",
)
st.plotly_chart(fig, use_container_width=True)

# ── Bottom row ────────────────────────────────────────────────────────────────
c1,c2,c3 = st.columns(3)

with c1:

    st.markdown("### Transaction Type")

    tx = (
        df["transaction_type"]
        .value_counts()
        .sort_values(ascending=True)
        .reset_index()
    )

    tx.columns = ["transaction_type", "count"]

    max_val = tx["count"].max()

    fig2 = go.Figure()

    fig2.add_trace(go.Bar(
    x=tx["count"],
    y=tx["transaction_type"],
    orientation="h",

    marker=dict(
        color=[
            BLUE if v == max_val else "#dbe4f0"
            for v in tx["count"]
        ]
    ),

    text=[
        f"{v:,}" if v > max_val * 0.35 else None
        for v in tx["count"]
    ],

    textposition="inside",

    textfont=dict(
        color="white",
        size=11
    ),
))

    layout = base_layout(240)

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

    layout["margin"] = dict(
    l=10,
    r=10,
    t=30,
    b=10
    )
    fig2.update_layout(
    **layout,
    showlegend=False)

    st.plotly_chart(fig2, use_container_width=True)

with c2:
    st.markdown('### Channel by volume')
    ch = df.groupby("channel")["amount"].sum().sort_values(ascending=True).reset_index()
    fig3 = go.Figure(go.Bar(
        x=ch["amount"], y=ch["channel"], orientation="h",
        marker=dict(color=[BLUE if i==len(ch)-1 else "#e5e7eb" for i in range(len(ch))],
                    line_width=0),
        text=[fmt(v) for v in ch["amount"]], textposition="inside",
        textfont=dict(color="white", size=10),
    ))
    layout = base_layout(240)
    layout["xaxis"].update({
    "visible": False})
    
    layout["yaxis"].update({
    "showgrid": False,
    "tickfont": dict(color="#374151", size=11)})
    
    fig3.update_layout(
    **layout,
    **title_kw("")
    )
    st.plotly_chart(fig3, use_container_width=True)

with c3:

    st.markdown("### Product Category")

    cat = (
        df["product_category"]
        .value_counts()
        .sort_values(ascending=True)
        .reset_index()
    )

    cat.columns = ["product_category", "count"]

    max_val = cat["count"].max()

    fig4 = go.Figure()

    fig4.add_trace(go.Bar(
        x=cat["count"],
        y=cat["product_category"],
        orientation="h",

        marker=dict(
            color=[
                BLUE if v == max_val else "#e5e7eb"
                for v in cat["count"]
            ]
        ),

        text=cat["count"],
        textposition="inside",
    ))

    layout = base_layout(240)

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

    layout["margin"] = dict(
    l=10,
    r=10,
    t=30,
    b=10
    )
    
    fig4.update_layout(
    **layout,
    showlegend=False
    )

    st.plotly_chart(fig4, use_container_width=True)

# Date range
d0 = pd.to_datetime(df["transaction_date"], errors="coerce").min()
d1 = pd.to_datetime(df["transaction_date"], errors="coerce").max()

d0 = d0.strftime("%Y-%m-%d")
d1 = d1.strftime("%Y-%m-%d")

st.markdown(f"""
<div style="margin-top:20px;font-size:.69rem;color:#d1d5db;font-family:'Inter',sans-serif">
    {len(df):,} rows &nbsp;·&nbsp; {len(df.columns)} columns &nbsp;·&nbsp; {d0} to {d1}
</div>""", unsafe_allow_html=True)

st.markdown("""
Digital channels are now the primary driver of banking activity, with Mobile transactions contributing 
the highest overall volume. Transaction behavior is concentrated around withdrawals, repayments, 
and card-based activity, while Credit Card and Savings products remain the most actively used offerings 
across the customer base.
""")