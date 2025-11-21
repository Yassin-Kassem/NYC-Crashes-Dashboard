"""
NYC Motor Vehicle Collisions Dashboard
DuckDB-powered version (Render-friendly)
"""

import os
import duckdb
import pandas as pd

import dash
from dash import dcc, html, Input, Output, State
import plotly.express as px
import plotly.graph_objects as go

# =============================================================================
# CONFIG & DATA SOURCES
# =============================================================================

CRASH_URL = "https://github.com/Yassin-Kassem/NYC-Crashes-Dashboard/releases/download/v1.0/cleaned_collisions_crash_level.csv"
PERSON_URL = "https://github.com/Yassin-Kassem/NYC-Crashes-Dashboard/releases/download/v1.0/cleaned_collisions_person_level.csv"

ON_RENDER = "RENDER" in os.environ  # Render sets this env variable automatically
print("Running on Render:", ON_RENDER)

# =============================================================================
# DUCKDB CONNECTION & VIEWS
# =============================================================================

print("Setting up DuckDB and registering CSVs...")

con = duckdb.connect()

# We filter 2015–2025 at the view level to reduce data volume a bit
con.execute(f"""
    CREATE OR REPLACE VIEW crash AS
    SELECT *
    FROM read_csv_auto('{CRASH_URL}', AUTO_DETECT=TRUE)
    WHERE "CRASH DATE" IS NOT NULL
      AND year(CAST("CRASH DATE" AS DATE)) BETWEEN 2015 AND 2025
""")

con.execute(f"""
    CREATE OR REPLACE VIEW person AS
    SELECT *
    FROM read_csv_auto('{PERSON_URL}', AUTO_DETECT=TRUE)
    WHERE "CRASH DATE" IS NOT NULL
      AND year(CAST("CRASH DATE" AS DATE)) BETWEEN 2015 AND 2025
""")

print("✅ DuckDB views created (no full in-memory load).")

# =============================================================================
# GLOBAL METADATA & FILTER OPTIONS
# =============================================================================

# Column names from crash view
crash_cols = con.execute("SELECT * FROM crash LIMIT 0").df().columns.tolist()

# Vehicle type columns
vehicle_cols = [c for c in crash_cols if "VEHICLE TYPE CODE" in c.upper()]

# Borough options
boroughs_df = con.execute("""
    SELECT DISTINCT BOROUGH
    FROM crash
    WHERE BOROUGH IS NOT NULL
    ORDER BY BOROUGH
""").df()
boroughs = boroughs_df["BOROUGH"].tolist()

# Year options
years_df = con.execute("""
    SELECT DISTINCT year(CAST("CRASH DATE" AS DATE)) AS YEAR
    FROM crash
    ORDER BY YEAR
""").df()
years = years_df["YEAR"].tolist()

# Vehicle type options (top 30 from first vehicle column)
if vehicle_cols:
    vcol = vehicle_cols[0]
    vehicle_types_df = con.execute(f"""
        SELECT "{vcol}" AS vehicle, COUNT(*) AS cnt
        FROM crash
        WHERE "{vcol}" IS NOT NULL
        GROUP BY vehicle
        ORDER BY cnt DESC
        LIMIT 30
    """).df()
    vehicle_types = sorted(vehicle_types_df["vehicle"].tolist())
else:
    vehicle_types = []

# Person types
person_cols = con.execute("SELECT * FROM person LIMIT 0").df().columns.tolist()
if "PERSON_TYPE" in person_cols:
    person_types_df = con.execute("""
        SELECT DISTINCT PERSON_TYPE
        FROM person
        WHERE PERSON_TYPE IS NOT NULL
        ORDER BY PERSON_TYPE
    """).df()
    person_types = person_types_df["PERSON_TYPE"].tolist()
else:
    person_types = []

# Global counts for header meta
crash_total = con.execute("SELECT COUNT(*) FROM crash").fetchone()[0]
person_total = con.execute("SELECT COUNT(*) FROM person").fetchone()[0]

print("Filter options prepared.")
print(f"  Boroughs: {len(boroughs)}")
print(f"  Years: {len(years)}")
print(f"  Vehicle types: {len(vehicle_types)}")
print(f"  Person types: {len(person_types)}")
print(f"  Crashes: {crash_total:,}")
print(f"  Person records: {person_total:,}")

