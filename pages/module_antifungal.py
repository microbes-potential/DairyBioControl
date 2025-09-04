# pages/module_antifungal.py
from __future__ import annotations

import pandas as pd
import plotly.express as px
from dash import dcc, html, Input, Output, State, dash_table

from components.common import info_banner
from utils.perf import cached_build_detection

PAGE_KEY = "antifungal"
CATEGORY = "Antifungal"

GRAPH_CONFIG = {
    "displaylogo": False,
    "toImageButtonOptions": {"format":"png","filename":"dairybio_antifungal","height":800,"width":1600,"scale":3},
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
        html.H2("🍄 Antifungal Traits"),
        _view_toggle(),
        html.Div(id=f"{PAGE_KEY}-notice"),
        dcc.Loading(
            id="loading-antifungal",
            type="circle",
            children=dcc.Graph(id=f"{PAGE_KEY}-graph", config=GRAPH_CONFIG),
            color="#8aa7ff",
        ),
        dcc.Loading(
            id="loading-antifungal-table",
            type="circle",
            children=html.Div(id=f"{PAGE_KEY}-table", style={"marginTop":"8px"}),
            color="#8aa7ff",
        ),

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
        allowed = (mode == "full") or (mode == "antifungal")
        if not allowed:
            return _empty_figure(), info_banner("ℹ️ Hidden for current Analysis Mode."), html.Div()

        if status != "ready":
            return _empty_figure(), info_banner("⬆️ Upload a file and click Submit."), html.Div()

        summary, hits = cached_build_detection(CATEGORY, features or [], genome_name=fname or "query")
        total = int(summary["Detected"].sum()) if not summary.empty else 0
        notice = html.Div(f"Detected total: {total} matches across {len(summary)} subcategories.",
                          style={"margin":"4px 0 10px 2px","color":"#456","fontSize":"15px"})

        fig = px.bar(summary if not summary.empty else pd.DataFrame({"Trait":["No traits found"],"Detected":[0]}),
                     x="Trait", y="Detected", color="Trait", title=None)
        fig.update_layout(width=1200, height=620, margin=dict(l=40,r=20,t=10,b=80),
                          plot_bgcolor="white", paper_bgcolor="white")

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
        summary, _ = cached_build_detection(CATEGORY, features or [], genome_name=fname or "query")
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
        _, hits = cached_build_detection(CATEGORY, features or [], genome_name=fname or "query")
        csv = hits.to_csv(index=False)
        return dict(content=csv, filename=f"{(fname or 'results').split('/')[-1]}_{CATEGORY}_hits.csv")

