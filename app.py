import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import base64
import io
import json
import tempfile
import plotly.graph_objects as go
from Bio import SeqIO
from datetime import datetime
from pdf_report_generator import generate_pdf
from trait_detection_score_based import detect_traits_with_score
from parse_antismash_json import parse_antismash_json
from db_utils import init_db, save_report, fetch_recent_reports
from trait_analytics import get_cooccurrence_network
import networkx as nx

with open("dairy_biocontrol_traits.json") as f:
    trait_db = json.load(f)

init_db()

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server
app.title = "DairyBioControl"

category_options = sorted(set(t["category"] for t in trait_db))

detected_data = {}

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H2("DairyBioControl", className="text-primary")),
        dbc.Col(html.Div([
            html.Img(src="/assets/Prof.PNG", style={"height": "50px", "marginRight": "10px", "borderRadius": "50%"}),
            html.Div("LaPointes Research Group", style={"fontSize": "14px", "color": "gray"})
        ], style={"display": "flex", "alignItems": "center", "justifyContent": "flex-end"}),
            style={"marginLeft": "auto", "paddingTop": "18px"})
    ], justify="between", align="center", className="mb-4"),

    dcc.Store(id="trait-store"),
    dcc.Store(id="filename-store"),
    dcc.Store(id="score-store"),

    dbc.Alert("🔬 Predict microbial biocontrol potential from genome files (.gbk, .csv, .json)", color="info"),

    dbc.Row([
        dbc.Col([
            dcc.Upload(
                id="upload-genome",
                children=html.Div(["📂 Drag and drop or click to upload file"]),
                style={
                    "width": "100%", "height": "60px", "lineHeight": "60px", "borderWidth": "1px",
                    "borderStyle": "dashed", "borderRadius": "5px", "textAlign": "center",
                    "marginBottom": "10px"
                },
                multiple=False
            ),
            html.Div(id="file-name", className="text-muted"),
            html.Div(id="upload-error", style={"color": "red"})
        ], width=8),
        dbc.Col([
            html.Label("Filter by Category:"),
            dcc.Checklist(id="trait-category-filter",
                          options=[{"label": cat, "value": cat} for cat in category_options],
                          value=category_options)
        ], width=4)
    ]),

    dbc.Card([
        dbc.CardHeader("🧐 Biocontrol Scores"),
        dbc.CardBody(id="score-bar")
    ], className="mb-4"),

    dbc.Tabs([
        dbc.Tab(label="Trait Matrix", tab_id="matrix"),
        dbc.Tab(label="Trait Co-occurrence", tab_id="cooccur"),
        dbc.Tab(label="Upload History", tab_id="history")
    ], id="tabs", active_tab="matrix", className="mb-3"),

    html.Div(id="tabs-content"),

    dbc.Card([
        dbc.CardHeader("📅 Download Report"),
        dbc.CardBody([
            html.Button("Download PDF Report", id="download-pdf-btn", className="btn btn-outline-danger"),
            dcc.Download(id="download-pdf")
        ])
    ], className="mb-5"),

    html.Footer("\u00a9 2025 DairyBioControl | LaPointes Research Group", style={"textAlign": "center", "color": "gray", "marginTop": "30px"})
], fluid=True, style={"backgroundColor": "white", "padding": "20px"})

@app.callback(
    Output("trait-store", "data"),
    Output("filename-store", "data"),
    Output("score-store", "data"),
    Output("file-name", "children"),
    Output("upload-error", "children"),
    Input("upload-genome", "contents"),
    State("upload-genome", "filename")
)
def process_file(contents, filename):
    if contents is None:
        return dash.no_update, dash.no_update, dash.no_update, "", ""

    try:
        decoded = base64.b64decode(contents.split(",")[1])
        ext = filename.split(".")[-1].lower()
        gene_list = []

        if ext == "csv":
            df = pd.read_csv(io.StringIO(decoded.decode("utf-8")))
            gene_list = df.columns.tolist() + df.get("product", pd.Series()).dropna().tolist()
        elif ext in ["gbk", "gbff"]:
            records = list(SeqIO.parse(io.StringIO(decoded.decode("utf-8")), "genbank"))
            for record in records:
                for feature in record.features:
                    if feature.type == "CDS":
                    gene_list += feature.qualifiers.get("gene", []) + \
                                 feature.qualifiers.get("product", []) + \
                                 feature.qualifiers.get("note", [])
        elif ext == "json":
            gene_list = parse_antismash_json(decoded.decode("utf-8"))

        score, trait_results = detect_traits_with_score(gene_list, trait_db)

        save_report(filename, score, trait_results)

        return trait_results, filename, score, f"✅ Uploaded: {filename}", ""

    except Exception as e:
        return [], "", 0, "", f"❌ Error: {str(e)}"

@app.callback(
    Output("score-bar", "children"),
    Input("score-store", "data")
)
def update_score_bar(score):
    if score is None:
        return ""
    return html.Div([
        dbc.Progress(f"Trait Score: {score}%", value=score, color="info", className="mb-2")
    ])

@app.callback(
    Output("tabs-content", "children"),
    Input("tabs", "active_tab"),
    Input("trait-store", "data"),
    Input("trait-category-filter", "value")
)
def update_tabs(tab, traits, selected_categories):
    if traits is None:
        return ""

    filtered = [t for t in traits if t["category"] in selected_categories]

    if tab == "matrix":
        return html.Div([
            html.Div([
                html.Div(f"{t['trait']} ({t['hits']} hits)", className="p-2", style={
                    "backgroundColor": "#d4edda" if t["status"] == "Detected" else "#f8d7da",
                    "border": "1px solid #ccc",
                    "borderRadius": "8px",
                    "margin": "5px",
                    "display": "inline-block"
                }) for t in filtered
            ])
        ])
    elif tab == "cooccur":
        if len(filtered) < 2:
            return html.Div("Not enough traits to build co-occurrence network.")
        G = get_cooccurrence_network(filtered)
        if len(G.nodes) < 2:
            return html.Div("No trait pairs found.")
        pos = nx.spring_layout(G, seed=42)
        edge_x, edge_y, node_x, node_y, node_text = [], [], [], [], []
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x += [x0, x1, None]
            edge_y += [y0, y1, None]
        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_text.append(node)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=edge_x, y=edge_y, line=dict(width=0.5, color='#888'),
                                 hoverinfo='none', mode='lines'))
        fig.add_trace(go.Scatter(x=node_x, y=node_y, mode='markers+text', text=node_text,
                                 textposition='top center', marker=dict(size=10, color='green')))
        fig.update_layout(title="Trait Co-occurrence Network", showlegend=False, margin=dict(l=10, r=10, t=30, b=10))
        return dcc.Graph(figure=fig)
    elif tab == "history":
        rows = fetch_recent_reports()
        table = dbc.Table([
            html.Thead(html.Tr([html.Th("File"), html.Th("Score"), html.Th("Traits"), html.Th("Time")])),
            html.Tbody([html.Tr([html.Td(r[0]), html.Td(r[1]), html.Td(r[2]), html.Td(r[3])]) for r in rows])
        ], bordered=True, striped=True, hover=True)
        return table
    return ""

@app.callback(
    Output("download-pdf", "data"),
    Input("download-pdf-btn", "n_clicks"),
    State("trait-store", "data"),
    State("score-store", "data"),
    prevent_initial_call=True
)
def download_pdf(n, traits, score):
    if not traits:
        return None
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        generate_pdf(traits, score, tmp.name)
        return dcc.send_file(tmp.name)

if __name__ == "__main__":
    import os
    print("🚀 DairyBioControl is running...")
    app.run_server(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

