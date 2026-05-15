import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(
    page_title="Customer Intelligence",
    page_icon="👜", layout="wide")

BLUE, GREEN, AMBER, RED, PURPLE, TEAL = "#2563eb","#16a34a","#d97706","#dc2626","#7c3aed","#0891b2"
SEG_COLORS = {"Low Income Segment":BLUE,"Middle Income Segment":PURPLE,"High Income Segment":GREEN}
SEG_ORDER  = ["Low Income Segment","Middle Income Segment","High Income Segment"]

SEG_FILL = {
    "Low Income Segment": "rgba(37, 99, 235, 0.35)",
    "Middle Income Segment": "rgba(22, 163, 74, 0.35)",
    "High Income Segment": "rgba(124, 58, 237, 0.35)",
}

SEG_FILL_LIGHT = {
    "Low Income Segment": "rgba(37, 99, 235, 0.15)",
    "Middle Income Segment": "rgba(22, 163, 74, 0.15)",
    "High Income Segment": "rgba(124, 58, 237, 0.15)",
}

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
st.title("👜 Customer Intelligence")
st.caption(
    "Analyze customer segments, behavioral patterns, income profiles, "
    "and engagement opportunities across the portfolio."
)

# ── Segment scorecards ────────────────────────────────────────────────────────
st.markdown('### Segment Overview')

seg_agg = (
    df.groupby("customer_segment")
    .agg(
        Customers=("customer_id", "nunique"),
        volume=("amount", "sum"),
        AvgTx=("amount", "mean"),
        AvgScore=("customer_score", "mean"),
        AvgIncome=("monthly_income", "mean"),
        LateRate=("late_payment_amount", lambda x: (x > 0).mean()),
    )
    .reindex(SEG_ORDER)
    .fillna(0)
    .reset_index()
)
total_vol  = df["amount"].sum()
cols = st.columns(4)
for col, (_, row) in zip(cols, seg_agg.iterrows()):
    color = SEG_COLORS.get(row["customer_segment"], BLUE)
    share = row["volume"] / total_vol * 100
    with col:
        st.markdown(f"""
        <div class="card" style="border-top:3px solid {color}">
            <div style="font-size:.68rem;font-weight:700;text-transform:uppercase;
                        letter-spacing:.1em;color:#9ca3af;margin-bottom:6px">{row['customer_segment']}</div>
            <div style="font-size:1.6rem;font-weight:700;color:{color};letter-spacing:-.02em;line-height:1">
                {int(row['Customers']):,}
            </div>
            <div style="font-size:.76rem;color:#9ca3af;margin-top:4px">customers · {share:.1f}% of volume</div>
            <div style="border-top:1px solid #f3f4f6;margin:12px 0"></div>
            <div style="font-size:.75rem;color:#9ca3af;line-height:1.85">
                Avg Score<span style="float:right;color:#374151;font-weight:600">{row['AvgScore']:.0f}</span><br>
                Avg Income<span style="float:right;color:#374151;font-weight:600">{fmt(row['AvgIncome'])}</span><br>
                Late Pay Rate<span style="float:right;color:{'#dc2626' if row['LateRate']>.15 else '#374151'};font-weight:600">{row['LateRate']:.1%}</span>
            </div>
        </div>""", unsafe_allow_html=True)

# ── Segment volume over time ──────────────────────────────────────────────────
st.markdown('### Segment Volume Over Time')

seg_m = df.groupby(["month","customer_segment"])["amount"].sum().reset_index().sort_values("month")
fig_area = go.Figure()
SEG_FILL_LIGHT = {
    "Low Income Segment": "rgba(37, 99, 235, 0.15)",
    "Middle Income Segment": "rgba(22, 163, 74, 0.15)",
    "High Income Segment": "rgba(124, 58, 237, 0.15)",
}
for seg in SEG_ORDER:
    sub = seg_m[seg_m["customer_segment"] == seg]

    fig_area.add_trace(go.Scatter(
        x=sub["month"],
        y=sub["amount"],
        name=seg,
        stackgroup="one",
        mode="lines",
        line=dict(width=0),
        fillcolor=SEG_FILL[seg],
    ))
layout = base_layout(290)

layout["yaxis"].update({
    "showgrid": True,
    "gridcolor": "#f3f4f6",
    "zeroline": False,
    "tickfont": dict(color="#9ca3af", size=10)
})

layout["xaxis"].update({
    "showgrid": False,
    "tickfont": dict(color="#9ca3af", size=10)
})

fig_area.update_layout(
    **layout,
    **title_kw("Stacked transaction volume by customer segment"),
    legend=dict(
        orientation="h",
        y=1.1,
        font=dict(color="#9ca3af", size=10)
    )
)
st.plotly_chart(fig_area, use_container_width=True)

# ── Score distribution + Income scatter ──────────────────────────────────────
st.markdown('### Score Distribution & Income Profile')
c1, c2 = st.columns(2)

