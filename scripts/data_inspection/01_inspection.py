
import pandas as pd
from pathlib import Path

# Project paths
BASE_DIR = Path(__file__).resolve().parents[2]
RAW_DIR = BASE_DIR / "data" / "raw"
REPORT_DIR = BASE_DIR / "reports"

REPORT_DIR.mkdir(parents=True, exist_ok=True)

# Load all six datasets
datasets = {
    "centres": pd.read_csv(RAW_DIR / "centres.csv"),
    "daily_stock": pd.read_csv(RAW_DIR / "daily_stock.csv"),
    "donors": pd.read_csv(RAW_DIR / "donors.csv"),
    "donations": pd.read_csv(RAW_DIR / "donations.csv"),
    "hospitals": pd.read_csv(RAW_DIR / "hospitals.csv"),
    "blood_orders": pd.read_csv(RAW_DIR / "blood_orders.csv")
}

# Store inspection results
summary = []

for name, df in datasets.items():

    print("\n" + "=" * 60)
    print(f"DATASET: {name.upper()}")
    print("=" * 60)

    # 1. Dataset dimensions
    print("\n1. Dataset shape:")
    print("Rows:", df.shape[0])
    print("Columns:", df.shape[1])

    # 2. Column names and data types
    print("\n2. Column names and data types:")
    print(df.dtypes)

    # 3. Missing values
    print("\n3. Missing values:")
    missing = df.isnull().sum()
    print(missing[missing > 0])

    # 4. Exact duplicate records
    duplicates = df.duplicated().sum()

    print("\n4. Exact duplicate rows:")
    print(duplicates)

    # 5. Check categorical labels
    print("\n5. Categorical values:")

    for col in df.select_dtypes(include="object").columns:
        print(f"\n{col}:")
        print(df[col].value_counts(dropna=False).head(30))

    # 6. Numeric column summary
    print("\n6. Numeric summary:")
    print(df.describe(include="number").T)

    # 7. Potential negative numeric values
    print("\n7. Negative numeric values:")

    for col in df.select_dtypes(include="number").columns:
        negative_count = (df[col] < 0).sum()

        if negative_count > 0:
            print(f"{col}: {negative_count} negative values")

    # Save summary
    summary.append({
        "dataset": name,
        "rows": len(df),
        "columns": len(df.columns),
        "missing_cells": int(df.isnull().sum().sum()),
        "duplicate_rows": int(duplicates)
    })

# Export overall inspection summary
summary_df = pd.DataFrame(summary)

summary_df.to_csv(
    REPORT_DIR / "inspection_summary.csv",
    index=False
)

print("\n" + "=" * 60)
print("INSPECTION COMPLETED")
print("=" * 60)

print(summary_df)
