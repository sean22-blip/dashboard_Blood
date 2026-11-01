
from pathlib import Path
import pandas as pd

# 1. Define paths
BASE_DIR = Path(__file__).resolve().parents[2]
FEATURED_DIR = BASE_DIR / "data" / "featured"
AGGREGATED_DIR = BASE_DIR / "data" / "aggregated"

# 2. Load datasets
orders = pd.read_csv(FEATURED_DIR / "orders_featured.csv")
daily_blood = pd.read_csv(
    AGGREGATED_DIR / "daily_blood_demand.csv"
)

# 3. Calculate original totals
original_requested = orders["units_requested"].sum()
original_issued = orders["units_issued"].sum()

# 4. Calculate aggregated totals
aggregated_requested = daily_blood["units_requested"].sum()
aggregated_issued = daily_blood["units_issued"].sum()

# 5. Compare results
print("AGGREGATION ACCURACY CHECK")
print("=" * 45)

print(f"Original requested units: {original_requested}")
print(f"Aggregated requested units: {aggregated_requested}")

print(f"\nOriginal issued units: {original_issued}")
print(f"Aggregated issued units: {aggregated_issued}")

if (
    original_requested == aggregated_requested
    and original_issued == aggregated_issued
):
    print("\nSTATUS: PASSED - Aggregated totals match!")
else:
    print("\nSTATUS: FAILED - Totals do not match!")
