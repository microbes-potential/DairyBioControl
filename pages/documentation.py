# pages/documentation.py
from __future__ import annotations
from dash import html, dcc

# ---------- Small style helpers ----------
_CARD = {
    "background": "#fff",
    "border": "1px solid #e9eef5",
    "borderRadius": "12px",
    "padding": "16px",
    "boxShadow": "0 2px 8px rgba(0,0,0,0.04)",
    "marginBottom": "16px",
}

def _h2(txt): return html.H2(txt, style={"margin": "14px 0 8px", "color": "#243a73"})
def _h3(txt): return html.H3(txt, style={"margin": "10px 0 6px", "color": "#2a446e"})
def _p(txt):  return html.P(txt,  style={"margin": "6px 0", "fontSize": "16px", "color": "#333"})

# ---------- Page ----------
def page_documentation():
    return html.Div([
        # Title card
        html.Div([
            html.H1("Documentation", style={"margin":"0 0 6px", "fontWeight":"800", "color":"#1e3163"}),
            _p("DairyBioControl integrates genome annotation parsing, trait detection, safety screening, and a "
               "penalized scoring system to evaluate microbial genomes for dairy and biocontrol potential.")
        ], style=_CARD),

        # Overview + flow image
        html.Div([
            _h2("1. Overview"),
            _p("Upload an annotated GenBank file (PGAP/PROKKA) or a protein FASTA (.faa). The app extracts genes/product sequences, "
               "detects curated traits across modules, screens safety markers, and computes a final "
               "biocontrol potential score that balances benefit vs. risk."),
            html.Div([
                html.Img(
                    src="/assets/flow_figure.png",
                    alt="Analysis flow diagram",
                    style={
                        "maxWidth": "520px",
                        "height": "auto",
                        "display": "block",
                        "margin": "8px auto",
                        "border": "1px solid #e6eef7",
                        "borderRadius": "10px",
                    },
                ),
            ], style={"display": "grid", "gridTemplateColumns": "1.2fr 1fr", "gap": "14px", "alignItems": "center"}),
        ], style=_CARD),

        # Inputs
        html.Div([
            _h2("2. Inputs"),
            _h3("Supported formats"),
            html.Ul([
                html.Li("GenBank: *.gb, *.gbk, *.gbff, *.genbank (PGAP/PROKKA preferred)"),
                html.Li("Protein FASTA: *.faa"),
            ], style={"margin":"6px 0 12px 18px"}),

            _h3("Tips for best results"),
            html.Ul([
                html.Li("Use annotated genomes (PGAP or PROKKA) to maximize matches."),
            ], style={"margin":"0 0 6px 18px"}),
        ], style=_CARD),

        # Modules (Safety, Dairy+Probiotic, Antibacterial, Antifungal)
        html.Div([
            _h2("3. Trait Modules"),
            _p("Each module is built from curated gene/product sets and their representative sequences."),
            html.Div([
                _h3("3.1 Safety Screening"),
                _p("Screens for potential risks using curated lists:"),
                html.Ul([
                    html.Li("ARGs: Antibiotic resistance genes"),
                    html.Li("Virulence factors"),
                    html.Li("Toxin–Antitoxin systems (TA)"),
                ], style={"margin":"6px 0 6px 18px"}),
                _p("Outputs a per-subcategory count of unique matched genes."),
            ], style={"marginBottom":"10px"}),

            html.Div([
                _h3("3.2 Dairy Adaptation"),
                _p("Detects dairy-relevant physiology and probiotic-like features, e.g.:"),
                html.Ul([
                    html.Li("Acid, cold and salt tolerance; lactose metabolism"),
                    html.Li("Proteolysis & lipolysis; adhesion, EPS and biofilm components"),
                    html.Li("Bile salt resistance; immunomodulators/antioxidants"),
                ], style={"margin":"6px 0 6px 18px"}),
            ], style={"marginBottom":"10px"}),

            html.Div([
                _h3("3.3 Antibacterial (biocontrol against bacteria)"),
                _p("Curated antibacterial mechanisms (e.g., bacteriocins, iron/nutrient competition, phage/immunity systems, "
                   "and secretion systems)."),
            ], style={"marginBottom":"10px"}),

            html.Div([
                _h3("3.4 Antifungal (biocontrol against fungi)"),
                _p("Curated antifungal determinants (e.g., lipopeptide clusters such as iturin/fengycin/surfactin, "
                   "chitinase/glucanase enzymes, siderophores, antifungal volatiles)."),
            ]),
        ], style=_CARD),

        # Outputs
        html.Div([
            _h2("5. Outputs"),
            _h3("5.1 On-screen"),
            html.Ul([
                html.Li("Bar graphs: counts per subcategory (modules) + weighted-hits chart in Results."),
                html.Li("Tables: trait summaries (counts + representative names) and detailed hit tables."),
            ], style={"margin":"6px 0 6px 18px"}),
            _h3("5.2 Downloads"),
            html.Ul([
                html.Li("Summary CSV — per module: subcategory, Detected, concatenated genes."),
                html.Li("Hits CSV — detailed records: hit name, product, locus, coordinates, match kind."),
            ], style={"margin":"6px 0 6px 18px"}),
        ], style=_CARD),

        # Results & Scoring (blue box + dial)
        html.Div([
            _h2("6. Results & Scoring"),

            # Equation / method box (styled, clarified & sequential)
            html.Div(
                [
                    html.Div(
                        "How the score is computed",
                        style={
                            "fontWeight": 800,
                            "marginBottom": "6px",
                            "color": "#243a73",
                        },
                    ),
                    html.Pre(
                        """
Symbols
  E_trait = Evidence for one subcategory (trait)
  h = A unique hit (gene) within that subcategory
  w_h = Tier weight for hit h  (core = 1.0; supportive = 0.6)  
  S_module = Benefit score for a module (Dairy / Antibacterial / Antifungal)
  ARGs,VFs,TAs = Counts of safety hits (antibiotic resistance, virulence, toxin–antitoxin)
  PRS = Pothogenecity Risk Score (Raw safety magnitude); PRI = Pothogenecity Risk Index (normalized safety penalty, 0..1)
  γ = Penalty strength (default 1.0)
  C = Capacity (total curated unique genes across benefit modules)

A) Per-trait evidence (unique hits per subcategory)
  E_trait = Σ_{h ∈ hits} w_h
    • Duplicates are de-duplicated by gene name. 

B) Per-module benefit (sum of all traits in the module)
  S_module = Σ_traits E_trait

C) Safety penalty (from the Safety module)
  PRS = √( ARGs^2 + VFs^2 + TAs^2 )
  PRI = PRS / (1 + PRS)        

D) Composite Biocontrol Potential (0..100)
  benefit   = S_Dairy + S_Antibacterial + S_Antifungal
  capacity  = C  (curated maximum possible benefit if everything were present)
  Biocontrol% = 100 × (benefit / capacity) ÷ (1 + γ·PRI)
                        """.strip("\n"),
                        style={
                            "background": "#f3f7ff",
                            "border": "1px solid #e2ecff",
                            "borderLeft": "6px solid #8aa7ff",
                            "padding": "12px 14px",
                            "borderRadius": "8px",
                            "whiteSpace": "pre-wrap",
                            "fontFamily": "ui-monospace, SFMono-Regular, Menlo, monospace",
                            "fontSize": "14px",
                            "lineHeight": "1.55",
                        },
                    ),
                    _p(
                        "Results tables group hits by tier for readability. Only two tiers are shown in the UI: "
                        "“core” (highly informative) and “supportive” (complementary)."
                    ),
                ],
                style={"marginBottom": "12px"},
            ),

            # Dial image on the right
            html.Div(
                [
                    html.Div(
                        [
                            _h3("Interpreting the dial"),
                            _p(
                                "Higher scores indicate more detected benefit (normalized by what’s theoretically "
                                "possible in the databases) and fewer safety risks. Because both the benefit and "
                                "the penalty are normalized, different genomes can be compared directly."
                            ),
                        ],
                        style={"flex": "1", "minWidth": "260px"},
                    ),
                    html.Img(
                        src="/assets/scoring_dial.png",
                        alt="Scoring dial",
                        style={
                            "maxWidth": "320px",
                            "height": "auto",
                            "display": "block",
                            "margin": "8px auto",
                            "border": "1px solid #e6eef7",
                            "borderRadius": "10px",
                        },
                    ),
                ],
                style={
                    "display": "grid",
                    "gridTemplateColumns": "1.2fr 0.8fr",
                    "gap": "14px",
                    "alignItems": "center",
                },
            ),
        ], style=_CARD),

        # FAQ / Notes
        html.Div([
            _h2("7. Notes & FAQ"),

            html.Details([
                html.Summary("Why is the final score sometimes low?"),
                _p("The final score is normalized by the total capacity of curated databases and penalized by the "
                   "safety risk index (PRI). A genome with few detected benefit markers or many safety markers will "
                   "score lower by design. This keeps comparisons fair across genomes."),
            ], open=False, style={"margin":"6px 0"}),

            html.Details([
                html.Summary("Can I export all tables?"),
                _p("Yes. Each module provides CSV downloads for both the summary and the detailed hits."),
            ], open=False, style={"margin":"6px 0"}),
        ], style=_CARD),

        html.Div(style={"height":"10px"})  # small bottom spacer
    ], style={"padding": "16px 18px"})

