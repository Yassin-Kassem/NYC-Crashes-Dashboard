"""
NYC Motor Vehicle Collisions Dashboard
Data Loading & Preprocessing
"""

import pandas as pd
import numpy as np
from datetime import datetime

# =============================================================================
# LOAD AND PREPARE DATA
# =============================================================================

print("Loading datasets...")
print("This may take a moment with large datasets...")

# Load crash data
df_crash = pd.read_csv("data/cleaned_collisions_crash_level.csv", low_memory=False)

# Load person data with optimized dtypes
df_person = pd.read_csv(
    "data/cleaned_collisions_person_level.csv",
    low_memory=False,
    usecols=[
        "COLLISION_ID",
        "CRASH DATE",
        "CRASH TIME",
        "BOROUGH",
        "PERSON_TYPE",
        "PERSON_AGE",
        "PERSON_SEX",
        "PERSON_INJURY",
    ],
)

print(f"Loaded {len(df_crash):,} crashes and {len(df_person):,} person records")

# Convert dates
df_crash["CRASH DATE"] = pd.to_datetime(df_crash["CRASH DATE"], errors="coerce")
df_person["CRASH DATE"] = pd.to_datetime(df_person["CRASH DATE"], errors="coerce")

# Time features
df_crash["YEAR"] = df_crash["CRASH DATE"].dt.year
df_crash["MONTH"] = df_crash["CRASH DATE"].dt.month
df_crash["HOUR"] = pd.to_datetime(
    df_crash["CRASH TIME"], format="%H:%M:%S", errors="coerce"
).dt.hour

# Filter to 2015–2025
df_crash = df_crash[df_crash["YEAR"].between(2015, 2025)].reset_index(drop=True)
df_person = df_person[
    df_person["CRASH DATE"].dt.year.between(2015, 2025)
].reset_index(drop=True)

# Seasons
df_crash["SEASON"] = df_crash["MONTH"].map(
    {
        12: "Winter", 1: "Winter", 2: "Winter",
        3: "Spring", 4: "Spring", 5: "Spring",
        6: "Summer", 7: "Summer", 8: "Summer",
        9: "Fall", 10: "Fall", 11: "Fall",
    }
)

# Options
boroughs = sorted(df_crash["BOROUGH"].dropna().unique().tolist())
years = sorted(df_crash["YEAR"].dropna().unique().tolist())
vehicle_cols = [c for c in df_crash.columns if "VEHICLE TYPE CODE" in c.upper()]
vehicle_types = sorted(
    df_crash[vehicle_cols[0]].dropna().value_counts().head(30).index.tolist()
) if vehicle_cols else []

person_types = (
    sorted(df_person["PERSON_TYPE"].dropna().unique().tolist())
    if "PERSON_TYPE" in df_person.columns
    else []
)

print("Data preparation complete.")
