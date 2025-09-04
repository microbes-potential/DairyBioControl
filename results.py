from __future__ import annotations
import math
import pandas as pd
from dash import dcc, html, Input, Output, State
from dash.dash_table import DataTable

from utils.perf import cached_build_detection
from utils.trait_db import get_module_ref_cap  # << NEW realistic denominator

_CARD = {"background":"#fff", "border":"1px solid #e9eef5", "borderRadius":"12px",
         "padding":"16px", "boxShadow":"0 2px 8px rgba(0,0,0,0.04)"}

def _heading(txt:str):
    return html.H3(txt, style={"margin":"0 0 12px","fontWeight":"800"})

def page_results():
    return html.Div([
        html.Div([
            _heading("DairyBioControl — Summary"),
            html.Div(id="results-notice", style={"color":"#a33","marginBottom":"8px"}),

            html.Div([
                html.Div([
                    _heading("Biocontrol Potential"),
                    DataTable(
                        id="indices-table",
                        columns=[{"name":"Metric","id":"Metric"},
                                 {"name":"Score","id":"Score"}],
                        data=[],
                        style_table={"overflowX":"auto"},
                        style_cell={"fontSize":"16px","padding":"10px"},
                        style_header={"background":"#f5f7fb","fontWeight":"700"},
                        style_data_conditional=[
                            {"if":{"filter_query":"{Metric} = 'Biocontrol Potential (0–100)'"}, "backgroundColor":"#f6fff7"},
                        ]
                    ),
                ], style={"flex":"1"}),

                dcc.Loading(
                    id="loading-results-bars",
                    type="circle",
                    color="#8aa7ff",
                    children=html.Div([
                        _heading("Weighted hits"),
                        dcc.Graph(id="benefit-bars", config={"displayModeBar":False}, figure={})
                    ], style={"flex":"1","minWidth":"340px"}),
                ),
            ], style={"display":"grid","gridTemplateColumns":"1fr 1fr","gap":"16px"}),
        ], style=_CARD),
    ], style={"padding":"16px 18px"})

def register_callbacks(app):
    @app.callback(
        Output("indices-table","data"),
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
            return [], {"data":[], "layout":{"height":280, "margin":{"l":40,"r":10,"t":10,"b":40}}}, ""

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
        PPRS = (arg_n**2 + vf_n**2 + ta_n**2) ** 0.5
        gamma = 0.5  # gentler penalty
        PPRI = PPRS / (1.0 + PPRS)

        # Realistic reference cap: sum of top-K gene weights in each module DB
        ref_cap = (
            get_module_ref_cap("DairyAdaptation", 40) +
            get_module_ref_cap("Antibacterial",  30) +
            get_module_ref_cap("Antifungal",     30)
        )
        ref_cap = max(ref_cap, 1e-9)

        benefit_w = S_Dairy_w + S_Abx_w + S_Af_w
        norm_benefit = benefit_w / ref_cap
        biocontrol = 100.0 * norm_benefit / (1.0 + gamma*PPRI)
        biocontrol = max(0.0, min(100.0, biocontrol))

        indices_rows = [{"Metric":"Biocontrol Potential (0–100)", "Score": f"{biocontrol:.2f}"}]

        # Weighted hits bar chart (unchanged structure)
        bars_df = pd.DataFrame({
            "Module": ["Adaptation","Antibacterial","Antifungal"],
            "Weighted hits":  [S_Dairy_w, S_Abx_w, S_Af_w]
        })
        fig = {
            "data":[{"type":"bar","x":bars_df["Module"],"y":bars_df["Weighted hits"],"name":"Weighted hits"}],
            "layout":{"height":280,"margin":{"l":50,"r":10,"t":10,"b":40},"yaxis":{"title":"Weighted hits"}}
        }

        note = "" if (benefit_w + arg_n + vf_n + ta_n) > 0 else \
               "No traits matched. Check gene/product names or upload an annotated GenBank/FASTA."
        return indices_rows, fig, note

