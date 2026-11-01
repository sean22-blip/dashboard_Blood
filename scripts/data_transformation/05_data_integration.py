
import pandas as pd
from pathlib import Path

# Project paths
BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data" / "cleaned"
OUTPUT_DIR = BASE_DIR / "data" / "integrated"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Load cleaned datasets
centres = pd.read_csv(DATA_DIR / "centres_cleaned.csv")
donors = pd.read_csv(DATA_DIR / "donors_cleaned.csv")
hospitals = pd.read_csv(DATA_DIR / "hospitals_cleaned.csv")
daily_stock = pd.read_csv(DATA_DIR / "daily_stock_cleaned.csv")
donations = pd.read_csv(DATA_DIR / "donations_cleaned.csv")
blood_orders = pd.read_csv(DATA_DIR / "blood_orders_cleaned.csv")


# Prepare centre information
centres_info = centres.rename(columns={
    "id": "centre_id",
    "name": "centre_name",
    "town": "centre_town",
    "opened_on": "centre_opened_on"
})

# Prepare hospital information
hospitals_info = hospitals.rename(columns={
    "id": "hospital_id",
    "name": "hospital_name",
    "town": "hospital_town",
    "size_band": "hospital_size_band"
})

# Prepare donor information
donors_info = donors.rename(columns={
    "id": "donor_id",
    "blood_type": "donor_blood_type"
})


# ==================================
# 1. Integrate blood orders
# ==================================

orders_integrated = blood_orders.merge(
    hospitals_info,
    on="hospital_id",
    how="left",
    validate="many_to_one"
)

orders_integrated = orders_integrated.merge(
    centres_info,
    on="centre_id",
    how="left",
    validate="many_to_one"
)


# ==================================
# 2. Integrate donations
# ==================================

donations_integrated = donations.merge(
    donors_info,
    on="donor_id",
    how="left",
    validate="many_to_one"
)

donations_integrated = donations_integrated.merge(
    centres_info,
    on="centre_id",
    how="left",
    validate="many_to_one"
)


# ==================================
# 3. Integrate daily stock
# ==================================

stock_integrated = daily_stock.merge(
    centres_info,
    on="centre_id",
    how="left",
    validate="many_to_one"
)


# ==================================
# 4. Check integration results
# ==================================

datasets = {
    "orders_integrated": (blood_orders, orders_integrated),
    "donations_integrated": (donations, donations_integrated),
    "stock_integrated": (daily_stock, stock_integrated)
}

print("\n===== DATA INTEGRATION SUMMARY =====")

for name, (original, integrated) in datasets.items():

    print(f"\nDataset: {name}")
    print(f"Original rows: {len(original)}")
    print(f"Integrated rows: {len(integrated)}")
    print(f"Original columns: {len(original.columns)}")
    print(f"Integrated columns: {len(integrated.columns)}")

    if len(original) == len(integrated):
        print("Row count check: PASS")
    else:
        print("Row count check: FAIL")


# ==================================
# 5. Export integrated datasets
# ==================================

orders_integrated.to_csv(
    OUTPUT_DIR / "orders_integrated.csv",
    index=False
)

donations_integrated.to_csv(
    OUTPUT_DIR / "donations_integrated.csv",
    index=False
)

stock_integrated.to_csv(
    OUTPUT_DIR / "stock_integrated.csv",
    index=False
)

print("\nAll integrated datasets exported successfully!")
