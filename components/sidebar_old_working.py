from dash import dcc, html

sidebar_style = {
    "position": "fixed", "top": 0, "left": 0, "bottom": 0,
    "width": "280px", "padding": "20px 14px",
    "background-color": "#f0f4f7", "border-right": "2px solid #d0d7de",
    "overflowY": "auto"
}
content_style = {"margin-left": "300px", "margin-right": "20px", "padding": "20px 30px"}

tabs = [
    "Home","Documentation","Login","Upload","Safety Screening",
    "Dairy Adaptation","Antibacterial","Antifungal","Results",
    "About Us","Contact","Cite"
]

def sidebar():
    return html.Div([
        html.H2("🧬 DairyBioControl", style={"marginBottom": "30px"}),
        dcc.Location(id="url"),
        dcc.Location(id="router", refresh=False),  # used to jump after Submit
        html.Nav([
            dcc.Link(tab, href=f"/{tab.replace(' ','').lower()}",
                     style={"display":"block","margin":"10px 0","fontWeight":"600","color":"#222","textDecoration":"none"})
            for tab in tabs
        ]),
        # Global stores
        dcc.Store(id="store-features", data=[]),
        dcc.Store(id="store-upload-status", data="idle"),
        dcc.Store(id="store-upload-started", data=False),
        dcc.Store(id="store-analysis-mode", data="full"),
        dcc.Store(id="store-email", data=""),
        dcc.Store(id="store-filename", data=""),
        dcc.Store(id="store-filekind", data=""),
        dcc.Store(id="store-auth", data={"logged_in": False, "approved": False, "email": "", "name": "", "role": "user"}),
        dcc.Store(id="store-progress", data=0),
        dcc.Interval(id="progress-interval", interval=180, n_intervals=0, disabled=True),
    ], style=sidebar_style)