# =============================================================================
# SQL WHERE BUILDERS (FILTER LOGIC)
# =============================================================================

def build_crash_where(boroughs_sel, years_sel, vehicles_sel):
    clauses = ["1=1"]

    if boroughs_sel and "ALL" not in boroughs_sel:
        b_list = "', '".join(boroughs_sel)
        clauses.append(f"BOROUGH IN ('{b_list}')")

    if years_sel and "ALL" not in years_sel:
        y_list = ", ".join(str(y) for y in years_sel)
        clauses.append(f"year(CAST(\"CRASH DATE\" AS DATE)) IN ({y_list})")

    if vehicles_sel and "ALL" not in vehicles_sel and vehicle_cols:
        v_list = "', '".join(vehicles_sel)
        vcol = vehicle_cols[0]
        clauses.append(f"\"{vcol}\" IN ('{v_list}')")

    return " AND ".join(clauses)


def build_person_where(boroughs_sel, years_sel, persons_sel):
    clauses = ["1=1"]

    if boroughs_sel and "ALL" not in boroughs_sel:
        b_list = "', '".join(boroughs_sel)
        clauses.append(f"BOROUGH IN ('{b_list}')")

    if years_sel and "ALL" not in years_sel:
        y_list = ", ".join(str(y) for y in years_sel)
        clauses.append(f"year(CAST(\"CRASH DATE\" AS DATE)) IN ({y_list})")

    if persons_sel and "ALL" not in persons_sel and "PERSON_TYPE" in person_cols:
        p_list = "', '".join(persons_sel)
        clauses.append(f"PERSON_TYPE IN ('{p_list}')")

    return " AND ".join(clauses)


# =============================================================================
# NATURAL LANGUAGE SEARCH
# =============================================================================

def parse_search_query(query):
    if not query:
        return None, None, None

    q = query.lower()

    borough = next((b for b in boroughs if b and b.lower() in q), None)
    year = next((y for y in years if str(y) in q), None)

    person = None
    if "pedestrian" in q:
        person = [p for p in person_types if "pedestrian" in p.lower()]
    elif "cyclist" in q or "bicyclist" in q:
        person = [p for p in person_types if "cyclist" in p.lower() or "bicyclist" in p.lower()]

    return ([borough] if borough else None,
            [year] if year else None,
            person)


# =============================================================================
# DASH APP SETUP
# =============================================================================

