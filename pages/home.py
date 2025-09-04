# pages/home.py
from dash import html

def page_home():
    return html.Div([
        # Hero banner
        html.Div(
            style={
                "backgroundImage": "url('/assets/dairybio_home_banner.png')",
                "backgroundSize": "cover",
                "backgroundPosition": "center",
                "padding": "120px 30px 60px 30px",
                "borderRadius": "12px",
                "color": "white",
                "textShadow": "1px 1px 2px #000",
                "marginBottom": "30px",
            },
            children=[
                html.H1(
                    "DairyBioControl",
                    style={
                        "fontSize": "72px",
                        "color": "#00D7F9",
                        "marginTop": "-40px",
                        "marginBottom": "10px",
                        "fontWeight": "bold",
                        "textAlign": "center",
                        "textShadow": "2px 2px 6px rgba(0,0,0,0.4)",
                    },
                ),
                html.H2(
                    "🧬 Screening of Dairy-Relevant Microbial Genomes",
                    style={"fontSize": "36px", "fontWeight": "bold", "textAlign": "center"},
                ),
                html.P(
                    "DairyBioControl is an integrated, next-generation web platform designed to evaluate "
                    "and visualize the safety and functional potential of microbial genomes for dairy biocontrol ",
                    
                    style={
                        "fontSize": "20px",
                        "maxWidth": "960px",
                        "margin": "auto",
                        "textAlign": "center",
                        "marginTop": "20px",
                    },
                ),
            ],
        ),

        # Why it matters
        html.Div(
            [
                html.H2("🧠 Singnificance", style={"marginTop": "10px", "color": "#205375"}),
                html.P(
                    "Microbial biocontrol offers a natural approach to protect dairy products such as "
                    "cheese, yogurt, and kefir from spoilage bacteria and fungi.",
                    style={"fontSize": "18px"},
                ),
                html.P(
                    "Selecting strains with ability to adapt to the dairy environment and with antimicrobial and antifungal traits "
                    "— while ensuring they are free from resistance or virulence markers — is essential for:",
                    style={"fontSize": "18px"},
                ),
                html.Ul(
                    [
                        html.Li("🛡️ Extending shelf life by suppressing spoilage organisms", style={"fontSize": "17px"}),
                        html.Li("🌿 Replacing chemical preservatives with biocontrol microbes", style={"fontSize": "17px"}),
                        html.Li("🧬 Harnessing beneficial microbes as protective cultures", style={"fontSize": "17px"}),
                        html.Li("🚫 Avoiding toxin producers or resistant bacteria", style={"fontSize": "17px"}),
                    ],
                    style={"marginTop": "10px"},
                ),
                html.Hr(style={"margin": "30px 0"}),
                html.P(
                    "Developed by LaPointes Research Group, University of Guelph. ",
                    
                    style={"fontSize": "18px", "fontStyle": "italic"},
                ),
            ],
            style={"padding": "20px 40px", "backgroundColor": "#f9fbfd", "borderRadius": "10px"},
        ),
    ], style={"padding": "16px 18px"})

