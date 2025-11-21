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
"""
NYC Motor Vehicle Collisions Dashboard
Commit 2 — App Initialization & Layout
"""

import dash
from dash import dcc, html

# Reuse data & variables from Commit 1

# =============================================================================
# INITIALIZE APP
# =============================================================================

app = dash.Dash(
    _name_,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)
server = app.server
app.title = "NYC Motor Vehicle Collisions Dashboard"

# =============================================================================
# LAYOUT
# =============================================================================

app.layout = html.Div(
    className="app-shell",
    children=[
        html.Div(
            className="app-header",
            children=[
                html.Div(
                    className="app-title",
                    children="🚗 NYC Motor Vehicle Collisions Dashboard",
                ),
                html.Div(
                    className="app-header-meta",
                    children=f"{len(df_crash):,} crashes · {len(df_person):,} people records",
                ),
            ],
        ),

        html.Div(
            className="main-layout",
            children=[
                # Sidebar
                html.Div(
                    className="sidebar",
                    children=[
                        html.Div(
                            className="card",
                            children=[
                                html.H3("Filters"),
                                html.Label("Borough"),
                                dcc.Dropdown(
                                    id="borough-filter",
                                    options=[{"label": "All", "value": "ALL"}]
                                    + [{"label": b, "value": b} for b in boroughs],
                                    value="ALL",
                                    multi=True,
                                ),
                                html.Label("Year"),
                                dcc.Dropdown(
                                    id="year-filter",
                                    options=[{"label": "All", "value": "ALL"}]
                                    + [{"label": str(y), "value": y} for y in years],
                                    value="ALL",
                                    multi=True,
                                ),
                                html.Label("Vehicle Type"),
                                dcc.Dropdown(
                                    id="vehicle-filter",
                                    options=[{"label": "All", "value": "ALL"}]
                                    + [{"label": v, "value": v} for v in vehicle_types],
                                    value="ALL",
                                    multi=True,
                                ),
                                html.Label("Person Type"),
                                dcc.Dropdown(
                                    id="person-filter",
                                    options=[{"label": "All", "value": "ALL"}]
                                    + [{"label": p, "value": p} for p in person_types],
                                    value="ALL",
                                    multi=True,
                                ),
                                html.Label("Search"),
                                dcc.Input(id="search-input", type="text"),
                                html.Button("Clear", id="clear-search-btn"),
                            ],
                        ),
                        html.Button("📊 Generate Report", id="generate-report-btn"),
                    ],
                ),

                # Content Area
                html.Div(
                    className="content-area",
                    children=[
                        html.Div(id="summary-stats"),
                        dcc.Graph(id="temporal-chart"),
                        dcc.Graph(id="borough-chart"),
                        dcc.Graph(id="hour-chart"),
                        dcc.Graph(id="victim-chart"),
                        dcc.Graph(id="factors-chart"),
                        dcc.Graph(id="vehicle-chart"),
                        dcc.Graph(id="map-chart"),
                        dcc.Graph(id="seasonal-chart"),
                        dcc.Graph(id="heatmap-chart"),
                        dcc.Graph(id="age-chart"),
                    ],
                ),
            ],
        ),

        html.Div("NYC Motor Vehicle Collisions Dashboard · GIU 2025", className="footer-text"),
    ],
)

"""
NYC Dashboard Helper Functions
Commit 3 — Filtering + Search Parser
"""

# =============================================================================
# FILTERING FUNCTIONS
# =============================================================================

def filter_data(df, boroughs_sel, years_sel, vehicles_sel):
    filtered = df.copy()

    if boroughs_sel and "ALL" not in boroughs_sel:
        filtered = filtered[filtered["BOROUGH"].isin(boroughs_sel)]

    if years_sel and "ALL" not in years_sel:
        filtered = filtered[filtered["YEAR"].isin(years_sel)]

    if vehicles_sel and "ALL" not in vehicles_sel and vehicle_cols:
        mask = filtered[vehicle_cols[0]].isin(vehicles_sel)
        for col in vehicle_cols[1:]:
            mask |= filtered[col].isin(vehicles_sel)
        filtered = filtered[mask]

    return filtered


def filter_person_data(df, boroughs_sel, years_sel, persons_sel):
    filtered = df.copy()

    if boroughs_sel and "ALL" not in boroughs_sel:
        filtered = filtered[filtered["BOROUGH"].isin(boroughs_sel)]

    if years_sel and "ALL" not in years_sel:
        filtered = filtered[df["CRASH DATE"].dt.year.isin(years_sel)]

    if persons_sel and "ALL" not in persons_sel:
        filtered = filtered[filtered["PERSON_TYPE"].isin(persons_sel)]

    return filtered


# =============================================================================
# NATURAL LANGUAGE SEARCH
# =============================================================================

def parse_search_query(query):
    if not query:
        return None, None, None

    query = query.lower()

    borough = next((b for b in boroughs if b.lower() in query), None)
    year = next((y for y in years if str(y) in query), None)

    person = None
    if "pedestrian" in query:
        person = [p for p in person_types if "pedestrian" in p.lower()]
    elif "cyclist" in query or "bicyclist" in query:
        person = [p for p in person_types if "cyclist" in p.lower() or "bicyclist" in p.lower()]

    return ([borough] if borough else None,
            [year] if year else None,
            person)
