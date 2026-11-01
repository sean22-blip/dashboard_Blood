
from pathlib import Path
import pandas as pd

# 1. Define project directory
BASE_DIR = Path(__file__).resolve().parents[2]
AGGREGATED_DIR = BASE_DIR / "data" / "aggregated"

# 2. List expected aggregated datasets
expected_files = [
    "daily_hospital_demand.csv",
    "daily_blood_demand.csv",
    "daily_component_demand.csv",
    "monthly_blood_demand.csv",
    "monthly_hospital_demand.csv",
    "monthly_component_demand.csv",
    "monthly_donations.csv",
    "daily_stock_summary.csv",
    "daily_stock_by_blood_type.csv"
]

print("FINAL DATASET VALIDATION")
print("=" * 50)

# 3. Check each dataset
for filename in expected_files:

    file_path = AGGREGATED_DIR / filename

    print(f"\nDataset: {filename}")

    if not file_path.exists():
        print("STATUS: FAILED - File not found")
        continue

    df = pd.read_csv(file_path)

    missing_values = df.isnull().sum().sum()
    duplicate_rows = df.duplicated().sum()

    print(f"Rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")
    print(f"Missing values: {missing_values}")
    print(f"Duplicate rows: {duplicate_rows}")

    if missing_values == 0 and duplicate_rows == 0:
        print("STATUS: PASSED")
    else:
        print("STATUS: NEEDS REVIEW")

print("\nValidation completed!")
