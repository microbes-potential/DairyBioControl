# pages/module_common.py
from __future__ import annotations
from typing import Dict, Any, List, Tuple

import pandas as pd
import plotly.express as px
from dash import dcc, html, Input, Output, State, no_update
from dash import dash_table

from utils.trait_db import build_detection_tables

GRAPH_CONFIG = {
    "displaylogo": False,
    "toImageButtonOptions": {"format":"png","filename":"dairybio_module","height":800,"width":1600,"scale":3},
    "modeBarButtonsToRemove": ["select2d","lasso2d","autoScale2d"]
}

def module_layout(page_key: str, title: str) -> html.Div:
    return html.Div([
        html.H2(title),
        html.Div([
            dcc.RadioItems(
                id=f"{page_key}-view", value="graph",
                options=[{"label":"📊 Graph", "value":"graph"}, {"label":"📋 Table", "value":"table"}],
                labelStyle={"display":"inline-block","marginRight":"16px"}
            )
        ], style={"margin":"6px 0 12px 4px"}),

        html.Div(id=f"{page_key}-notice", style={"margin":"6px 0 12px", "color":"#345"}),
        dcc.Graph(id=f"{page_key}-graph", config=GRAPH_CONFIG),
        html.Div(id=f"{page_key}-table", style={"marginTop":"8px"}),

        html.Div([
            html.Button("📥 Download Summary CSV", id=f"download-btn-{page_key}", n_clicks=0, style={"marginTop":"12px","marginRight":"8px"}),
            dcc.Download(id=f"download-table-{page_key}"),
            html.Button("📥 Download Hits CSV", id=f"download-hits-btn-{page_key}", n_clicks=0, style={"marginTop":"12px"}),
            dcc.Download(id=f"download-hits-{page_key}")
        ])
    ])

def _bar(summary: pd.DataFrame, palette: List[str] | None = None):
    if summary.empty:
        summary = pd.DataFrame({"Trait": ["No traits found"], "Detected": [0]})
    fig = px.bar(summary, x="Trait", y="Detected", color="Trait",
                 labels={"Trait":"Trait","Detected":"Detected Count"},
                 color_discrete_sequence=palette or px.colors.qualitative.Set2)
    fig.update_layout(width=1200, height=620, margin=dict(l=40,r=20,t=10,b=80),
                      plot_bgcolor="white", paper_bgcolor="white",
                      xaxis=dict(title_font=dict(size=16), tickfont=dict(size=13), showgrid=True, gridcolor="rgba(0,0,0,0.07)"),
                      yaxis=dict(title_font=dict(size=16), tickfont=dict(size=13), showgrid=True, gridcolor="rgba(0,0,0,0.07)"),
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, font=dict(size=12)), title=None)
    fig.update_traces(marker_line_width=0.8, marker_line_color="rgba(0,0,0,0.3)")
    return fig

def register_callbacks(app, *, page_key: str, category: str, flatten_safety: bool = False, palette: List[str] | None = None):
    @app.callback(
        Output(f"{page_key}-graph","figure"),
        Output(f"{page_key}-notice","children"),
        Output(f"{page_key}-table","children"),
        Input("store-features","data"),
        Input("store-upload-status","data"),
        Input(f"{page_key}-view","value"),
        State("store-filename","data"),
        prevent_initial_call=False  # so page shows something right away
    )
    def update_module(features: List[Dict[str, Any]], status: str, view: str, fname: str):
        try:
            trait_db = app.server.config.get("TRAIT_DB", {}) or {}

            if status != "ready":
                empty = pd.DataFrame({"Trait": [], "Detected": []})
                return _bar(empty, palette), "⬆️ Upload a file and click Submit.", html.Div()

            summary, hits = build_detection_tables(trait_db, category, features or [], genome_name=fname or "query", flatten_safety=flatten_safety)
            fig = _bar(summary.rename(columns={"Detected":"Detected"}), palette)
            total = int(summary["Detected"].sum()) if not summary.empty else 0
            notice = f"Detected total: {total} matches across {len(summary)} traits."

            if view == "table":
                tbl = dash_table.DataTable(
                    columns=[{"name":c, "id":c} for c in summary.columns],
                    data=summary.to_dict("records"),
                    page_size=15,
                    style_cell={"fontSize":"14px","padding":"6px","whiteSpace":"normal","height":"auto"},
                    style_header={"backgroundColor":"#f7f7f7","fontWeight":"700"},
                )
                tbl2 = dash_table.DataTable(
                    columns=[{"name":c, "id":c} for c in hits.columns],
                    data=hits.to_dict("records"),
                    page_size=12,
                    style_cell={"fontSize":"13px","padding":"5px","whiteSpace":"normal","height":"auto"},
                    style_header={"backgroundColor":"#f7f7f7","fontWeight":"700"},
                )
                return fig, notice, html.Div([html.H4("Summary"), tbl, html.H4("Hits"), tbl2])
            else:
                return fig, notice, html.Div()

        except Exception as e:
            empty = pd.DataFrame({"Trait": [], "Detected": []})
            return _bar(empty, palette), f"⚠️ Error rendering module: {e}", html.Div()

    # CSV downloads
    @app.callback(
        Output(f"download-table-{page_key}", "data"),
        Input(f"download-btn-{page_key}", "n_clicks"),
        State("store-features","data"),
        State("store-filename","data"),
        prevent_initial_call=True
    )
    def dl_summary(n, features, fname):
        if not n: return no_update
        trait_db = app.server.config.get("TRAIT_DB", {}) or {}
        summary, _ = build_detection_tables(trait_db, category, features or [], genome_name=fname or "query", flatten_safety=flatten_safety)
        return dcc.send_data_frame(summary.to_csv, f"{page_key}_summary.csv", index=False)

    @app.callback(
        Output(f"download-hits-{page_key}", "data"),
        Input(f"download-hits-btn-{page_key}", "n_clicks"),
        State("store-features","data"),
        State("store-filename","data"),
        prevent_initial_call=True
    )
    def dl_hits(n, features, fname):
        if not n: return no_update
        trait_db = app.server.config.get("TRAIT_DB", {}) or {}
        _, hits = build_detection_tables(trait_db, category, features or [], genome_name=fname or "query", flatten_safety=flatten_safety)
        return dcc.send_data_frame(hits.to_csv, f"{page_key}_hits.csv", index=False)

