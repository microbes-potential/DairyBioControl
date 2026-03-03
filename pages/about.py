from dash import html

def page_about():
    return html.Div([
        html.H2("👩‍🔬 About Us"),
        html.P("Developed by LaPointe Research Group, University of Guelph."),

        html.H4("Principal Investigator"),
        html.P("Gisèle LaPointe"),
        html.P("Department Web site:"),
        html.A(
            "https://www.uoguelph.ca/foodscience/people/gisele-lapointe",
            href="https://www.uoguelph.ca/foodscience/people/gisele-lapointe",
            target="_blank"
        )
    ])
