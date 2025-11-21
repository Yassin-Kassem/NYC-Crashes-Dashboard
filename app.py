"""
NYC Motor Vehicle Collisions Dashboard
Polars-lazy + GitHub Releases + Render-friendly (no OOM)
"""

import os
from pathlib import Path

import dash
from dash import dcc, html, Input, Output, State
import plotly.express as px
import plotly.graph_objects as go

import pandas as pd
import polars as pl

# =============================================================================
# CONFIG: FILL THESE WITH YOUR GITHUB RELEASE URLS
# =============================================================================

CRASH_URL = "https://github.com/Yassin-Kassem/NYC-Crashes-Dashboard/releases/download/v1.0/cleaned_collisions_crash_level.csv"
PERSON_URL = "https://github.com/Yassin-Kassem/NYC-Crashes-Dashboard/releases/download/v1.0/cleaned_collisions_person_level.csv"
# Local paths on Render / locally
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

CRASH_CSV_PATH = DATA_DIR / "cleaned_collisions_crash_level.csv"
PERSON_CSV_PATH = DATA_DIR / "cleaned_collisions_person_level.csv"


# =============================================================================
# HELPERS: DOWNLOAD LARGE CSVs ONCE (STREAMED, LOW RAM)
# =============================================================================

def download_if_missing(url: str, dest: Path):
    """Download a large CSV from a URL to dest if not already there."""
    if dest.exists():
        print(f"✅ Using existing local file: {dest}")
        return

    import requests

    print(f"⬇️ Downloading {url} → {dest} (this may take a while)...")
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
    print(f"✅ Download complete: {dest}")


# Download once (Render free can store on ephemeral disk)
download_if_missing(CRASH_URL, CRASH_CSV_PATH)
download_if_missing(PERSON_URL, PERSON_CSV_PATH)


# =============================================================================
# LOAD & PREPARE DATA (POLARS LAZY)
# =============================================================================

print("Setting up lazy data sources with Polars...")

# Lazy scan (does NOT load into RAM)
crash_lazy = pl.scan_csv(CRASH_CSV_PATH, ignore_errors=True)
person_lazy = pl.scan_csv(PERSON_CSV_PATH, ignore_errors=True)

# Prepare crash dataset: parse dates, times, add YEAR/MONTH/HOUR/SEASON
crash_lazy = crash_lazy.with_columns(
    [
        pl.col("CRASH DATE")
        .str.to_date(strict=False)
        .alias("CRASH_DATE"),
        pl.col("CRASH TIME")
        .str.to_date(strict=False)
        .alias("CRASH_TIME"),
    ]
).with_columns(
    [
        pl.col("CRASH_DATE").dt.year().alias("YEAR"),
        pl.col("CRASH_DATE").dt.month().alias("MONTH"),
        pl.col("CRASH_TIME").dt.hour().alias("HOUR"),
    ]
).with_columns(
    [
        pl.when(pl.col("MONTH").is_in([12, 1, 2]))
        .then("Winter")
        .when(pl.col("MONTH").is_in([3, 4, 5]))
        .then("Spring")
        .when(pl.col("MONTH").is_in([6, 7, 8]))
        .then("Summer")
        .when(pl.col("MONTH").is_in([9, 10, 11]))
        .then("Fall")
        .otherwise(None)
        .alias("SEASON")
    ]
).filter(pl.col("YEAR").is_between(2015, 2025))

# Prepare person dataset: parse date, add YEAR
person_lazy = person_lazy.with_columns(
    [
        pl.col("CRASH DATE")
        .str.to_date(strict=False)
        .alias("CRASH_DATE"),
        pl.col("CRASH DATE").dt.year().alias("YEAR"),
    ]
).filter(pl.col("YEAR").is_between(2015, 2025))

# Global counts (streaming, low RAM)
crash_count = crash_lazy.select(pl.count()).collect().item()
person_count = person_lazy.select(pl.count()).collect().item()

# Get filter options (only specific columns are read)
boroughs = (
    crash_lazy.select(pl.col("BOROUGH").drop_nulls().unique())
    .collect()
    .get_column("BOROUGH")
    .to_list()
)
boroughs = sorted(boroughs)

