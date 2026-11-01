import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("./data/cleaned/blood_orders_cleaned.csv")

def per_blood_group(df):
    return df.groupby("blood_type")[["units_requested", "units_issued"]].sum().reset_index()

def per_component(df):
    return df.groupby("component")[["units_requested", "units_issued"]].sum().reset_index()

def per_hospital(df):
    return df.groupby("hospital_id")[["units_requested", "units_issued"]].sum().reset_index()


def per_date(df):
    return df.groupby("ordered_at")[["units_requested", "units_issued"]].sum().reset_index()

# def summary_calculation(df):
    


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print(per_blood_group(df).to_string(index=False))
    print("\n" + "=" * 50)
    print(per_component(df).to_string(index=False))
    print("\n" + "=" * 50)
    print(per_hospital(df).to_string(index=False))
    print("\n" + "=" * 50)
    print(per_date(df).to_string(index=False))
    print("\n" + "=" * 50)