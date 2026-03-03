# pages/about.py
from dash import html, dcc

def page_about():
    return html.Div(
        style={"padding": "24px", "maxWidth": "900px", "margin": "0 auto"},
        children=[

            # Page title
            html.H2(
                "👩‍🔬 About Us",
                style={"marginBottom": "12px", "color": "#203864"}
            ),

            html.P(
                "Developed by the LaPointe Research Group at the University of Guelph.",
                style={"fontSize": "16px", "color": "#444", "marginBottom": "24px"}
            ),

            # ---------------- Principal Investigator Card ----------------
            html.Div(
                style={
                    "background": "#ffffff",
                    "border": "1px solid #e6ecf5",
                    "borderRadius": "14px",
                    "padding": "22px",
                    "marginBottom": "24px",
                    "boxShadow": "0 4px 14px rgba(0,0,0,0.05)"
                },
                children=[

                    html.H3(
                        "Principal Investigator",
                        style={"marginBottom": "6px", "color": "#203864", "fontWeight": "700"}
                    ),

                    html.H4(
                        "Dr. Gisèle LaPointe",
                        style={"marginTop": "0", "marginBottom": "6px", "fontWeight": "600"}
                    ),

                    html.A(
                        "Department of Food Science – University of Guelph",
                        href="https://www.uoguelph.ca/foodscience/people/gisele-lapointe",
                        target="_blank",
                        style={
                            "display": "inline-block",
                            "marginBottom": "16px",
                            "color": "#1a73e8",
                            "fontWeight": "500",
                            "textDecoration": "none"
                        }
                    ),

                    # -------- Collapsible Research Themes --------
                    dcc.Details(
                        open=True,
                        children=[
                            html.Summary(
                                "Key Research Themes: Microorganisms for Gut Health and Food Quality",
                                style={
                                    "fontWeight": "600",
                                    "cursor": "pointer",
                                    "color": "#2b4c7e",
                                    "marginBottom": "10px"
                                }
                            ),

                            html.Ul(
                                [
                                    html.Li("Milk Quality from Farm to Gut"),
                                    html.Li("Microbial Ecology in Food and Feed Systems"),
                                    html.Li("Gut–Health Connections"),
                                    html.Li("Fermentation for Bioactive Compounds and Flavour"),
                                ],
                                style={
                                    "marginTop": "10px",
                                    "paddingLeft": "20px",
                                    "lineHeight": "1.7",
                                    "color": "#444",
                                    "fontSize": "15px"
                                }
                            )
                        ]
                    )
                ]
            ),

            # ---------------- Placeholder for future Research Team ----------------
            html.Div(
                style={
                    "background": "#f8fafc",
                    "border": "1px dashed #cfd8ea",
                    "borderRadius": "14px",
                    "padding": "18px",
                    "color": "#666"
                },
                children=[
                    html.H4("Research Team", style={"marginBottom": "6px"}),
                    html.P(
                        "Information on postdoctoral researchers and their research themes "
                        "will be added here.",
                        style={"fontStyle": "italic"}
                    )
                ]
            )
        ]
    )