with c1:
    fig_box = go.Figure()
    for seg in SEG_ORDER:
        sub = df[df["customer_segment"] == seg]["customer_score"]
        
        fig_box.add_trace(go.Box(
            y=sub,
            name=seg,
            marker_color=SEG_COLORS[seg],
            line_color=SEG_COLORS[seg],
            fillcolor=SEG_FILL_LIGHT[seg],
            boxmean=True,
    ))
    layout = base_layout(280)
    
    layout["yaxis"].update({
    "showgrid": True,
    "gridcolor": "#f3f4f6",
    "zeroline": False,
    "tickfont": dict(color="#9ca3af", size=10),
    "title": "Score"
})

    layout["xaxis"].update({
    "showgrid": False,
    "tickfont": dict(color="#374151", size=11)
})

    fig_box.update_layout(
    **layout,
    **title_kw("Credit score distribution by segment"),
    showlegend=False
)
    st.plotly_chart(fig_box, use_container_width=True)
    st.markdown("""
        Clear score stratification across segments. High Income Segment averages ~730 vs Low Income Segment ~500.
        Score is a reliable signal for product eligibility and risk pricing.
    """)

with c2:
    cust_df = df.groupby("customer_id").agg(
        Income=("monthly_income","first"), AvgAmt=("amount","mean"),
        Segment=("customer_segment","first"),
    ).reset_index().sample(min(500,len(df)), random_state=42)
    fig_sc = go.Figure()
    for seg in SEG_ORDER:
        sub = cust_df[cust_df["Segment"]==seg]
        fig_sc.add_trace(go.Scatter(
            x=sub["Income"], y=sub["AvgAmt"], name=seg, mode="markers",
            marker=dict(size=6, color=SEG_COLORS[seg], opacity=.6, line=dict(width=0)),
        ))
    layout = base_layout(280)

    layout["xaxis"].update({
    "showgrid": False,
    "tickfont": dict(color="#9ca3af", size=10),
    "title": "Monthly Income ($)"
})

    layout["yaxis"].update({
    "showgrid": True,
    "gridcolor": "#f3f4f6",
    "zeroline": False,
    "tickfont": dict(color="#9ca3af", size=10),
    "title": "Avg Transaction ($)"
})

    fig_sc.update_layout(
    **layout,
    **title_kw("Monthly income vs average transaction size"),
    legend=dict(
        orientation="h",
        y=1.1,
        font=dict(color="#9ca3af", size=10)
    )
)
    st.plotly_chart(fig_sc, use_container_width=True)
    st.markdown("""
        Low Income Segment customers show high variance relative to income — behaviour is driven by
        external triggers (paydays, promotions) more than income level alone.
   """, unsafe_allow_html=True)

# ── Channel affinity heatmap ──────────────────────────────────────────────────
st.markdown('### Channel Affinity by Segment')

ch_seg = df.groupby(["customer_segment","channel"])["transaction_id"].count().reset_index()
ch_seg.columns = ["Segment","Channel","Count"]
pivot = ch_seg.pivot(index="Segment", columns="Channel", values="Count").fillna(0)
pivot_pct = pivot.div(pivot.sum(axis=1), axis=0) * 100
pivot_pct = pivot_pct.reindex([s for s in SEG_ORDER if s in pivot_pct.index])

fig_aff = go.Figure(go.Heatmap(
    z=pivot_pct.values, x=pivot_pct.columns.tolist(), y=pivot_pct.index.tolist(),
    colorscale=[[0,"#f8fafc"],[0.5,"#93c5fd"],[1,"#1d4ed8"]],
    text=[[f"{v:.1f}%" for v in row] for row in pivot_pct.values],
    texttemplate="%{text}", textfont=dict(color="#374151",size=12,family="Inter"),
    showscale=False,
    hovertemplate="<b>%{y}</b> · %{x}: <b>%{z:.1f}%</b><extra></extra>",
))
fig_aff.update_layout(**{
    **base_layout(210),
    "title":dict(text="Channel share (%) per segment — row normalised",
                 font=dict(color="#6b7280",size=11),x=0,xanchor="left"),
    "xaxis":dict(tickfont=dict(color="#374151",size=11),showgrid=False),
    "yaxis":dict(tickfont=dict(color="#374151",size=11),showgrid=False),
})
st.plotly_chart(fig_aff, use_container_width=True)
st.markdown("""<div class="callout green">
    Mobile and Online dominate across all segments — digital-first is validated. Branch usage is
    highest for HNW, indicating high-value clients expect in-person relationship banking.
    Recommendation: invest in mobile UX for mass market; maintain premium branch experience for HNW.
</div>""", unsafe_allow_html=True)

# ── Top customers ─────────────────────────────────────────────────────────────
st.markdown('### Top 15 Customers by Volume')
top = (
    df.groupby("customer_id")
    .agg(
        Segment=("customer_segment", "first"),
        volume=("amount", "sum"),
        Transactions=("transaction_id", "count"),
        Score=("customer_score", "first"),
        Income=("monthly_income", "first"),
    )
    .sort_values("volume", ascending=False)
    .head(15)
    .reset_index()
)

# fill NaN trước khi format
top["volume"] = top["volume"].fillna(0)
top["Income"] = top["Income"].fillna(0)
top["Score"] = top["Score"].fillna(0)

# format display
top["volume"] = top["volume"].apply(lambda x: f"${x:,.0f}")
top["Income"] = top["Income"].apply(lambda x: f"${x:,.0f}")
top["Score"] = top["Score"].apply(lambda x: f"{x:.0f}")

st.dataframe(
    top,
    use_container_width=True,
    hide_index=True
)