
import pandas as pd
from pathlib import Path

# Project paths
BASE_DIR = Path(__file__).resolve().parents[2]
INPUT_DIR = BASE_DIR / "data" / "integrated"
OUTPUT_DIR = BASE_DIR / "data" / "featured"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Load integrated datasets
orders = pd.read_csv(INPUT_DIR / "orders_integrated.csv")
donations = pd.read_csv(INPUT_DIR / "donations_integrated.csv")
stock = pd.read_csv(INPUT_DIR / "stock_integrated.csv")


# ==================================
# 1. Blood orders features
# ==================================

orders["ordered_at"] = pd.to_datetime(orders["ordered_at"])

orders["order_date"] = orders["ordered_at"].dt.date
orders["order_month"] = orders["ordered_at"].dt.to_period("M").astype(str)

orders["unfulfilled_units"] = (
    orders["units_requested"] - orders["units_issued"]
)

orders["fulfillment_rate"] = (
    orders["units_issued"] / orders["units_requested"]
) * 100


# ==================================
# 2. Donations features
# ==================================

donations["collected_on"] = pd.to_datetime(donations["collected_on"])

donations["collection_date"] = donations["collected_on"].dt.date
donations["collection_month"] = (
    donations["collected_on"].dt.to_period("M").astype(str)
)


# ==================================
# 3. Daily stock features
# ==================================

stock_columns = [
    "o_pos_units", "a_pos_units", "b_pos_units", "ab_pos_units",
    "o_neg_units", "a_neg_units", "b_neg_units", "ab_neg_units"
]

stock["total_stock_units"] = stock[stock_columns].sum(axis=1)


# ==================================
# 4. Display feature results
# ==================================

print("\n===== FEATURE ENGINEERING SUMMARY =====")

print("\nBlood orders:")
print(orders[
    ["order_date", "order_month", "unfulfilled_units", "fulfillment_rate"]
].head())

print("\nDonations:")
print(donations[
    ["collection_date", "collection_month"]
].head())

print("\nDaily stock:")
print(stock[
    ["centre_name", "stock_date", "total_stock_units"]
].head())


# ==================================
# 5. Export featured datasets
# ==================================

orders.to_csv(OUTPUT_DIR / "orders_featured.csv", index=False)
donations.to_csv(OUTPUT_DIR / "donations_featured.csv", index=False)
stock.to_csv(OUTPUT_DIR / "stock_featured.csv", index=False)

print("\nAll featured datasets exported successfully!")
