"""
NYC Motor Vehicle Collisions Dashboard
Optimized for Render Free Tier with intelligent sampling
"""

import dash
from dash import dcc, html, Input, Output, State
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime

# =============================================================================
# CONFIGURATION
# =============================================================================

# Smart sampling configuration
CRASH_SAMPLE_SIZE = 30000  # Load 30k most recent crashes
PERSON_SAMPLE_SIZE = 60000  # Load 60k person records

print("=" * 60)
print("NYC MOTOR VEHICLE COLLISIONS DASHBOARD")
print("Optimized for Render Free Tier")
print("=" * 60)

# =============================================================================
# LOAD AND PREPARE DATA
# =============================================================================

print(f"Loading sampled data (Crashes: {CRASH_SAMPLE_SIZE:,}, Persons: {PERSON_SAMPLE_SIZE:,})...")

# Load crash data with sampling
df_crash = pd.read_csv(
    "data/cleaned_collisions_crash_level.csv",
    low_memory=False,
    nrows=CRASH_SAMPLE_SIZE  # Only load first N rows
)

# Load person data with sampling
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
    nrows=PERSON_SAMPLE_SIZE  # Only load first N rows
)

print(f"✅ Loaded {len(df_crash):,} crashes and {len(df_person):,} person records")

# Convert dates
df_crash["CRASH DATE"] = pd.to_datetime(df_crash["CRASH DATE"], errors="coerce")
df_person["CRASH DATE"] = pd.to_datetime(df_person["CRASH DATE"], errors="coerce")

# Create time features
df_crash["YEAR"] = df_crash["CRASH DATE"].dt.year
df_crash["MONTH"] = df_crash["CRASH DATE"].dt.month
df_crash["HOUR"] = pd.to_datetime(
    df_crash["CRASH TIME"], format="%H:%M:%S", errors="coerce"
).dt.hour

# Filter to 2015-2025 only (reduces memory further)
print("Filtering data to 2015-2025...")
df_crash = df_crash[df_crash["YEAR"].between(2015, 2025)].reset_index(drop=True)
df_person = df_person[
    df_person["CRASH DATE"].dt.year.between(2015, 2025)
].reset_index(drop=True)

print(f"✅ Filtered to {len(df_crash):,} crashes and {len(df_person):,} person records (2015-2025)")

# Create season column
df_crash["SEASON"] = df_crash["MONTH"].map(
    {
        12: "Winter", 1: "Winter", 2: "Winter",
        3: "Spring", 4: "Spring", 5: "Spring",
        6: "Summer", 7: "Summer", 8: "Summer",
        9: "Fall", 10: "Fall", 11: "Fall",
    }
)

# Get filter options
print("Preparing filter options...")
boroughs = sorted(df_crash["BOROUGH"].dropna().unique().tolist())
years = sorted(df_crash["YEAR"].dropna().unique().tolist())

# Get vehicle types (top 30 only)
vehicle_cols = [col for col in df_crash.columns if "VEHICLE TYPE CODE" in col.upper()]
if vehicle_cols:
    all_vehicles = df_crash[vehicle_cols[0]].dropna().value_counts()
    vehicle_types = sorted(all_vehicles.head(30).index.tolist())
else:
    vehicle_types = []

# Get person types
person_types = (
    sorted(df_person["PERSON_TYPE"].dropna().unique().tolist())
    if "PERSON_TYPE" in df_person.columns
    else []
)

print("✅ Data preparation complete!")
print(f"   Boroughs: {len(boroughs)}")
print(f"   Years: {len(years)} ({min(years)}-{max(years)})")
print(f"   Vehicle types: {len(vehicle_types)}")
print(f"   Person types: {len(person_types)}")
print("=" * 60)

# =============================================================================
# INITIALIZE DASH APP
# =============================================================================

app = dash.Dash(
    __name__, 
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}]
)

server = app.server  # For deployment

app.title = "NYC Motor Vehicle Collisions Dashboard"

