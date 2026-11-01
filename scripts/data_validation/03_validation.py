# Goal of this validation 

# Goal 1 : Relationship validation: Do the IDs in one dataset correctly refer to records in another dataset?

import pandas as pd
from pathlib import Path

# Locate cleaned data folder
BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data" / "cleaned"
REPORT_DIR = BASE_DIR / "reports"

REPORT_DIR.mkdir(parents=True, exist_ok=True)

# Load cleaned datasets
centres = pd.read_csv(DATA_DIR / "centres_cleaned.csv")
donors = pd.read_csv(DATA_DIR / "donors_cleaned.csv")
hospitals = pd.read_csv(DATA_DIR / "hospitals_cleaned.csv")
daily_stock = pd.read_csv(DATA_DIR / "daily_stock_cleaned.csv")
donations = pd.read_csv(DATA_DIR / "donations_cleaned.csv")
blood_orders = pd.read_csv(DATA_DIR / "blood_orders_cleaned.csv")

# Define relationships to validate
relationships = [
    ("daily_stock", daily_stock, "centre_id", "centres", centres, "id"),
    ("donations", donations, "donor_id", "donors", donors, "id"),
    ("donations", donations, "centre_id", "centres", centres, "id"),
    ("blood_orders", blood_orders, "hospital_id", "hospitals", hospitals, "id"),
    ("blood_orders", blood_orders, "centre_id", "centres", centres, "id"),
]

results = []

for child_name, child_df, fk, parent_name, parent_df, pk in relationships:

    # Find IDs that do not exist in the referenced dataset
    invalid_records = child_df[~child_df[fk].isin(parent_df[pk])]

    results.append({
        "dataset": child_name,
        "foreign_key": fk,
        "referenced_dataset": parent_name,
        "total_records": len(child_df),
        "invalid_references": len(invalid_records),
        "validation_status": (
            "PASS" if len(invalid_records) == 0 else "FAIL"
        )
    })

    print(f"\n{child_name}: {fk} -> {pk}")
    print(f"Invalid references: {len(invalid_records)}")

    if not invalid_records.empty:
        print(invalid_records)

# Save validation report
results_df = pd.DataFrame(results)
results_df.to_csv(
    REPORT_DIR / "relationship_validation.csv",
    index=False
)

print("\n===== RELATIONSHIP VALIDATION SUMMARY =====")
print(results_df.to_string(index=False))

print("\nReport saved to reports/relationship_validation.csv")

# Goal 2 : Date validation: Do the dates make sense and follow the correct chronological order?

# We'll check:
# 1. Whether date values can be converted into valid dates.
# 2. Whether the dates fall within the expected sequence.
# 3. Whether activities happened after the relevant centre or donor was registered/opened.
# Convert date columns
date_columns = {
    "centres": (centres, ["opened_on"]),
    "donors": (donors, ["registered_on"]),
    "daily_stock": (daily_stock, ["stock_date"]),
    "donations": (donations, ["collected_on"]),
    "blood_orders": (blood_orders, ["ordered_at"])
}

summary = []
issues = []

# 1. Check date validity and ranges
for dataset_name, (df, columns) in date_columns.items():

    for column in columns:
        original = df[column]
        converted = pd.to_datetime(original, errors="coerce")

        invalid = converted.isna()

        summary.append({
            "dataset": dataset_name,
            "column": column,
            "total_records": len(df),
            "invalid_dates": int(invalid.sum()),
            "earliest_date": converted.min(),
            "latest_date": converted.max(),
            "status": "PASS" if not invalid.any() else "FAIL"
        })

        if invalid.any():
            for index in df.index[invalid]:
                issues.append({
                    "dataset": dataset_name,
                    "column": column,
                    "row_index": index,
                    "value": original.loc[index],
                    "issue": "Invalid or missing date"
                })

# 2. Check donation date against donor registration date
donation_check = donations.merge(
    donors[["id", "registered_on"]],
    left_on="donor_id",
    right_on="id",
    suffixes=("", "_donor")
)

donation_check["collected_on"] = pd.to_datetime(
    donation_check["collected_on"], errors="coerce"
)
donation_check["registered_on"] = pd.to_datetime(
    donation_check["registered_on"], errors="coerce"
)

invalid_donations = donation_check[
    donation_check["collected_on"] < donation_check["registered_on"]
]

for _, row in invalid_donations.iterrows():
    issues.append({
        "dataset": "donations",
        "column": "collected_on",
        "row_index": row.name,
        "value": row["collected_on"],
        "issue": "Donation occurred before donor registration"
    })