years = (
    crash_lazy.select(pl.col("YEAR").drop_nulls().unique())
    .collect()
    .get_column("YEAR")
    .to_list()
)
years = sorted(years)

# Vehicle type columns from schema
vehicle_cols = [
    name
    for name in crash_lazy.collect_schema().names()
    if "VEHICLE TYPE CODE" in name.upper()
]

if vehicle_cols:
    vehicle_counts = (
        crash_lazy
        .select(pl.col(vehicle_cols[0]).alias("VEHICLE"))
        .filter(pl.col("VEHICLE").is_not_null())
        .groupby("VEHICLE")
        .count()
        .sort("count", descending=True)
        .limit(30)
        .collect()
    )
    vehicle_types = sorted(vehicle_counts["VEHICLE"].to_list())
else:
    vehicle_types = []

# Person types
if "PERSON_TYPE" in person_lazy.collect_schema().names():
    person_type_df = (
        person_lazy
        .select(pl.col("PERSON_TYPE").drop_nulls().unique())
        .collect()
    )
    person_types = sorted(person_type_df["PERSON_TYPE"].to_list())
else:
    person_types = []

print("✅ Lazy data setup complete")
print(f"   Crashes: {crash_count:,}")
print(f"   Persons: {person_count:,}")
print(f"   Boroughs: {len(boroughs)}")
print(f"   Years: {len(years)}")
print(f"   Vehicle types: {len(vehicle_types)}")
print(f"   Person types: {len(person_types)}")
print("=" * 60)


# =============================================================================
# DASH APP SETUP
# =============================================================================

app = dash.Dash(
    __name__, meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}]
)
server = app.server
app.title = "NYC Motor Vehicle Collisions Dashboard"

# =============================================================================
# LAYOUT (same visual structure as your original)
# =============================================================================

