# pages/results.py
from __future__ import annotations
import math
import pandas as pd
from dash import dcc, html, Input, Output, State
from dash.dash_table import DataTable
import plotly.graph_objects as go  # for the dial

from utils.perf import cached_build_detection
from utils.trait_db import get_module_ref_cap  # realistic denominator

_CARD = {"background":"#fff", "border":"1px solid #e9eef5", "borderRadius":"12px",
         "padding":"16px", "boxShadow":"0 2px 8px rgba(0,0,0,0.04)"}

def _heading(txt:str):
    return html.H3(txt, style={"margin":"0 0 12px","fontWeight":"800"})

def _empty_bar_figure():
    return {"data":[], "layout":{"height":280, "margin":{"l":40,"r":10,"t":10,"b":40}}}

def _dial_figure(score: float) -> go.Figure:
    s = max(0.0, min(100.0, float(score)))
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=s,
            number={"suffix":" / 100", "font":{"size":32}},
            title={"text":"Genome Suitability (0–100)", "font":{"size":20}},
            gauge={
                "axis": {"range":[0,100], "tickwidth":1, "tickcolor":"#b8c1d1"},
                "bar": {"color":"#3c7df0"},
                "bgcolor": "white",
                "borderwidth": 1,
                "bordercolor": "#e6eef7",
                "steps": [
                    {"range":[0,30],  "color":"#ffe5e5"},
                    {"range":[30,60], "color":"#fff6d9"},
                    {"range":[60,100],"color":"#e8f7e9"},
                ],
                "threshold": {
                    "line": {"color": "#2f5bd2", "width": 4},
                    "thickness": 0.8,
                    "value": s
                },
            },
            domain={"x":[0,1], "y":[0,1]},
        )
    )
    fig.update_layout(
        margin=dict(l=20, r=20, t=30, b=20),
        paper_bgcolor="white",
        height=380,   # <-- bigger dial
    )
    return fig

def page_results():
    return html.Div([
        html.Div([
            _heading("DairyBioControl — Summary"),
            html.Div(id="results-notice", style={"color":"#a33","marginBottom":"8px"}),

            # TOP: Big dial
            dcc.Loading(
                id="loading-results-dial",
                type="circle",
                color="#8aa7ff",
                children=html.Div([
                    _heading("Genome Suitability"),
                    dcc.Graph(id="biocontrol-dial", config={"displayModeBar":False}, figure=_dial_figure(0.0))
                ], style={"minWidth":"320px"}),
            ),

            # BOTTOM: Weighted hits bars
            dcc.Loading(
                id="loading-results-bars",
                type="circle",
                color="#8aa7ff",
                children=html.Div([
                    _heading("Weighted hits"),
                    dcc.Graph(id="benefit-bars", config={"displayModeBar":False}, figure={})
                ], style={"minWidth":"340px", "marginTop":"12px"}),
            ),
        ], style=_CARD),
    ], style={"padding":"16px 18px"})

def register_callbacks(app):
    @app.callback(
        Output("biocontrol-dial","figure"),
        Output("benefit-bars","figure"),
        Output("results-notice","children"),
        Input("store-features","data"),
        State("store-filename","data"),
        prevent_initial_call=False
    )
    def compute_indices(features, fname):
        feats = features or []
        genome = fname or "query"

        if not feats:
            return _dial_figure(0.0), _empty_bar_figure(), ""

        # benefit modules (weighted) — cached
        d_sum, d_hits = cached_build_detection("DairyAdaptation", feats, genome)
        a_sum, a_hits = cached_build_detection("Antibacterial",  feats, genome)
        f_sum, f_hits = cached_build_detection("Antifungal",     feats, genome)

        S_Dairy_w = float(d_hits["Weight"].sum()) if not d_hits.empty else 0.0
        S_Abx_w   = float(a_hits["Weight"].sum()) if not a_hits.empty else 0.0
        S_Af_w    = float(f_hits["Weight"].sum()) if not f_hits.empty else 0.0

        # Safety → risk (counts) — cached
        s_sum, s_hits = cached_build_detection("Safety", feats, genome)
        arg_n = vf_n = ta_n = 0
        if not s_hits.empty:
            grp = s_hits.groupby("Trait")["Hit"].nunique().to_dict()
            arg_n = int(grp.get("ARGs", 0))
            vf_n  = int(grp.get("Virulence Factors", 0))
            ta_n  = int(grp.get("Toxin-Antitoxin", 0))

        # Risk indices
        PPRS  = (arg_n**2 + vf_n**2 + ta_n**2) ** 0.5
        gamma = 0.5  # gentler penalty
        PPRI  = PPRS / (1.0 + PPRS)

        # Realistic reference cap
        ref_cap = (
            get_module_ref_cap("DairyAdaptation", 40) +
            get_module_ref_cap("Antibacterial",  30) +
            get_module_ref_cap("Antifungal",     30)
        )
        ref_cap = max(ref_cap, 1e-9)

        benefit_w    = S_Dairy_w + S_Abx_w + S_Af_w
        norm_benefit = benefit_w / ref_cap
        biocontrol   = 100.0 * norm_benefit / (1.0 + gamma * PPRI)
        biocontrol   = max(0.0, min(100.0, biocontrol))

        # Build dial
        dial_fig = _dial_figure(biocontrol)

        # Weighted hits bar chart (unchanged structure)
        bars_df = pd.DataFrame({
            "Module": ["Adaptation","Antibacterial","Antifungal"],
            "Weighted hits":  [S_Dairy_w, S_Abx_w, S_Af_w]
        })
        bars_fig = {
            "data":[{"type":"bar","x":bars_df["Module"],"y":bars_df["Weighted hits"],"name":"Weighted hits"}],
            "layout":{"height":300,"margin":{"l":50,"r":10,"t":10,"b":40},"yaxis":{"title":"Weighted hits"}}
        }

        note = "" if (benefit_w + arg_n + vf_n + ta_n) > 0 else \
               "No traits matched. Check gene/product names or upload an annotated GenBank/FASTA."

        return dial_fig, bars_fig, note
