# pages/upload.py
from __future__ import annotations
import hashlib

from dash import dcc, html, Input, Output, State, no_update
from components.common import info_banner
from utils.parsing import (
    parse_contents, is_genbank, is_protein_fasta,
    detect_annotator_from_text, parse_genbank_features, parse_protein_fasta_features
)

_CARD = {"background":"#fff","border":"1px solid #e9eef5","borderRadius":"12px",
         "padding":"16px","boxShadow":"0 2px 8px rgba(0,0,0,0.04)"}

def _progress_bar():
    return html.Div([
        html.Div("Upload / Parse Progress", style={"marginBottom":"4px","fontSize":"13px","color":"#345"}),
        html.Div([html.Div(id="progress-inner", style={
            "height":"10px","width":"0%","background":"linear-gradient(90deg,#7ad,#4bb)",
            "transition":"width 0.18s linear","boxShadow":"inset 0 0 3px rgba(0,0,0,0.3)",
            "borderRadius":"8px"})], style={"width":"100%","height":"10px","background":"#e8eef5",
            "border":"1px solid #cfe0ff","borderRadius":"8px"})
    ], style={"marginTop":"8px"})

def page_upload():
    return html.Div([
        html.Div([
            html.H3("Upload GenBank (PROKKA/PGAP) or Protein FASTA (.faa)"),
            info_banner("You must be logged in and approved to upload."),
            html.Div([
                html.Label("E-mail (optional, for results)"),
                dcc.Input(id="email-input", type="email",
                          placeholder="your.email@example.com",
                          style={"width":"100%","marginBottom":"10px"})
            ]),
            html.Label("Upload GenBank (*.gb/*.gbk/*.gbff/*.genbank) or Protein FASTA (*.faa)"),
            dcc.Upload(
                id="upload-data",
                children=html.Div(['📁 Drag & Drop or ',
                                   html.Button('Browse ...', style={"display":"inline-block","marginLeft":"10px"})]),
                style={'width':'100%','height':'60px','lineHeight':'60px','borderWidth':'1px',
                       'borderStyle':'dashed','borderRadius':'5px','textAlign':'center',
                       'marginBottom':'8px','cursor':'pointer'},
                multiple=False
            ),
            # --- NEW: handy downloadable example right below the uploader ---
            html.Div([
                html.Span("Need a test file? ", style={"marginRight":"6px", "color":"#556"}),
                html.A("Download example GenBank",
                       href="/assets/Example_file.gbk",
                       download="Example_file.gbk",
                       target="_blank",
                       style={
                           "display":"inline-block","padding":"4px 10px","border":"1px solid #cfe0ff",
                           "borderRadius":"6px","textDecoration":"none","background":"#f5f9ff",
                           "color":"#205375","fontWeight":"600"
                       })
            ], style={"marginBottom":"10px"}),
            # ----------------------------------------------------------------
            _progress_bar(),
            html.Div(id='uploaded-filename', style={"color":"green","fontWeight":"bold","marginTop":"10px"}),
        ], style=_CARD),

        # NOTE: Stores are now global in app layout. Do NOT redeclare them here.

        html.Br(),
        html.Div([
            html.H5("🧬 Select Analysis Mode", style={"marginBottom":"10px","fontWeight":"bold"}),
            dcc.RadioItems(
                id='analysis-mode', value='full',
                options=[{'label':'🔍 Full Analysis (All Modules)','value':'full'},
                         {'label':'🧪 Safety Screening','value':'safety'},
                         {'label':'🥛 Dairy Adaptation Traits','value':'dairy'},
                         {'label':'🧫 Antibacterial Traits','value':'antibacterial'},
                         {'label':'🍄 Antifungal Traits','value':'antifungal'}],
                labelStyle={'display':'block','margin':'5px 0'}, style={"marginLeft":"10px"}
            ),
            html.Button("Submit", id="submit-button", n_clicks=0, style={"marginTop":"10px"})
        ], style=_CARD),

        # Friendly guidance note (subtle + italic)
        html.Div(
            "Select a specific module and click Submit to run the job. "
            "The results will be displayed in the corresponding module tabs. "
            "Please be patient if it takes some time.",
            style={
                "marginTop": "10px",
                "color": "#556",
                "fontStyle": "italic",
                "fontSize": "15px"
            }
        ),
    ], style={"padding":"16px 18px"})

def register_callbacks(app):
    @app.callback(Output("store-upload-started","data"),
                  Input("upload-data","contents"),
                  prevent_initial_call=True)
    def mark_upload_started(contents):
        return bool(contents)

    @app.callback(Output("progress-interval","disabled"),
                  Output("store-progress","data"),
                  Input("store-upload-started","data"),
                  Input("store-upload-status","data"),
                  Input("progress-interval","n_intervals"),
                  State("store-progress","data"),
                  prevent_initial_call=True)
    def animate_progress(started, status, ticks, prog):
        if started and status != "ready":
            return False, min(90, (prog or 0)+6)
        if status == "ready":
            return True, 100
        return no_update, min(95, (prog or 0)+2)

    @app.callback(Output("progress-inner","style"), Input("store-progress","data"))
    def set_progress_style(p):
        return {"height":"10px","width":f"{int(p or 0)}%",
                "background":"linear-gradient(90deg,#7ad,#4bb)","transition":"width 0.18s linear",
                "boxShadow":"inset 0 0 3px rgba(0,0,0,0.3)","borderRadius":"8px"}

    @app.callback(Output("store-analysis-mode","data"), Input("analysis-mode","value"))
    def set_mode(mode): return mode or "full"

    @app.callback(Output("uploaded-filename","children"),
                  Output("store-upload-status","data"),
                  Output("store-features","data"),
                  Output("store-email","data"),
                  Output("store-filename","data"),
                  Output("store-filekind","data"),
                  Input("upload-data","contents"),
                  State("upload-data","filename"),
                  State("email-input","value"),
                  State("store-auth","data"),
                  prevent_initial_call=True)
    def handle_upload(contents, filename, email_value, auth):
        if not contents or not filename:
            return "", "idle", [], email_value or "", filename or "", ""
        if not (auth or {}).get("logged_in"):
            return "❌ Please sign in first.", "idle", [], email_value or "", filename, ""
        if not (auth or {}).get("approved"):
            return "❌ Your account is pending admin approval.", "idle", [], email_value or "", filename, ""

        text = parse_contents(contents)
        fname = (filename or "").lower()
        _ = hashlib.md5(text.encode("utf-8","ignore")).hexdigest()

        if is_genbank(fname):
            detected = detect_annotator_from_text(text)
            feats = parse_genbank_features(text)
            kind = f"GenBank ({(detected or 'unknown').upper()})"
        elif is_protein_fasta(fname):
            feats = parse_protein_fasta_features(text)
            kind = "Protein FASTA (.faa)"
        else:
            return "❌ Unsupported file type.", "idle", [], email_value or "", filename, ""

        msg = f"✅ Uploaded File: {filename} — Parsed ~{len(feats)} features [{kind}]"
        return msg, "ready", feats, (email_value or ""), filename, kind

    @app.callback(Output("router","href"),
                  Input("submit-button","n_clicks"),
                  State("store-analysis-mode","data"),
                  prevent_initial_call=True)
    def go_to_selected(n_clicks, mode):
        if not n_clicks: return no_update
        return ("/results" if mode=="full" else
                "/safetyscreening" if mode=="safety" else
                "/dairyadaptation" if mode=="dairy" else
                "/antibacterial" if mode=="antibacterial" else
                "/antifungal")