# =============================================================================
# APP LAYOUT
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
                    children=f"Dataset: {len(df_crash):,} crashes · {len(df_person):,} person records (representative sample)",
                ),
            ],
        ),

        # Main layout: sidebar + content
        html.Div(
            className="main-layout",
            children=[
                # Sidebar (filters)
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
                                # Filter row
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
                                                    placeholder="Select borough(s)...",
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
                                                    placeholder="Select year(s)...",
                                                ),
                                            ],
                                        ),
                                    ],
                                ),
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
                                                    placeholder="Select vehicle type(s)...",
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
                                                    placeholder="Select person type(s)...",
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
                        # Generate report card
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

                # Content area (summary + visualizations)
                html.Div(
                    className="content-area",
                    children=[
                        # Summary Statistics
                        html.Div(id="summary-stats"),

                        # Visualizations Grid
                        html.Div(
                            children=[
                                # Row 1: Temporal and Borough Analysis
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
                                # Row 2: Time of Day and Victim Analysis
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
                                # Row 3: Contributing Factors and Vehicle Types
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
                                # Row 4: Map and Seasonal Analysis
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
                                # Row 5: Heatmap and Age Analysis
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

        # Footer
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
# HELPER FUNCTIONS
# =============================================================================

def filter_data(df, boroughs_sel, years_sel, vehicles_sel):
    """Apply filters to crash dataset"""
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
    """Apply filters to person dataset"""
    filtered = df.copy()

    if boroughs_sel and "ALL" not in boroughs_sel:
        filtered = filtered[filtered["BOROUGH"].isin(boroughs_sel)]

    if years_sel and "ALL" not in years_sel:
        filtered = filtered[filtered["CRASH DATE"].dt.year.isin(years_sel)]

    if persons_sel and "ALL" not in persons_sel and "PERSON_TYPE" in filtered.columns:
        filtered = filtered[filtered["PERSON_TYPE"].isin(persons_sel)]

    return filtered

def parse_search_query(query):
    """Parse natural language search query into filters"""
    if not query:
        return None, None, None

    query = query.lower()

    borough_match = None
    for b in boroughs:
        if b.lower() in query:
            borough_match = [b]
            break

    year_match = None
    for y in years:
        if str(y) in query:
            year_match = [y]
            break

    person_match = None
    if "pedestrian" in query:
        person_match = [p for p in person_types if "pedestrian" in p.lower()]
    elif "cyclist" in query or "bicyclist" in query:
        person_match = [
            p for p in person_types
            if "cyclist" in p.lower() or "bicyclist" in p.lower()
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
    """Handle search input and clear button"""
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
    """Main callback to update all visualizations"""

    # Convert 'ALL' to list for processing
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

    # Filter data
    filtered_crash = filter_data(df_crash, boroughs_sel, years_sel, vehicles_sel)
    filtered_person = filter_person_data(df_person, boroughs_sel, years_sel, persons_sel)

    # Summary statistics
    total_crashes = len(filtered_crash)
    total_injuries = filtered_crash["NUMBER OF PERSONS INJURED"].sum()
    total_deaths = filtered_crash["NUMBER OF PERSONS KILLED"].sum()

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
                                f"{int(total_injuries):,}",
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
                                f"{int(total_deaths):,}",
                                className="summary-number",
                                style={"color": "#e74c3c"},
                            ),
                        ],
                    ),
                ],
            )
        ],
    )

    # 1. Temporal Chart
    temporal_data = filtered_crash.groupby("YEAR").size().reset_index(name="crashes")
    fig_temporal = px.line(
        temporal_data,
        x="YEAR",
        y="crashes",
        title="Crashes Over Time",
        labels={"crashes": "Number of Crashes", "YEAR": "Year"},
        markers=True,
    )
    fig_temporal.update_traces(line_color="#3498db", line_width=3)
    fig_temporal.update_layout(hovermode="x unified")

    # 2. Borough Chart
    borough_data = filtered_crash["BOROUGH"].value_counts().reset_index()
    borough_data.columns = ["Borough", "Crashes"]
    fig_borough = go.Figure(
        go.Bar(
            x=borough_data["Borough"],
            y=borough_data["Crashes"],
            marker=dict(color=borough_data["Crashes"], colorscale="Reds", showscale=True),
        )
    )
    fig_borough.update_layout(
        title="Crashes by Borough", 
        xaxis_title="Borough", 
        yaxis_title="Number of Crashes", 
        height=400
    )

    # 3. Hour Chart
    hour_data = filtered_crash.groupby("HOUR").size().reset_index(name="crashes")
    fig_hour = px.area(
        hour_data,
        x="HOUR",
        y="crashes",
        title="Crashes by Hour of Day",
        labels={"crashes": "Number of Crashes", "HOUR": "Hour"},
    )
    fig_hour.update_traces(fill="tozeroy", line_color="#2ecc71")

    # 4. Victim Chart
    if "PERSON_TYPE" in filtered_person.columns:
        victim_data = filtered_person["PERSON_TYPE"].value_counts().head(5)
        fig_victim = px.pie(
            values=victim_data.values,
            names=victim_data.index,
            title="Victim Types Distribution",
        )
    else:
        fig_victim = go.Figure()
        fig_victim.add_annotation(
            text="Person type data not available", showarrow=False, font_size=16
        )

    # 5. Contributing Factors
    factor_cols = [col for col in filtered_crash.columns if "CONTRIBUTING FACTOR" in col.upper()]
    if factor_cols:
        factors_data = filtered_crash[factor_cols[0]].value_counts().head(10)
        fig_factors = go.Figure(
            go.Bar(
                x=factors_data.values,
                y=factors_data.index,
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
        fig_factors.update_layout(height=400)

    # 6. Vehicle Chart
    if vehicle_cols:
        vehicle_data = filtered_crash[vehicle_cols[0]].value_counts().head(10)
        fig_vehicle = go.Figure(
            go.Bar(x=vehicle_data.index, y=vehicle_data.values, marker_color="#9b59b6")
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
        fig_vehicle.update_layout(height=400)

    # 7. Map (optimized with sampling)
    map_data = filtered_crash[
        (filtered_crash["LATITUDE"].notna()) & (filtered_crash["LONGITUDE"].notna())
    ]

    # Sample for performance (max 1500 points)
    if len(map_data) > 1500:
        map_sample = map_data.sample(n=1500, random_state=42)
    else:
        map_sample = map_data

    if len(map_sample) > 0:
        fig_map = px.scatter_mapbox(
            map_sample,
            lat="LATITUDE",
            lon="LONGITUDE",
            hover_data=["BOROUGH", "NUMBER OF PERSONS INJURED"],
            title=f"Crash Locations Map (showing {len(map_sample):,} of {len(map_data):,} crashes)",
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

    # 8. Seasonal Chart
    seasonal_data = (
        filtered_crash["SEASON"]
        .value_counts()
        .reindex(["Spring", "Summer", "Fall", "Winter"])
    )
    fig_seasonal = px.bar(
        x=seasonal_data.index,
        y=seasonal_data.values,
        title="Crashes by Season",
        labels={"x": "Season", "y": "Number of Crashes"},
        color=seasonal_data.index,
        color_discrete_map={
            "Spring": "#2ecc71",
            "Summer": "#f39c12",
            "Fall": "#e67e22",
            "Winter": "#3498db",
        },
    )
    fig_seasonal.update_layout(showlegend=False)

    # 9. Heatmap
    filtered_crash["WEEKDAY"] = filtered_crash["CRASH DATE"].dt.day_name()
    weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    heatmap_data = filtered_crash.groupby(["HOUR", "WEEKDAY"]).size().reset_index(name="crashes")
    heatmap_pivot = (
        heatmap_data.pivot(index="HOUR", columns="WEEKDAY", values="crashes")
        .fillna(0)
        .reindex(columns=weekday_order)
    )

    fig_heatmap = go.Figure(
        data=go.Heatmap(
            z=heatmap_pivot.values,
            x=heatmap_pivot.columns,
            y=heatmap_pivot.index,
            colorscale="Reds",
            hovertemplate="Day: %{x}<br>Hour: %{y}<br>Crashes: %{z}<extra></extra>",
        )
    )
    fig_heatmap.update_layout(
        title="Crash Heatmap: Hour vs Day of Week",
        xaxis_title="Day of Week",
        yaxis_title="Hour of Day",
    )

    # 10. Age Chart
    if "PERSON_AGE" in filtered_person.columns:
        age_data = filtered_person[
            (filtered_person["PERSON_AGE"].notna())
            & (filtered_person["PERSON_AGE"] > 0)
            & (filtered_person["PERSON_AGE"] < 120)
        ]
        fig_age = px.histogram(
            age_data,
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
# RUN APP
# =============================================================================

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)