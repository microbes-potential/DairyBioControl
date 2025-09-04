# pages/module_safety.py
from __future__ import annotations

import pandas as pd
import plotly.express as px
from dash import dcc, html, Input, Output, State, no_update, dash_table

from components.common import info_banner
from utils.trait_db import build_detection_table_and_hits

PAGE_KEY = "safetyscreening"
CATEGORY = "Safety"

GRAPH_CONFIG = {
    "displaylogo": False,
    "toImageButtonOptions": {"format":"png","filename":"dairybio_safety","height":800,"width":1600,"scale":3},
    "modeBarButtonsToRemove": ["select2d","lasso2d","autoScale2d"]
}

def _view_toggle():
    return html.Div([
        dcc.RadioItems(
            id=f"{PAGE_KEY}-view", value="graph",
            options=[{"label":"📊 Graph", "value":"graph"}, {"label":"📋 Table", "value":"table"}],
            labelStyle={"display":"inline-block","marginRight":"16px"}
        )
    ], style={"margin":"6px 0 12px 4px"})

def page_module():
    return html.Div([
        html.H2("🛡️ Safety Screening"),
        _view_toggle(),
        html.Div(id=f"{PAGE_KEY}-notice"),
        dcc.Graph(id=f"{PAGE_KEY}-graph", config=GRAPH_CONFIG),
        html.Div(id=f"{PAGE_KEY}-table", style={"marginTop":"8px"}),

        html.Div([
            html.Button("📥 Download Summary CSV", id=f"download-btn-{PAGE_KEY}", n_clicks=0, style={"marginTop":"12px","marginRight":"8px"}),
            dcc.Download(id=f"download-table-{PAGE_KEY}"),
            html.Button("📥 Download Hits CSV", id=f"download-hits-btn-{PAGE_KEY}", n_clicks=0, style={"marginTop":"12px"}),
            dcc.Download(id=f"download-hits-{PAGE_KEY}")
        ])
    ])

def _empty_figure():
    return px.bar(pd.DataFrame({"Trait":["No data"], "Detected":[0]}), x="Trait", y="Detected")

def register_callbacks(app):
    @app.callback(
        Output(f"{PAGE_KEY}-graph","figure"),
        Output(f"{PAGE_KEY}-notice","children"),
        Output(f"{PAGE_KEY}-table","children"),
        Input("store-features","data"),
        Input("store-analysis-mode","data"),
        Input("store-upload-status","data"),
        Input(f"{PAGE_KEY}-view","value"),
        State("store-filename","data")
    )
    def update_module(features, mode, status, view, fname):
        allowed = (mode == "full") or (mode == "safety")
        if not allowed:
            return _empty_figure(), info_banner("ℹ️ Hidden for current Analysis Mode."), html.Div()

        if status != "ready":
            return _empty_figure(), info_banner("⬆️ Upload a file and click Submit."), html.Div()

        # Build data strictly from Safety DB (ARGs_db.csv, VFs_db.csv, TA_db.csv)
        summary, hits = build_detection_table_and_hits(CATEGORY, features or [], genome_name=fname or "query")
        # Total = unique matches across subcategories, but use the summary number you already show
        total = int(summary["Detected"].sum()) if not summary.empty else 0
        notice = html.Div(f"Detected total: {total} matches across {len(summary)} subcategories.",
                          style={"margin":"4px 0 10px 2px","color":"#456","fontSize":"15px"})

        # Graph
        fig = px.bar(
            summary if not summary.empty else pd.DataFrame({"Trait":["No traits found"],"Detected":[0]}),
            x="Trait", y="Detected", color="Trait", title=None
        )
        fig.update_layout(width=1200, height=620, margin=dict(l=40,r=20,t=10,b=80),
                          plot_bgcolor="white", paper_bgcolor="white")

        # Optional table view
        if view == "table":
            table = dash_table.DataTable(
                columns=[{"name":"Trait","id":"Trait"},{"name":"Detected","id":"Detected"},{"name":"Genes","id":"Genes"}],
                data=summary.to_dict("records"),
                style_cell={"fontSize":"14px","padding":"6px"},
                style_header={"backgroundColor":"#f7f7f7","fontWeight":"700"},
                page_size=20
            )
            return fig, notice, table
        else:
            return fig, notice, html.Div()

    @app.callback(
        Output(f"download-table-{PAGE_KEY}","data"),
        Input(f"download-btn-{PAGE_KEY}","n_clicks"),
        State("store-features","data"),
        State("store-filename","data"),
        prevent_initial_call=True
    )
    def download_summary(n, features, fname):
        summary, _ = build_detection_table_and_hits(CATEGORY, features or [], genome_name=fname or "query")
        csv = summary.to_csv(index=False)
        return dict(content=csv, filename=f"{(fname or 'results').split('/')[-1]}_{CATEGORY}_summary.csv")

    @app.callback(
        Output(f"download-hits-{PAGE_KEY}","data"),
        Input(f"download-hits-btn-{PAGE_KEY}","n_clicks"),
        State("store-features","data"),
        State("store-filename","data"),
        prevent_initial_call=True
    )
    def download_hits(n, features, fname):
        """
        Export ONLY Gene and Product (no tier/weight/kind/category columns),
        per your Safety CSV schemas (ARGs_db.csv, VFs_db.csv, TA_db.csv).
        """
        _, hits = build_detection_table_and_hits(CATEGORY, features or [], genome_name=fname or "query")
        if hits is None or hits.empty:
            simple = pd.DataFrame(columns=["Gene","Product"])
        else:
            # Gene column: only keep the name if the match was by gene; otherwise leave blank
            gene_series = hits.apply(lambda r: r["Hit"] if str(r.get("Kind","")) == "gene" else "", axis=1)
            product_series = hits["Product"].astype(str)
            # De-duplicate identical Gene/Product pairs
            simple = pd.DataFrame({"Gene": gene_series, "Product": product_series}).drop_duplicates()

        csv = simple.to_csv(index=False)
        return dict(content=csv, filename=f"{(fname or 'results').split('/')[-1]}_{CATEGORY}_hits.csv")

