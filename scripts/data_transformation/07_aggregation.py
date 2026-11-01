#Purpose 
#These files output from this script summarize your cleaned, integrated, and feature-engineered data so that your Streamlit dashboard can use them directly.
# How the output will be used in your dashboard
#  Dashboard feature	              Dataset
# Demand by blood group	            daily_blood_demand.csv
# Demand by component	            daily_component_demand.csv
# Demand by hospital	            monthly_hospital_demand.csv
# Historical demand trends	        Daily and monthly demand files
# Inventory overview	            Stock summary files
# Donation overview	                monthly_donations.csv
from pathlib import Path
import pandas as pd

# 1. Define project directories
BASE_DIR = Path(__file__).resolve().parents[2]

FEATURED_DIR = BASE_DIR / "data" / "featured"
OUTPUT_DIR = BASE_DIR / "data" / "aggregated"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 2. Load featured datasets
orders = pd.read_csv(FEATURED_DIR / "orders_featured.csv")
donations = pd.read_csv(FEATURED_DIR / "donations_featured.csv")
stock = pd.read_csv(FEATURED_DIR / "stock_featured.csv")

print("Featured datasets loaded successfully!")

# 3. Daily demand by hospital and blood type
daily_hospital_demand = (
    orders.groupby(
        ["order_date", "hospital_name", "blood_type"],
        as_index=False
    )
    .agg(
        total_orders=("id", "count"),
        units_requested=("units_requested", "sum"),
        units_issued=("units_issued", "sum"),
        unfulfilled_units=("unfulfilled_units", "sum")
    )
)

daily_hospital_demand["fulfillment_rate"] = (
    daily_hospital_demand["units_issued"]
    / daily_hospital_demand["units_requested"]
) * 100

# 4. Daily demand by blood type
daily_blood_demand = (
    orders.groupby(["order_date", "blood_type"], as_index=False)
    .agg(
        total_orders=("id", "count"),
        units_requested=("units_requested", "sum"),
        units_issued=("units_issued", "sum"),
        unfulfilled_units=("unfulfilled_units", "sum")
    )
)

daily_blood_demand["fulfillment_rate"] = (
    daily_blood_demand["units_issued"]
    / daily_blood_demand["units_requested"]
) * 100

# 5. Daily demand by component
daily_component_demand = (
    orders.groupby(["order_date", "component"], as_index=False)
    .agg(
        total_orders=("id", "count"),
        units_requested=("units_requested", "sum"),
        units_issued=("units_issued", "sum"),
        unfulfilled_units=("unfulfilled_units", "sum")
    )
)

daily_component_demand["fulfillment_rate"] = (
    daily_component_demand["units_issued"]
    / daily_component_demand["units_requested"]
) * 100

# 6. Monthly demand by blood type
monthly_blood_demand = (
    orders.groupby(["order_month", "blood_type"], as_index=False)
    .agg(
        total_orders=("id", "count"),
        units_requested=("units_requested", "sum"),
        units_issued=("units_issued", "sum"),
        unfulfilled_units=("unfulfilled_units", "sum")
    )
)

monthly_blood_demand["fulfillment_rate"] = (
    monthly_blood_demand["units_issued"]
    / monthly_blood_demand["units_requested"]
) * 100

# 7. Monthly demand by hospital
monthly_hospital_demand = (
    orders.groupby(["order_month", "hospital_name"], as_index=False)
    .agg(
        total_orders=("id", "count"),
        units_requested=("units_requested", "sum"),
        units_issued=("units_issued", "sum"),
        unfulfilled_units=("unfulfilled_units", "sum")
    )
)

monthly_hospital_demand["fulfillment_rate"] = (
    monthly_hospital_demand["units_issued"]
    / monthly_hospital_demand["units_requested"]
) * 100

# 8. Monthly demand by component
monthly_component_demand = (
    orders.groupby(["order_month", "component"], as_index=False)
    .agg(
        total_orders=("id", "count"),
        units_requested=("units_requested", "sum"),
        units_issued=("units_issued", "sum"),
        unfulfilled_units=("unfulfilled_units", "sum")
    )
)

monthly_component_demand["fulfillment_rate"] = (
    monthly_component_demand["units_issued"]
    / monthly_component_demand["units_requested"]
) * 100

# 9. Monthly donations
monthly_donations = (
    donations.groupby(
        ["collection_month", "centre_name", "blood_type", "screening_outcome"],
        as_index=False
    )
    .agg(
        total_donations=("id", "count"),
        total_volume_ml=("volume_ml", "sum")
    )
)

# 10. Daily total stock by centre
daily_stock_summary = (
    stock.groupby(["stock_date", "centre_name"], as_index=False)
    .agg(total_stock_units=("total_stock_units", "sum"))
)

# 11. Daily stock by blood type
stock_columns = {
    "o_pos_units": "O+",
    "a_pos_units": "A+",
    "b_pos_units": "B+",
    "ab_pos_units": "AB+",
    "o_neg_units": "O-",
    "a_neg_units": "A-",
    "b_neg_units": "B-",
    "ab_neg_units": "AB-"
}

daily_stock_by_blood_type = stock.melt(
    id_vars=["stock_date", "centre_name"],
    value_vars=list(stock_columns.keys()),
    var_name="blood_type_column",
    value_name="stock_units"
)

daily_stock_by_blood_type["blood_type"] = (
    daily_stock_by_blood_type["blood_type_column"]
    .map(stock_columns)
)

daily_stock_by_blood_type = daily_stock_by_blood_type.drop(
    columns=["blood_type_column"]
)

# 12. Export all aggregated datasets
aggregated_datasets = {
    "daily_hospital_demand": daily_hospital_demand,
    "daily_blood_demand": daily_blood_demand,
    "daily_component_demand": daily_component_demand,
    "monthly_blood_demand": monthly_blood_demand,
    "monthly_hospital_demand": monthly_hospital_demand,
    "monthly_component_demand": monthly_component_demand,
    "monthly_donations": monthly_donations,
    "daily_stock_summary": daily_stock_summary,
    "daily_stock_by_blood_type": daily_stock_by_blood_type
}

for name, df in aggregated_datasets.items():
    df.to_csv(OUTPUT_DIR / f"{name}.csv", index=False)
    print(f"{name}: {len(df)} rows, {len(df.columns)} columns")

print("\nAll aggregated datasets exported successfully!")
