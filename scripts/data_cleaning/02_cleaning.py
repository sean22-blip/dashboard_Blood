
import pandas as pd
from pathlib import Path

# ==========================================
# 1. PROJECT PATHS
# ==========================================

BASE_DIR = Path(__file__).resolve().parents[2]

RAW_DIR = BASE_DIR / "data" / "raw"
CLEAN_DIR = BASE_DIR / "data" / "cleaned"
REPORT_DIR = BASE_DIR / "reports"

CLEAN_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)


# ==========================================
# 2. LOAD RAW DATASETS
# ==========================================

datasets = {
    "centres": pd.read_csv(RAW_DIR / "centres.csv"),
    "daily_stock": pd.read_csv(RAW_DIR / "daily_stock.csv"),
    "donors": pd.read_csv(RAW_DIR / "donors.csv"),
    "donations": pd.read_csv(RAW_DIR / "donations.csv"),
    "hospitals": pd.read_csv(RAW_DIR / "hospitals.csv"),
    "blood_orders": pd.read_csv(RAW_DIR / "blood_orders.csv")
}

# Preserve original totals for comparison
original_totals = {
    name: {
        "rows": len(df),
        "requested": (
            df["units_requested"].sum()
            if "units_requested" in df.columns else None
        ),
        "issued": (
            df["units_issued"].sum()
            if "units_issued" in df.columns else None
        )
    }
    for name, df in datasets.items()
}


# ==========================================
# 3. HELPER FUNCTIONS
# ==========================================

issues = []
cleaning_summary = []


def add_issue(dataset, row, column, issue, value):
    issues.append({
        "dataset": dataset,
        "row": row,
        "column": column,
        "issue": issue,
        "original_value": str(value)
    })


def clean_text(series):
    """Remove leading/trailing and repeated spaces."""
    return (
        series.astype("string")
        .str.strip()
        .str.replace(r"\s+", " ", regex=True)
    )


def clean_date(df, column, dataset, date_only=True):
    """Convert date strings and report invalid dates."""

    original = df[column].copy()

    converted = pd.to_datetime(
        original,
        errors="coerce"
    )

    invalid = converted.isna() & original.notna()

    for index in df.index[invalid]:
        add_issue(
            dataset,
            index,
            column,
            "Invalid date",
            original.loc[index]
        )

    df[column] = converted

    return df


def clean_blood_type(series):
    """Standardize the eight ABO/Rh blood groups."""

    return clean_text(series).str.upper()


# ==========================================
# 4. CLEAN EACH DATASET
# ==========================================

cleaned = {}

