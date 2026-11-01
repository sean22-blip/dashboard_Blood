import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
CLEANED_DIR = BASE_DIR / "data" / "cleaned"


## Code outlier detection 
outlier_results = []

datasets = {
    "daily_stock": [
        "o_pos_units", "a_pos_units",
        "b_pos_units", "ab_pos_units",
        "o_neg_units", "a_neg_units",
        "b_neg_units", "ab_neg_units"
    ],
    "donations": ["volume_ml"],
    "blood_orders": ["units_requested", "units_issued"]
}

for dataset_name, columns in datasets.items():

    df = pd.read_csv(CLEANED_DIR / f"{dataset_name}_cleaned.csv")

    for column in columns:

        q1 = df[column].quantile(0.25)
        q3 = df[column].quantile(0.75)
        iqr = q3 - q1

        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        outliers = df[
            (df[column] < lower_bound) |
            (df[column] > upper_bound)
        ]

        outlier_results.append({
            "dataset": dataset_name,
            "column": column,
            "Q1": q1,
            "Q3": q3,
            "IQR": iqr,
            "lower_bound": lower_bound,
            "upper_bound": upper_bound,
            "outlier_count": len(outliers)
        })

        print(f"\n{dataset_name} - {column}")
        print(f"Outliers found: {len(outliers)}")

        if not outliers.empty:
            print(outliers[["id", column]])

results_df = pd.DataFrame(outlier_results)

REPORT_DIR = BASE_DIR / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)
results_df.to_csv(
    REPORT_DIR / "outlier_summary.csv",
    index=False
)

print("\nOutlier detection completed!")


# Inspection of outliers after detection
# 1. Are high-volume orders common?
# 2. Are high-volume orders concentrated in a particular urgency category?
# 3. Are certain blood components associated with larger orders?
# 4. Are there unusual patterns that require further investigation?
orders = pd.read_csv(CLEANED_DIR / "blood_orders_cleaned.csv")
orders["high_volume"] = orders["units_issued"] > 6

print("\n===== UNITS ISSUED BY URGENCY =====")
print(
    orders.groupby("urgency")["units_issued"]
    .agg(["count", "mean", "median", "max"])
)

print("\n===== ORDERS ABOVE 6 UNITS BY URGENCY =====")
urgency_summary = (
    orders.groupby("urgency")["high_volume"]
    .agg(high_volume_count="sum", total_orders="count")
)
urgency_summary["high_volume_pct"] = (
    urgency_summary["high_volume_count"] / urgency_summary["total_orders"] * 100
)
print(urgency_summary)

print("\n===== UNITS ISSUED BY COMPONENT =====")
component_summary = (
    orders.groupby("component")
    .agg(
        count=("units_issued", "count"),
        mean=("units_issued", "mean"),
        median=("units_issued", "median"),
        max=("units_issued", "max"),
        high_volume_count=("high_volume", "sum"),
        high_volume_pct=("high_volume", "mean"),
    )
)
component_summary["high_volume_pct"] *= 100
print(component_summary)

print("\n===== UNITS ISSUED FREQUENCY =====")
print(orders["units_issued"].value_counts().sort_index())

# Inspect high-volume orders as potential outliers using the 1.5 x IQR rule.
column = "units_issued"
q1 = orders[column].quantile(0.25)
q3 = orders[column].quantile(0.75)
iqr = q3 - q1
lower_bound = q1 - 1.5 * iqr
upper_bound = q3 + 1.5 * iqr

flagged = orders[
    (orders[column] < lower_bound) |
    (orders[column] > upper_bound)
]

print(f"\nOutliers in blood orders - {column}")
print(f"IQR bounds: {lower_bound:g} to {upper_bound:g}")
print(f"Outliers found: {len(flagged)}")

if flagged.empty:
    print("No outlier orders found.")
else:
    print(
        flagged[
            [
                "id",
                "units_requested",
                "units_issued",
                "urgency",
                "blood_type",
                "component"
            ]
        ].to_string(index=False)
    )