app.layout = html.Div(
    className="app-shell",
    children=[
        # Header
        html.Div(
            className="app-header",
            children=[
                html.Div(
                    className="app-header-top",
                    children=[
                        html.Div(
                            className="app-title",
                            children=[
                                html.Span("🚗", className="app-title-icon"),
                                html.Span(
                                    "NYC Motor Vehicle Collisions Dashboard",
                                    className="app-title-text",
                                ),
                            ],
                        ),
                        html.Div(
                            className="app-badge",
                            children="Data Engineering & Visualization · GIU 2025",
                        ),
                    ],
                ),
                html.Div(
                    className="app-header-subtitle",
                    children="Interactive analysis of motor vehicle crashes in New York City (2015–2025)",
                ),
                html.Div(
                    className="app-header-meta",
                    children=f"Dataset: {crash_count:,} crashes · {person_count:,} person records",
                ),
            ],
        ),

        # Main layout: sidebar + content
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
                                html.Div(
                                    className="filter-section-title",
                                    children=[
                                        html.H3("Filters"),
                                        html.Span(
                                            "Tip: use the search box for quick smart filtering",
                                            className="filter-hint",
                                        ),
                                    ],
                                ),
                                # Row 1
                                html.Div(
                                    className="filter-row",
                                    children=[
                                        html.Div(
                                            className="filter-col",
                                            children=[
                                                html.Label("Borough"),
                                                dcc.Dropdown(
                                                    id="borough-filter",
                                                    className="dash-dropdown",
                                                    options=[
                                                        {"label": "All Boroughs", "value": "ALL"}
                                                    ]
                                                    + [
                                                        {"label": b, "value": b}
                                                        for b in boroughs
                                                    ],
                                                    value="ALL",
                                                    multi=True,
                                                ),
                                            ],
                                        ),
                                        html.Div(
                                            className="filter-col",
                                            children=[
                                                html.Label("Year"),
                                                dcc.Dropdown(
                                                    id="year-filter",
                                                    className="dash-dropdown",
                                                    options=[
                                                        {"label": "All Years", "value": "ALL"}
                                                    ]
                                                    + [
                                                        {"label": str(y), "value": y}
                                                        for y in years
                                                    ],
                                                    value="ALL",
                                                    multi=True,
                                                ),
                                            ],
                                        ),
                                    ],
                                ),
                                # Row 2
                                html.Div(
                                    className="filter-row",
                                    children=[
                                        html.Div(
                                            className="filter-col",
                                            children=[
                                                html.Label("Vehicle Type"),
                                                dcc.Dropdown(
                                                    id="vehicle-filter",
                                                    className="dash-dropdown",
                                                    options=[
                                                        {"label": "All Vehicles", "value": "ALL"}
                                                    ]
                                                    + [
                                                        {"label": v, "value": v}
                                                        for v in vehicle_types
                                                    ],
                                                    value="ALL",
                                                    multi=True,
                                                ),
                                            ],
                                        ),
                                        html.Div(
                                            className="filter-col",
                                            children=[
                                                html.Label("Person Type"),
                                                dcc.Dropdown(
                                                    id="person-filter",
                                                    className="dash-dropdown",
                                                    options=[
                                                        {"label": "All Types", "value": "ALL"}
                                                    ]
                                                    + [
                                                        {"label": p, "value": p}
                                                        for p in person_types
                                                    ],
                                                    value="ALL",
                                                    multi=True,
                                                ),
                                            ],
                                        ),
                                    ],
                                ),
                                html.Label("Search Mode", style={"marginTop": "8px"}),
                                html.Div(
                                    className="search-row",
                                    children=[
                                        dcc.Input(
                                            id="search-input",
                                            type="text",
                                            placeholder='e.g., "Brooklyn 2022 pedestrian crashes"',
                                        ),
                                        html.Button("Clear", id="clear-search-btn", n_clicks=0),
                                    ],
                                ),
                            ],
                        ),
                        # Generate report
                        html.Div(
                            className="card",
                            style={"textAlign": "center"},
                            children=[
                                html.Button(
                                    "📊 Generate Report",
                                    id="generate-report-btn",
                                    n_clicks=0,
                                ),
                                html.Div(
                                    id="loading-indicator",
                                    style={
                                        "display": "block",
                                        "marginTop": "10px",
                                        "color": "#7f8c8d",
                                        "fontSize": "12px",
                                    },
                                ),
                            ],
                        ),
                    ],
                ),

                # Content area
                html.Div(
                    className="content-area",
                    children=[
                        html.Div(id="summary-stats"),
                        html.Div(
                            children=[
                                html.Div(
                                    className="row",
                                    children=[
                                        html.Div(
                                            className="col",
                                            children=[
                                                html.Div(
                                                    className="card graph-card",
                                                    children=[dcc.Graph(id="temporal-chart")],
                                                )
                                            ],
                                        ),
                                        html.Div(
                                            className="col",
                                            children=[
                                                html.Div(
                                                    className="card graph-card",
                                                    children=[dcc.Graph(id="borough-chart")],
                                                )
                                            ],
                                        ),
                                    ],
                                ),
                                html.Div(
                                    className="row",
                                    children=[
                                        html.Div(
                                            className="col",
                                            children=[
                                                html.Div(
                                                    className="card graph-card",
                                                    children=[dcc.Graph(id="hour-chart")],
                                                )
                                            ],
                                        ),
                                        html.Div(
                                            className="col",
                                            children=[
                                                html.Div(
                                                    className="card graph-card",
                                                    children=[dcc.Graph(id="victim-chart")],
                                                )
                                            ],
                                        ),
                                    ],
                                ),
                                html.Div(
                                    className="row",
                                    children=[
                                        html.Div(
                                            className="col",
                                            children=[
                                                html.Div(
                                                    className="card graph-card",
                                                    children=[dcc.Graph(id="factors-chart")],
                                                )
                                            ],
                                        ),
                                        html.Div(
                                            className="col",
                                            children=[
                                                html.Div(
                                                    className="card graph-card",
                                                    children=[dcc.Graph(id="vehicle-chart")],
                                                )
                                            ],
                                        ),
                                    ],
                                ),
                                html.Div(
                                    className="row",
                                    children=[
                                        html.Div(
                                            className="col",
                                            children=[
                                                html.Div(
                                                    className="card graph-card",
                                                    children=[dcc.Graph(id="map-chart")],
                                                )
                                            ],
                                        ),
                                        html.Div(
                                            className="col",
                                            children=[
                                                html.Div(
                                                    className="card graph-card",
                                                    children=[dcc.Graph(id="seasonal-chart")],
                                                )
                                            ],
                                        ),
                                    ],
                                ),
                                html.Div(
                                    className="row",
                                    children=[
                                        html.Div(
                                            className="col",
                                            children=[
                                                html.Div(
                                                    className="card graph-card",
                                                    children=[dcc.Graph(id="heatmap-chart")],
                                                )
                                            ],
                                        ),
                                        html.Div(
                                            className="col",
                                            children=[
                                                html.Div(
                                                    className="card graph-card",
                                                    children=[dcc.Graph(id="age-chart")],
                                                )
                                            ],
                                        ),
                                    ],
                                ),
                            ]
                        ),
                    ],
                ),
            ],
        ),

        html.Div(
            children=[
                html.P(
                    "NYC Motor Vehicle Collisions Dashboard · Data Engineering & Visualization Project · GIU 2025",
                    className="footer-text",
                )
            ]
        ),
    ],
)