for name, original_df in datasets.items():

    df = original_df.copy()

    print(f"Cleaning {name}...")

    # Remove unnecessary spaces from text columns
    for col in df.select_dtypes(include=["str", "object"]).columns:
        df[col] = clean_text(df[col])

    # --------------------------------------
    # CENTRES
    # --------------------------------------

    if name == "centres":

        df = clean_date(df, "opened_on", name)

    # --------------------------------------
    # DAILY STOCK
    # --------------------------------------

    elif name == "daily_stock":

        df = clean_date(df, "stock_date", name)

        stock_columns = [
            "o_pos_units",
            "a_pos_units",
            "b_pos_units",
            "ab_pos_units",
            "o_neg_units",
            "a_neg_units",
            "b_neg_units",
            "ab_neg_units"
        ]

        for col in stock_columns:
            df[col] = pd.to_numeric(
                df[col], errors="coerce"
            )

            invalid = df[col].isna() | (df[col] < 0)

            for index in df.index[invalid]:
                add_issue(
                    name, index, col,
                    "Missing or negative stock quantity",
                    df.loc[index, col]
                )

    # --------------------------------------
    # DONORS
    # --------------------------------------

    elif name == "donors":

        df = clean_date(df, "registered_on", name)

        df["blood_type"] = clean_blood_type(
            df["blood_type"]
        )

        df["sex"] = df["sex"].str.lower().map({
            "female": "Female",
            "male": "Male"
        }).fillna(df["sex"])

        valid_blood_groups = {
            "A+", "A-", "B+", "B-",
            "AB+", "AB-", "O+", "O-"
        }

        invalid = ~df["blood_type"].isin(valid_blood_groups)

        for index in df.index[invalid]:
            add_issue(
                name, index, "blood_type",
                "Unrecognized blood group",
                df.loc[index, "blood_type"]
            )

    # --------------------------------------
    # DONATIONS
    # --------------------------------------

    elif name == "donations":

        df = clean_date(df, "collected_on", name)

        df["blood_type"] = clean_blood_type(
            df["blood_type"]
        )

        df["screening_outcome"] = (
            df["screening_outcome"].str.lower()
        )

        df["volume_ml"] = pd.to_numeric(
            df["volume_ml"], errors="coerce"
        )

        invalid = df["volume_ml"].isna() | (
            df["volume_ml"] <= 0
        )

        for index in df.index[invalid]:
            add_issue(
                name, index, "volume_ml",
                "Missing or non-positive donation volume",
                df.loc[index, "volume_ml"]
            )

        valid_outcomes = {
            "released", "discarded", "quarantined"
        }

        invalid = ~df["screening_outcome"].isin(
            valid_outcomes
        )

        for index in df.index[invalid]:
            add_issue(
                name, index, "screening_outcome",
                "Unrecognized screening outcome",
                df.loc[index, "screening_outcome"]
            )

    # --------------------------------------
    # HOSPITALS
    # --------------------------------------

    elif name == "hospitals":

        df["size_band"] = df["size_band"].str.lower().map({
            "small": "Small",
            "medium": "Medium",
            "large": "Large"
        }).fillna(df["size_band"])

        # Names and towns are trimmed,
        # but their original capitalization is preserved.

    # --------------------------------------
    # BLOOD ORDERS
    # --------------------------------------

    elif name == "blood_orders":

        df = clean_date(df, "ordered_at", name)

        df["blood_type"] = clean_blood_type(
            df["blood_type"]
        )

        # Standardize component labels
        df["component"] = df["component"].str.lower().map({
            "red cells": "Red Cells",
            "plasma": "Plasma",
            "platelets": "Platelets"
        }).fillna(df["component"])

        df["urgency"] = df["urgency"].str.lower().map({
            "routine": "Routine",
            "urgent": "Urgent",
            "emergency": "Emergency"
        }).fillna(df["urgency"])

        valid_blood_groups = {
            "A+", "A-", "B+", "B-",
            "AB+", "AB-", "O+", "O-"
        }

        invalid = ~df["blood_type"].isin(valid_blood_groups)

        for index in df.index[invalid]:
            add_issue(
                name, index, "blood_type",
                "Unrecognized blood group",
                df.loc[index, "blood_type"]
            )

        for col in ["units_requested", "units_issued"]:

            df[col] = pd.to_numeric(
                df[col], errors="coerce"
            )

            invalid = (
                df[col].isna() |
                (df[col] < 0) |
                (df[col] % 1 != 0)
            )

            for index in df.index[invalid]:
                add_issue(
                    name, index, col,
                    "Missing, negative or non-integer quantity",
                    df.loc[index, col]
                )

        # Requested quantity should be positive
        invalid = df["units_requested"] <= 0

        for index in df.index[invalid]:
            add_issue(
                name, index, "units_requested",
                "Requested quantity must be positive",
                df.loc[index, "units_requested"]
            )

        # Investigate issued units exceeding requested units
        invalid = (
            df["units_issued"] > df["units_requested"]
        )

        for index in df.index[invalid]:
            add_issue(
                name, index, "units_issued",
                "Issued units exceed requested units",
                df.loc[index, "units_issued"]
            )

       
    # Check allowed categorical values

    allowed_categories = {
        "donors": {
            "sex": {"Female", "Male"},
            "blood_type": {
                "A+", "A-", "B+", "B-",
                "AB+", "AB-", "O+", "O-"
            }
        },

        "donations": {
            "screening_outcome": {
                "released", "discarded", "quarantined"
            },
            "blood_type": {
                "A+", "A-", "B+", "B-",
                "AB+", "AB-", "O+", "O-"
            }
        },

        "hospitals": {
            "size_band": {"Small", "Medium", "Large"}
        },

        "blood_orders": {
            "component": {"Red Cells", "Plasma", "Platelets"},
            "urgency": {"Routine", "Urgent", "Emergency"},
            "blood_type": {
                "A+", "A-", "B+", "B-",
                "AB+", "AB-", "O+", "O-"
            }
        }
    }

    for column, allowed_values in allowed_categories.get(name, {}).items():

        invalid = ~df[column].isin(allowed_values)

        for index in df.index[invalid]:
            add_issue(
                name,
                index,
                column,
                "Unexpected categorical value",
                df.loc[index, column]
            )

    # ======================================
    # 5. SAVE CLEANED DATASET
    # ======================================

    cleaned[name] = df

    df.to_csv(
        CLEAN_DIR / f"{name}_cleaned.csv",
        index=False,
        date_format="%Y-%m-%d"
    )

    cleaning_summary.append({
        "dataset": name,
        "original_rows": len(original_df),
        "cleaned_rows": len(df),
        "columns": len(df.columns)
    })


# ==========================================
# 6. CHECK PRIMARY KEY DUPLICATES
# ==========================================

for name, df in cleaned.items():

    if "id" in df.columns:

        duplicates = df["id"].duplicated(keep=False)

        for index in df.index[duplicates]:
            add_issue(
                name, index, "id",
                "Duplicate primary key",
                df.loc[index, "id"]
            )


# ==========================================
# 7. CHECK FOREIGN KEY RELATIONSHIPS
# ==========================================

relationships = [
    ("daily_stock", "centre_id", "centres", "id"),
    ("donations", "donor_id", "donors", "id"),
    ("donations", "centre_id", "centres", "id"),
    ("blood_orders", "hospital_id", "hospitals", "id"),
    ("blood_orders", "centre_id", "centres", "id")
]

for child, child_col, parent, parent_col in relationships:

    valid_ids = set(cleaned[parent][parent_col])

    invalid = ~cleaned[child][child_col].isin(valid_ids)

    for index in cleaned[child].index[invalid]:
        add_issue(
            child, index, child_col,
            f"No matching ID in {parent}",
            cleaned[child].loc[index, child_col]
        )


# ==========================================
# 8. SAVE REPORTS
# ==========================================

pd.DataFrame(cleaning_summary).to_csv(
    REPORT_DIR / "cleaning_summary.csv",
    index=False
)

issues_df = pd.DataFrame(
    issues,
    columns=[
        "dataset", "row", "column",
        "issue", "original_value"
    ]
)

issues_df.to_csv(
    REPORT_DIR / "cleaning_issues.csv",
    index=False
)

print("\nCLEANING COMPLETED")
print(pd.DataFrame(cleaning_summary))

print("\nTotal issues found:", len(issues_df))
print("\nIssue breakdown:")

if not issues_df.empty:
    print(issues_df.groupby(
        ["dataset", "issue"]
    ).size())
else:
    print("No issues found.")
