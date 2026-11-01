import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Blood Demand Dashboard", page_icon="🩸", layout="wide")


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
@st.cache_data
def load_raw():
    return {
        "Centres": pd.read_csv("data/raw/centres.csv"),
        "Daily Stock": pd.read_csv("data/raw/daily_stock.csv"),
        "Donors": pd.read_csv("data/raw/donors.csv"),
        "Donations": pd.read_csv("data/raw/donations.csv"),
        "Hospitals": pd.read_csv("data/raw/hospitals.csv"),
        "Blood Orders": pd.read_csv("data/raw/blood_orders.csv"),
    }


@st.cache_data
def load_cleaned():
    orders = pd.read_csv("data/cleaned/blood_orders_cleaned.csv", parse_dates=["ordered_at"])
    hospitals = pd.read_csv("data/cleaned/hospitals_cleaned.csv")
    orders = orders.merge(
        hospitals[["id", "name"]].rename(columns={"id": "hospital_id", "name": "hospital"}),
        on="hospital_id",
        how="left",
    )
    return orders


raw = load_raw()
orders = load_cleaned()

UNITS = ["units_requested", "units_issued"]
LABELS = {"units_requested": "Requested", "units_issued": "Issued", "value": "Units"}


def grouped(df, by):
    """Sum requested/issued units by a column and return it in long format for plotting."""
    g = df.groupby(by)[UNITS].sum().reset_index()
    return g, g.melt(id_vars=by, var_name="metric", value_name="units").assign(
        metric=lambda d: d["metric"].map(LABELS)
    )


# ---------------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------------
st.sidebar.header("Filters")

min_d, max_d = orders["ordered_at"].min().date(), orders["ordered_at"].max().date()
date_range = st.sidebar.date_input("Order date", (min_d, max_d), min_value=min_d, max_value=max_d)
blood_sel = st.sidebar.multiselect("Blood group", sorted(orders["blood_type"].unique()))
comp_sel = st.sidebar.multiselect("Component", sorted(orders["component"].unique()))
urg_sel = st.sidebar.multiselect("Urgency", sorted(orders["urgency"].unique()))
hosp_sel = st.sidebar.multiselect("Hospital", sorted(orders["hospital"].dropna().unique()))
st.sidebar.caption("Leave a filter empty to include everything.")

df = orders.copy()
if isinstance(date_range, tuple) and len(date_range) == 2:
    df = df[(df["ordered_at"].dt.date >= date_range[0]) & (df["ordered_at"].dt.date <= date_range[1])]
if blood_sel:
    df = df[df["blood_type"].isin(blood_sel)]
if comp_sel:
    df = df[df["component"].isin(comp_sel)]
if urg_sel:
    df = df[df["urgency"].isin(urg_sel)]
if hosp_sel:
    df = df[df["hospital"].isin(hosp_sel)]

# ---------------------------------------------------------------------------
# Header + KPIs
# ---------------------------------------------------------------------------
st.title("🩸 Blood Demand Forecasting Dashboard")
st.caption("Requested vs issued blood units across hospitals, blood groups and components.")

if df.empty:
    st.warning("No orders match the current filters.")
    st.stop()

requested = int(df["units_requested"].sum())
issued = int(df["units_issued"].sum())
fill_rate = issued / requested if requested else 0

k1, k2, k3, k4 = st.columns(4)
k1.metric("Orders", f"{len(df):,}")
k2.metric("Units requested", f"{requested:,}")
k3.metric("Units issued", f"{issued:,}")
k4.metric("Fulfilment rate", f"{fill_rate:.1%}", delta=f"-{requested - issued:,} unit shortfall", delta_color="inverse")

st.divider()

tab_blood, tab_comp, tab_hosp, tab_date, tab_summary, tab_data = st.tabs(
    ["Blood group", "Component", "Hospital", "Date", "Summary", "Dataset overview"]
)

# ---------------------------------------------------------------------------
# Blood group
# ---------------------------------------------------------------------------
with tab_blood:
    g, long = grouped(df, "blood_type")
    fig = px.bar(
        long, x="blood_type", y="units", color="metric", barmode="group",
        title="Demand by blood group", labels={"blood_type": "Blood group", "units": "Units", "metric": ""},
    )
    st.plotly_chart(fig, width="stretch")