# =============================================================================
# HELPER FUNCTIONS (FILTERING + SEARCH)
# =============================================================================

def filter_crash_lazy(boroughs_sel, years_sel, vehicles_sel):
    lf = crash_lazy

    if boroughs_sel and "ALL" not in boroughs_sel:
        lf = lf.filter(pl.col("BOROUGH").is_in(boroughs_sel))

    if years_sel and "ALL" not in years_sel:
        lf = lf.filter(pl.col("YEAR").is_in(years_sel))

    if vehicles_sel and "ALL" not in vehicles_sel and vehicle_cols:
        cond = pl.lit(False)
        for col in vehicle_cols:
            cond = cond | pl.col(col).is_in(vehicles_sel)
        lf = lf.filter(cond)

    return lf


def filter_person_lazy(boroughs_sel, years_sel, persons_sel):
    lf = person_lazy

    if boroughs_sel and "ALL" not in boroughs_sel:
        lf = lf.filter(pl.col("BOROUGH").is_in(boroughs_sel))

    if years_sel and "ALL" not in years_sel:
        lf = lf.filter(pl.col("YEAR").is_in(years_sel))

    if persons_sel and "ALL" not in persons_sel and "PERSON_TYPE" in person_lazy.collect_schema().names():
        lf = lf.filter(pl.col("PERSON_TYPE").is_in(persons_sel))

    return lf


def parse_search_query(query):
    if not query:
        return None, None, None

    q = query.lower()

    borough_match = None
    for b in boroughs:
        if b and b.lower() in q:
            borough_match = [b]
            break

    year_match = None
    for y in years:
        if str(y) in q:
            year_match = [y]
            break

    person_match = None
    if "pedestrian" in q:
        person_match = [p for p in person_types if "pedestrian" in p.lower()]
    elif "cyclist" in q or "bicyclist" in q:
        person_match = [
            p for p in person_types if "cyclist" in p.lower() or "bicyclist" in p.lower()
        ]

    return borough_match, year_match, person_match


# =============================================================================
# CALLBACKS
# =============================================================================

@app.callback(
    [
        Output("borough-filter", "value"),
        Output("year-filter", "value"),
        Output("person-filter", "value"),
    ],
    [Input("search-input", "value"), Input("clear-search-btn", "n_clicks")],
    [
        State("borough-filter", "value"),
        State("year-filter", "value"),
        State("person-filter", "value"),
    ],
)
def handle_search(search_query, clear_clicks, current_borough, current_year, current_person):
    ctx = dash.callback_context

    if not ctx.triggered:
        return current_borough, current_year, current_person

    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if trigger_id == "clear-search-btn":
        return "ALL", "ALL", "ALL"

    if trigger_id == "search-input" and search_query:
        borough_match, year_match, person_match = parse_search_query(search_query)
        return (
            borough_match or current_borough,
            year_match or current_year,
            person_match or current_person,
        )

    return current_borough, current_year, current_person