# 3. Check activities against centre opening dates
activity_checks = [
    ("daily_stock", daily_stock, "stock_date"),
    ("donations", donations, "collected_on"),
    ("blood_orders", blood_orders, "ordered_at")
]

for dataset_name, df, date_column in activity_checks:

    check = df.merge(
        centres[["id", "opened_on"]],
        left_on="centre_id",
        right_on="id",
        suffixes=("", "_centre")
    )

    check[date_column] = pd.to_datetime(
        check[date_column], errors="coerce"
    )
    check["opened_on"] = pd.to_datetime(
        check["opened_on"], errors="coerce"
    )

    invalid = check[check[date_column] < check["opened_on"]]

    for _, row in invalid.iterrows():
        issues.append({
            "dataset": dataset_name,
            "column": date_column,
            "row_index": row.name,
            "value": row[date_column],
            "issue": "Activity occurred before centre opening"
        })

# Save reports
summary_df = pd.DataFrame(summary)
issues_df = pd.DataFrame(issues)

summary_df.to_csv(
    REPORT_DIR / "date_validation_summary.csv",
    index=False
)

issues_df.to_csv(
    REPORT_DIR / "date_validation_issues.csv",
    index=False
)

print("\n===== DATE VALIDATION SUMMARY =====")
print(summary_df.to_string(index=False))

print("\n===== DATE VALIDATION ISSUES =====")

if issues_df.empty:
    print("No date validation issues found.")
else:
    print(issues_df.to_string(index=False))

print("\nReports saved in the reports folder.")

# Goal 3 : Business-rule validation: Do the records follow rules such as issued units not exceeding requested units?
# This checks whether the data makes sense according to the expected operations of a blood bank.


# Store validation issues
issues = []

def record_issues(df, dataset, condition, column, message):
    invalid = df[condition]

    for index, row in invalid.iterrows():
        issues.append({
            "dataset": dataset,
            "row_index": index,
            "column": column,
            "value": row[column],
            "issue": message
        })


# 1. Issued units must not exceed requested units
record_issues(
    blood_orders,
    "blood_orders",
    blood_orders["units_issued"] > blood_orders["units_requested"],
    "units_issued",
    "Issued units exceed requested units"
)

# 2. Requested units must be greater than zero
record_issues(
    blood_orders,
    "blood_orders",
    blood_orders["units_requested"] <= 0,
    "units_requested",
    "Requested units must be greater than zero"
)

# 3. Issued units cannot be negative
record_issues(
    blood_orders,
    "blood_orders",
    blood_orders["units_issued"] < 0,
    "units_issued",
    "Issued units cannot be negative"
)

# 4. Donation volume must be positive
record_issues(
    donations,
    "donations",
    donations["volume_ml"] <= 0,
    "volume_ml",
    "Donation volume must be greater than zero"
)

# 5. Screening outcome must be valid
valid_outcomes = ["released", "discarded", "quarantined"]

record_issues(
    donations,
    "donations",
    ~donations["screening_outcome"].str.lower().isin(valid_outcomes),
    "screening_outcome",
    "Unrecognized screening outcome"
)

# 6. Stock quantities cannot be negative
stock_columns = [
    "o_pos_units", "a_pos_units", "b_pos_units", "ab_pos_units",
    "o_neg_units", "a_neg_units", "b_neg_units", "ab_neg_units"
]

for column in stock_columns:
    record_issues(
        daily_stock,
        "daily_stock",
        daily_stock[column] < 0,
        column,
        "Stock quantity cannot be negative"
    )

# 7. Donation blood type must match donor record
donation_check = donations.merge(
    donors[["id", "blood_type"]],
    left_on="donor_id",
    right_on="id",
    suffixes=("_donation", "_donor")
)

mismatch = (
    donation_check["blood_type_donation"].str.upper()
    != donation_check["blood_type_donor"].str.upper()
)

for index, row in donation_check[mismatch].iterrows():
    issues.append({
        "dataset": "donations",
        "row_index": index,
        "column": "blood_type",
        "value": row["blood_type_donation"],
        "issue": "Donation blood type does not match donor record"
    })


# Save validation report
issues_df = pd.DataFrame(issues)

issues_df.to_csv(
    REPORT_DIR / "business_validation_issues.csv",
    index=False
)

print("\n===== BUSINESS RULE VALIDATION =====")

if issues_df.empty:
    print("All business rules passed. No issues found.")
else:
    print(issues_df.to_string(index=False))

print(f"\nTotal issues found: {len(issues_df)}")
print("Report saved to reports/business_validation_issues.csv")