# ---------------------------------------------------------------------------
# Component
# ---------------------------------------------------------------------------
with tab_comp:
    g, long = grouped(df, "component")
    c1, c2 = st.columns([2, 1])
    with c1:
        fig = px.bar(
            long, x="component", y="units", color="metric", barmode="group",
            title="Demand by component", labels={"component": "Component", "units": "Units", "metric": ""},
        )
        st.plotly_chart(fig, width="stretch")
    with c2:
        fig = px.pie(g, names="component", values="units_requested", hole=0.45, title="Share of requested units")
        st.plotly_chart(fig, width="stretch")

# ---------------------------------------------------------------------------
# Hospital
# ---------------------------------------------------------------------------
with tab_hosp:
    g, long = grouped(df, "hospital")
    order = g.sort_values("units_requested")["hospital"].tolist()
    fig = px.bar(
        long, y="hospital", x="units", color="metric", barmode="group", orientation="h",
        title="Hospital demand", labels={"hospital": "Hospital", "units": "Units", "metric": ""},
        category_orders={"hospital": order},
    )
    fig.update_layout(height=max(400, 60 * len(order)))
    st.plotly_chart(fig, width="stretch")

# ---------------------------------------------------------------------------
# Date
# ---------------------------------------------------------------------------
with tab_date:
    daily = df.groupby("ordered_at")[UNITS].sum().reset_index()
    daily_long = daily.melt(id_vars="ordered_at", var_name="metric", value_name="units").assign(
        metric=lambda d: d["metric"].map(LABELS)
    )

    fig = px.line(
        daily_long, x="ordered_at", y="units", color="metric", markers=True,
        title="Daily units requested vs issued", labels={"ordered_at": "Order date", "units": "Units", "metric": ""},
    )
    st.plotly_chart(fig, width="stretch")

    fig = px.box(
        daily_long, x="metric", y="units", color="metric", points="outliers",
        title="Requested vs issued (distribution of daily totals)",
        labels={"metric": "", "units": "Units"},
    )
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, width="stretch")

# ---------------------------------------------------------------------------
# Summary (computed from the filtered data, so it stays correct as filters change)
# ---------------------------------------------------------------------------
with tab_summary:
    bt = df.groupby("blood_type")["units_requested"].sum().sort_values(ascending=False)
    cp = df.groupby("component")["units_requested"].sum().sort_values(ascending=False)
    hp = df.groupby("hospital")[UNITS].sum().sort_values("units_requested", ascending=False)
    daily = df.groupby("ordered_at")[UNITS].sum()

    st.subheader("Blood group")
    st.markdown(
        f"- **Most requested:** {', '.join(bt.index[:2])} ({bt.iloc[0]:,} and {bt.iloc[1]:,} units)\n"
        f"- **Least requested:** {', '.join(bt.index[-3:][::-1])}\n"
        f"- **Supply gap:** {requested - issued:,} units requested but not issued "
        f"(fulfilment {fill_rate:.1%})"
        if len(bt) >= 2 else "Not enough blood groups in the current selection."
    )

    st.subheader("Component")
    st.markdown(
        "\n".join(f"- **{name}:** {int(v):,} units requested" for name, v in cp.items())
        + f"\n- **{cp.index[0]}** accounts for {cp.iloc[0] / cp.sum():.0%} of all requested units"
    )

    st.subheader("Hospital")
    top = hp.iloc[0]
    st.markdown(
        f"- **Top requester:** {hp.index[0]} ({int(top['units_requested']):,} requested, "
        f"{int(top['units_issued']):,} issued)\n"
        f"- **Hospitals issued less than requested:** "
        f"{int((hp['units_issued'] < hp['units_requested']).sum())} of {len(hp)}"
    )

    st.subheader("Date")
    st.markdown(
        f"- **Median daily requested:** {daily['units_requested'].median():.0f} units\n"
        f"- **Median daily issued:** {daily['units_issued'].median():.0f} units\n"
        f"- **Days with a shortfall:** {int((daily['units_issued'] < daily['units_requested']).sum())} "
        f"of {len(daily)}"
    )

# ---------------------------------------------------------------------------
# Dataset overview (from the original app.py)
# ---------------------------------------------------------------------------
with tab_data:
    st.subheader("Dataset overview")
    st.dataframe(
        pd.DataFrame(
            {"Dataset": list(raw), "Rows": [d.shape[0] for d in raw.values()], "Columns": [d.shape[1] for d in raw.values()]}
        ),
        hide_index=True,
        width="stretch",
    )

    for name, data in raw.items():
        with st.expander(name):
            st.write("Columns and data types:")
            st.dataframe(
                data.dtypes.astype(str).rename("dtype").reset_index().rename(columns={"index": "column"}),
                hide_index=True,
            )
            st.write("First 5 records:")
            st.dataframe(data.head(), width="stretch")