@app.callback(
    [
        Output("summary-stats", "children"),
        Output("temporal-chart", "figure"),
        Output("borough-chart", "figure"),
        Output("hour-chart", "figure"),
        Output("victim-chart", "figure"),
        Output("factors-chart", "figure"),
        Output("vehicle-chart", "figure"),
        Output("map-chart", "figure"),
        Output("seasonal-chart", "figure"),
        Output("heatmap-chart", "figure"),
        Output("age-chart", "figure"),
    ],
    [Input("generate-report-btn", "n_clicks")],
    [
        State("borough-filter", "value"),
        State("year-filter", "value"),
        State("vehicle-filter", "value"),
        State("person-filter", "value"),
    ],
)
def update_dashboard(n_clicks, boroughs_sel, years_sel, vehicles_sel, persons_sel):
    # Normalize filter values
    if boroughs_sel == "ALL" or not boroughs_sel:
        boroughs_sel = ["ALL"]
    elif not isinstance(boroughs_sel, list):
        boroughs_sel = [boroughs_sel]

    if years_sel == "ALL" or not years_sel:
        years_sel = ["ALL"]
    elif not isinstance(years_sel, list):
        years_sel = [years_sel]

    if vehicles_sel == "ALL" or not vehicles_sel:
        vehicles_sel = ["ALL"]
    elif not isinstance(vehicles_sel, list):
        vehicles_sel = [vehicles_sel]

    if persons_sel == "ALL" or not persons_sel:
        persons_sel = ["ALL"]
    elif not isinstance(persons_sel, list):
        persons_sel = [persons_sel]

    # Filtered lazy frames
    crash_lf = filter_crash_lazy(boroughs_sel, years_sel, vehicles_sel)
    person_lf = filter_person_lazy(boroughs_sel, years_sel, persons_sel)

    # Summary stats (streaming, low RAM)
    summary_counts = crash_lf.select(
        [
            pl.count().alias("total_crashes"),
            pl.col("NUMBER OF PERSONS INJURED").sum().alias("total_injuries"),
            pl.col("NUMBER OF PERSONS KILLED").sum().alias("total_deaths"),
        ]
    ).collect()

    total_crashes = int(summary_counts["total_crashes"][0] or 0)
    total_injuries = int(summary_counts["total_injuries"][0] or 0)
    total_deaths = int(summary_counts["total_deaths"][0] or 0)

    summary = html.Div(
        className="card",
        children=[
            html.Div(
                className="summary-row",
                children=[
                    html.Div(
                        className="summary-box",
                        children=[
                            html.Div("Total Crashes", className="summary-label"),
                            html.Div(
                                f"{total_crashes:,}",
                                className="summary-number",
                                style={"color": "#3498db"},
                            ),
                        ],
                    ),
                    html.Div(
                        className="summary-box",
                        children=[
                            html.Div("Total Injuries", className="summary-label"),
                            html.Div(
                                f"{total_injuries:,}",
                                className="summary-number",
                                style={"color": "#e67e22"},
                            ),
                        ],
                    ),
                    html.Div(
                        className="summary-box",
                        children=[
                            html.Div("Total Deaths", className="summary-label"),
                            html.Div(
                                f"{total_deaths:,}",
                                className="summary-number",
                                style={"color": "#e74c3c"},
                            ),
                        ],
                    ),
                ],
            )
        ],
    )

    # 1. Temporal chart
    temporal_df = (
        crash_lf.groupby("YEAR")
        .count()
        .select(["YEAR", "count"])
        .sort("YEAR")
        .collect()
        .to_pandas()
        .rename(columns={"count": "crashes"})
    )

    fig_temporal = px.line(
        temporal_df,
        x="YEAR",
        y="crashes",
        title="Crashes Over Time",
        labels={"YEAR": "Year", "crashes": "Number of Crashes"},
        markers=True,
    )
    fig_temporal.update_traces(line_color="#3498db", line_width=3)
    fig_temporal.update_layout(hovermode="x unified")

    # 2. Borough chart
    borough_df = (
        crash_lf.groupby("BOROUGH")
        .count()
        .select(["BOROUGH", "count"])
        .sort("count", descending=True)
        .collect()
        .to_pandas()
        .rename(columns={"count": "Crashes"})
    )

    fig_borough = go.Figure(
        go.Bar(
            x=borough_df["BOROUGH"],
            y=borough_df["Crashes"],
            marker=dict(color=borough_df["Crashes"], colorscale="Reds", showscale=True),
        )
    )
    fig_borough.update_layout(
        title="Crashes by Borough", xaxis_title="Borough", yaxis_title="Number of Crashes", height=400
    )

    # 3. Hour chart
    hour_df = (
        crash_lf.groupby("HOUR")
        .count()
        .select(["HOUR", "count"])
        .sort("HOUR")
        .collect()
        .to_pandas()
        .rename(columns={"count": "crashes"})
    )
    fig_hour = px.area(
        hour_df,
        x="HOUR",
        y="crashes",
        title="Crashes by Hour of Day",
        labels={"HOUR": "Hour", "crashes": "Number of Crashes"},
    )
    fig_hour.update_traces(fill="tozeroy", line_color="#2ecc71")

    # 4. Victim chart
    if "PERSON_TYPE" in person_lazy.collect_schema().names():
        victim_df = (
            person_lf.groupby("PERSON_TYPE")
            .count()
            .sort("count", descending=True)
            .limit(5)
            .collect()
            .to_pandas()
        )
        fig_victim = px.pie(
            victim_df,
            values="count",
            names="PERSON_TYPE",
            title="Victim Types Distribution",
        )
    else:
        fig_victim = go.Figure()
        fig_victim.add_annotation(
            text="Person type data not available", showarrow=False, font_size=16
        )

    # 5. Contributing factors
    factor_cols = [
        name
        for name in crash_lazy.collect_schema().names()
        if "CONTRIBUTING FACTOR" in name.upper()
    ]
    if factor_cols:
        factor_col = factor_cols[0]
        factors_df = (
            crash_lf.groupby(factor_col)
            .count()
            .sort("count", descending=True)
            .limit(10)
            .collect()
            .to_pandas()
        )
        fig_factors = go.Figure(
            go.Bar(
                x=factors_df["count"],
                y=factors_df[factor_col],
                orientation="h",
                marker_color="#e74c3c",
            )
        )
        fig_factors.update_layout(
            title="Top 10 Contributing Factors",
            xaxis_title="Number of Crashes",
            yaxis_title="Contributing Factor",
            height=400,
        )
    else:
        fig_factors = go.Figure()
        fig_factors.add_annotation(
            text="Contributing factor data not available", showarrow=False, font_size=16
        )

    # 6. Vehicle chart
    if vehicle_cols:
        vcol = vehicle_cols[0]
        vehicle_df = (
            crash_lf.groupby(vcol)
            .count()
            .sort("count", descending=True)
            .limit(10)
            .collect()
            .to_pandas()
        )
        fig_vehicle = go.Figure(
            go.Bar(
                x=vehicle_df[vcol],
                y=vehicle_df["count"],
                marker_color="#9b59b6",
            )
        )
        fig_vehicle.update_layout(
            title="Top 10 Vehicle Types",
            xaxis_title="Vehicle Type",
            yaxis_title="Number of Crashes",
            xaxis_tickangle=45,
            height=400,
        )
    else:
        fig_vehicle = go.Figure()
        fig_vehicle.add_annotation(
            text="Vehicle type data not available", showarrow=False, font_size=16
        )

    # 7. Map chart (sample for performance)
    map_base = crash_lf.select(
        [
            pl.col("LATITUDE"),
            pl.col("LONGITUDE"),
            pl.col("BOROUGH"),
            pl.col("NUMBER OF PERSONS INJURED"),
        ]
    ).filter(
        pl.col("LATITUDE").is_not_null() & pl.col("LONGITUDE").is_not_null()
    )

    map_count = map_base.select(pl.count().alias("n")).collect()["n"][0]
    if map_count > 0:
        sample_n = min(2000, map_count)
        map_df = (
            map_base.sample(n=sample_n, with_replacement=False)
            .collect()
            .to_pandas()
        )
        fig_map = px.scatter_mapbox(
            map_df,
            lat="LATITUDE",
            lon="LONGITUDE",
            hover_data=["BOROUGH", "NUMBER OF PERSONS INJURED"],
            title=f"Crash Locations Map (showing {sample_n:,} of {map_count:,} crashes)",
            zoom=9.5,
            height=500,
        )
        fig_map.update_layout(mapbox_style="open-street-map")
        fig_map.update_traces(marker=dict(size=4, opacity=0.6, color="red"))
    else:
        fig_map = go.Figure()
        fig_map.add_annotation(
            text="No location data available for selected filters",
            showarrow=False,
            font_size=16,
        )
        fig_map.update_layout(height=500)

    # 8. Seasonal chart
    seasonal_df = (
        crash_lf.groupby("SEASON")
        .count()
        .select(["SEASON", "count"])
        .collect()
        .to_pandas()
        .rename(columns={"count": "Crashes"})
    )

    # enforce order
    season_order = ["Spring", "Summer", "Fall", "Winter"]
    seasonal_df["SEASON"] = pd.Categorical(
        seasonal_df["SEASON"], categories=season_order, ordered=True
    )
    seasonal_df = seasonal_df.sort_values("SEASON")

    fig_seasonal = px.bar(
        seasonal_df,
        x="SEASON",
        y="Crashes",
        title="Crashes by Season",
        labels={"SEASON": "Season", "Crashes": "Number of Crashes"},
        color="SEASON",
        color_discrete_map={
            "Spring": "#2ecc71",
            "Summer": "#f39c12",
            "Fall": "#e67e22",
            "Winter": "#3498db",
        },
    )
    fig_seasonal.update_layout(showlegend=False)

    # 9. Heatmap (hour vs weekday)
    heat_lf = crash_lf.with_columns(
        [
            pl.col("CRASH_DATE").dt.weekday().alias("WEEKDAY_IDX"),
            pl.col("CRASH_DATE").dt.strftime("%A").alias("WEEKDAY"),
        ]
    )
    heat_df = (
        heat_lf.groupby(["HOUR", "WEEKDAY"])
        .count()
        .select(["HOUR", "WEEKDAY", "count"])
        .collect()
        .to_pandas()
        .rename(columns={"count": "crashes"})
    )

    weekday_order = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    heat_df["WEEKDAY"] = pd.Categorical(
        heat_df["WEEKDAY"], categories=weekday_order, ordered=True
    )
    heat_pivot = (
        heat_df.pivot(index="HOUR", columns="WEEKDAY", values="crashes")
        .fillna(0)
        .reindex(columns=weekday_order)
    )

    fig_heatmap = go.Figure(
        data=go.Heatmap(
            z=heat_pivot.values,
            x=heat_pivot.columns,
            y=heat_pivot.index,
            colorscale="Reds",
            hovertemplate="Day: %{x}<br>Hour: %{y}<br>Crashes: %{z}<extra></extra>",
        )
    )
    fig_heatmap.update_layout(
        title="Crash Heatmap: Hour vs Day of Week",
        xaxis_title="Day of Week",
        yaxis_title="Hour of Day",
    )

    # 10. Age histogram
    if "PERSON_AGE" in person_lazy.collect_schema().names():
        age_df = (
            person_lf
            .filter(
                (pl.col("PERSON_AGE").is_not_null())
                & (pl.col("PERSON_AGE") > 0)
                & (pl.col("PERSON_AGE") < 120)
            )
            .select("PERSON_AGE")
            .collect()
            .to_pandas()
        )
        fig_age = px.histogram(
            age_df,
            x="PERSON_AGE",
            nbins=30,
            title="Age Distribution of Crash Victims",
            labels={"PERSON_AGE": "Age", "count": "Number of Victims"},
        )
        fig_age.update_traces(marker_color="#1abc9c")
    else:
        fig_age = go.Figure()
        fig_age.add_annotation(
            text="Age data not available", showarrow=False, font_size=16
        )

    return (
        summary,
        fig_temporal,
        fig_borough,
        fig_hour,
        fig_victim,
        fig_factors,
        fig_vehicle,
        fig_map,
        fig_seasonal,
        fig_heatmap,
        fig_age,
    )


# =============================================================================
# RUN APP (LOCAL DEV)
# =============================================================================

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=8050)