app = dash.Dash(
    __name__,
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
                    children=f"{crash_total:,} crashes · {person_total:,} person records (2015–2025)",
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

# =============================================================================
# CALLBACKS: SEARCH
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

    trigger = ctx.triggered[0]["prop_id"].split(".")[0]

    if trigger == "clear-search-btn":
        return "ALL", "ALL", "ALL"

    borough, year, person = parse_search_query(search_query)
    return (
        borough or current_borough,
        year or current_year,
        person or current_person,
    )

# =============================================================================
# MAIN DASHBOARD CALLBACK (ALL CHARTS)
# =============================================================================

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
    # Normalize list values
    if boroughs_sel == "ALL" or boroughs_sel is None:
        boroughs_sel = ["ALL"]
    elif not isinstance(boroughs_sel, list):
        boroughs_sel = [boroughs_sel]

    if years_sel == "ALL" or years_sel is None:
        years_sel = ["ALL"]
    elif not isinstance(years_sel, list):
        years_sel = [years_sel]

    if vehicles_sel == "ALL" or vehicles_sel is None:
        vehicles_sel = ["ALL"]
    elif not isinstance(vehicles_sel, list):
        vehicles_sel = [vehicles_sel]

    if persons_sel == "ALL" or persons_sel is None:
        persons_sel = ["ALL"]
    elif not isinstance(persons_sel, list):
        persons_sel = [persons_sel]

    # Build WHERE conditions
    where_crash = build_crash_where(boroughs_sel, years_sel, vehicles_sel)
    where_person = build_person_where(boroughs_sel, years_sel, persons_sel)

    # ---------------- SUMMARY STATS ----------------
    summary_row = con.execute(f"""
        SELECT
            COUNT(*) AS total_crashes,
            SUM("NUMBER OF PERSONS INJURED") AS total_injuries,
            SUM("NUMBER OF PERSONS KILLED") AS total_deaths
        FROM crash
        WHERE {where_crash}
    """).fetchone()

    total_crashes = int(summary_row[0] or 0)
    total_injuries = int(summary_row[1] or 0)
    total_deaths = int(summary_row[2] or 0)

    summary = html.Div(
        className="card",
        children=[
            html.Div(
                className="summary-row",
                children=[
                    html.Div(["Total Crashes", f"{total_crashes:,}"]),
                    html.Div(["Injuries", f"{total_injuries:,}"]),
                    html.Div(["Deaths", f"{total_deaths:,}"]),
                ],
            )
        ],
    )

    # ---------------- TEMPORAL CHART ----------------
    temporal_df = con.execute(f"""
        SELECT
            year(CAST("CRASH DATE" AS DATE)) AS YEAR,
            COUNT(*) AS crashes
        FROM crash
        WHERE {where_crash}
        GROUP BY YEAR
        ORDER BY YEAR
    """).df()

    fig_temporal = px.line(
        temporal_df,
        x="YEAR", y="crashes",
        title="Crashes Over Time"
    )

    # ---------------- BOROUGH CHART ----------------
    borough_df = con.execute(f"""
        SELECT
            BOROUGH AS borough,
            COUNT(*) AS crashes
        FROM crash
        WHERE {where_crash}
          AND BOROUGH IS NOT NULL
        GROUP BY BOROUGH
        ORDER BY crashes DESC
    """).df()

    fig_borough = px.bar(
        borough_df,
        x="borough", y="crashes",
        title="Crashes by Borough"
    )

    # ---------------- HOUR CHART ----------------
    hour_df = con.execute(f"""
        SELECT
            EXTRACT(HOUR FROM CAST("CRASH TIME" AS TIME)) AS HOUR,
            COUNT(*) AS crashes
        FROM crash
        WHERE {where_crash}
        GROUP BY HOUR
        ORDER BY HOUR
    """).df()

    fig_hour = px.area(
        hour_df,
        x="HOUR", y="crashes",
        title="Crashes by Hour of Day"
    )

    # ---------------- VICTIM CHART ----------------
    if "PERSON_TYPE" in person_cols:
        victim_df = con.execute(f"""
            SELECT
                PERSON_TYPE,
                COUNT(*) AS cnt
            FROM person
            WHERE {where_person}
            GROUP BY PERSON_TYPE
            ORDER BY cnt DESC
            LIMIT 5
        """).df()

        if not victim_df.empty:
            fig_victim = px.pie(
                victim_df,
                names="PERSON_TYPE",
                values="cnt",
                title="Victim Type Distribution",
            )
        else:
            fig_victim = go.Figure()
    else:
        fig_victim = go.Figure()

    # ---------------- CONTRIBUTING FACTORS ----------------
    factor_cols = [c for c in crash_cols if "CONTRIBUTING FACTOR" in c.upper()]
    if factor_cols:
        fcol = factor_cols[0]
        factors_df = con.execute(f"""
            SELECT
                "{fcol}" AS factor,
                COUNT(*) AS cnt
            FROM crash
            WHERE {where_crash}
              AND "{fcol}" IS NOT NULL
            GROUP BY factor
            ORDER BY cnt DESC
            LIMIT 10
        """).df()

        fig_factors = px.bar(
            factors_df,
            x="cnt", y="factor",
            orientation="h",
            title="Top 10 Contributing Factors",
        )
    else:
        fig_factors = go.Figure()

    # ---------------- VEHICLE TYPES ----------------
    if vehicle_cols:
        vcol = vehicle_cols[0]
        v_df = con.execute(f"""
            SELECT
                "{vcol}" AS vehicle,
                COUNT(*) AS cnt
            FROM crash
            WHERE {where_crash}
              AND "{vcol}" IS NOT NULL
            GROUP BY vehicle
            ORDER BY cnt DESC
            LIMIT 10
        """).df()

        fig_vehicle = px.bar(
            v_df,
            x="vehicle", y="cnt",
            title="Top 10 Vehicle Types",
        )
    else:
        fig_vehicle = go.Figure()

    # ---------------- MAP CHART ----------------
    # Limit rows returned for performance; DuckDB still reads full dataset efficiently.
    map_df = con.execute(f"""
        SELECT
            LATITUDE,
            LONGITUDE,
            BOROUGH,
            "NUMBER OF PERSONS INJURED" AS injured
        FROM crash
        WHERE {where_crash}
          AND LATITUDE IS NOT NULL
          AND LONGITUDE IS NOT NULL
        ORDER BY random()
        LIMIT 2000
    """).df()

    if not map_df.empty:
        fig_map = px.scatter_mapbox(
            map_df,
            lat="LATITUDE",
            lon="LONGITUDE",
            hover_data=["BOROUGH", "injured"],
            zoom=9.5,
            title="Crash Locations Map (sample of up to 2,000 crashes)",
        )
        fig_map.update_layout(mapbox_style="open-street-map")
    else:
        fig_map = go.Figure()

    # ---------------- SEASONAL CHART ----------------
    seasonal_df = con.execute(f"""
        SELECT
            CASE
                WHEN EXTRACT(MONTH FROM CAST("CRASH DATE" AS DATE)) IN (3,4,5) THEN 'Spring'
                WHEN EXTRACT(MONTH FROM CAST("CRASH DATE" AS DATE)) IN (6,7,8) THEN 'Summer'
                WHEN EXTRACT(MONTH FROM CAST("CRASH DATE" AS DATE)) IN (9,10,11) THEN 'Fall'
                WHEN EXTRACT(MONTH FROM CAST("CRASH DATE" AS DATE)) IN (12,1,2) THEN 'Winter'
                ELSE 'Unknown'
            END AS SEASON,
            COUNT(*) AS crashes
        FROM crash
        WHERE {where_crash}
        GROUP BY SEASON
    """).df()

    # enforce order
    season_order = ["Spring", "Summer", "Fall", "Winter", "Unknown"]
    seasonal_df["SEASON"] = pd.Categorical(seasonal_df["SEASON"], categories=season_order, ordered=True)
    seasonal_df = seasonal_df.sort_values("SEASON")

    fig_seasonal = px.bar(
        seasonal_df,
        x="SEASON", y="crashes",
        title="Crashes by Season",
    )

    # ---------------- HEATMAP (HOUR vs WEEKDAY) ----------------
    heat_df = con.execute(f"""
        SELECT
            EXTRACT(HOUR FROM CAST("CRASH TIME" AS TIME)) AS HOUR,
            strftime(CAST("CRASH DATE" AS DATE), '%A') AS WEEKDAY,
            COUNT(*) AS crashes
        FROM crash
        WHERE {where_crash}
        GROUP BY HOUR, WEEKDAY
    """).df()

    weekday_order = [
        "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
    ]
    heat_df["WEEKDAY"] = pd.Categorical(heat_df["WEEKDAY"], categories=weekday_order, ordered=True)
    heat_pivot = (
        heat_df.pivot(index="HOUR", columns="WEEKDAY", values="crashes")
        .fillna(0)
        .reindex(columns=weekday_order)
    )

    fig_heatmap = px.imshow(
        heat_pivot,
        title="Hour vs Day Heatmap",
        labels=dict(x="Day of Week", y="Hour of Day", color="Crashes"),
        aspect="auto",
    )

    # ---------------- AGE HISTOGRAM ----------------
    if "PERSON_AGE" in person_cols:
        # limit rows only on Render to be extra safe, though DuckDB is efficient
        limit_clause = "LIMIT 500000" if ON_RENDER else ""
        age_df = con.execute(f"""
            SELECT PERSON_AGE
            FROM person
            WHERE {where_person}
              AND PERSON_AGE > 0
              AND PERSON_AGE < 120
            {limit_clause}
        """).df()

        if not age_df.empty:
            fig_age = px.histogram(
                age_df,
                x="PERSON_AGE",
                nbins=30,
                title="Age Distribution of Crash Victims",
            )
        else:
            fig_age = go.Figure()
    else:
        fig_age = go.Figure()

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
# RUN APP (LOCAL)
# =============================================================================

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=8050)
