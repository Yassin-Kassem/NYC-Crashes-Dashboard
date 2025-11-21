"""
NYC Motor Vehicle Collisions Dashboard
Commit 2 — App Initialization & Layout
"""

import dash
from dash import dcc, html

# Reuse data & variables from Commit 1
# Assumes df_crash, df_person, boroughs, years, vehicle_types, person_types
# are already defined/imported somewhere else in your project.

# =============================================================================
# INITIALIZE APP
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

        html.Div(
            "NYC Motor Vehicle Collisions Dashboard · GIU 2025",
            className="footer-text",
        ),
    ],
)

if __name__ == "__main__":
    app.run_server(debug=True)
