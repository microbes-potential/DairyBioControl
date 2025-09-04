from __future__ import annotations

import json, re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set

import pandas as pd

# ---------------- Files ----------------
ASSETS = Path("assets")

# Safety tables (flexible CSV/TSV/Excel headers: Gene/Product)
ARGS_PATH = ASSETS / "ARGs_db.csv"
VFS_PATH  = ASSETS / "VFs_db.csv"
TA_PATH   = ASSETS / "TA_db.csv"

# Benefit modules (CSV with: Gene, Product, Category, optional Tier)
ADAPT_CSV    = ASSETS / "adaptation_db.csv"
ANTIBACT_CSV = ASSETS / "antibacterial_db.csv"
ANTIFUNG_CSV = ASSETS / "antifungal_db.csv"

# ---- Counting / throttling ----
MAX_PER_TRAIT = 150
INTEGER_WEIGHT = 1.0  # every unique hit counts as 1 in the module pages

# ---- Tier weights (used ONLY for Results weighted hits) ----
TIER_WEIGHTS = {"core": 1.0, "supportive": 0.6, "contextual": 0.3}
PRODUCT_MATCH_WEIGHT = 0.5  # if only product matches in benefit modules

# Generic product phrases to ignore
_GENERIC_PRODUCTS = {
    "hypothetical protein","uncharacterized protein","putative protein","predicted protein",
    "membrane protein","integral membrane protein","transport protein","transporter",
    "abc transporter","permease","binding protein","regulatory protein","domain-containing protein",
    "protein","enzyme"
}

# ---------------- String helpers ----------------
def _read_json(p: Path) -> Any:
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except Exception:
        return None

def _norm_str(x: Any) -> str:
    return str(x or "").strip()

def _norm_lower(x: Any) -> str:
    return _norm_str(x).lower()

def _norm_product(s: Any) -> str:
    t = _norm_lower(s)
    t = re.sub(r"[^a-z0-9\s\.\-\/]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t

def _product_is_specific(p: str) -> bool:
    if not p or p in _GENERIC_PRODUCTS:
        return False
    if len(p) < 6:
        return False
    letters = sum(ch.isalpha() for ch in p)
    if letters < 4 or letters / max(1, len(p)) < 0.5:
        return False
    return True

def _to_list(x: Any) -> List[Any]:
    if x is None:
        return []
    if isinstance(x, list):
        return x
    if isinstance(x, (set, tuple)):
        return list(x)
    return [x]

# ---------------- Canonical entry coercer ----------------
def _coerce_entry(any_obj: Any) -> Dict[str, List[str]]:
    out = {"genes": [], "product_keywords": [], "KO": [], "EC": []}
    if any_obj is None:
        return out

    def _finish(genes: List[str], prods: List[str], kos: List[str], ecs: List[str]) -> Dict[str, List[str]]:
        prods_n = []
        for p in prods:
            pn = _norm_product(p)
            if _product_is_specific(pn):
                prods_n.append(pn)
        return {
            "genes": sorted({g for g in genes if g}),
            "product_keywords": sorted({q for q in prods_n if q}),
            "KO": sorted({_norm_str(k) for k in kos if _norm_str(k)}),
            "EC": sorted({_norm_str(e) for e in ecs if _norm_str(e)}),
        }

    # canonical dict?
    if isinstance(any_obj, dict) and any(k in any_obj for k in ("genes","product_keywords","KO","EC")):
        genes = [_norm_lower(g) for g in _to_list(any_obj.get("genes", []))]
        prods = [_norm_product(k) for k in _to_list(any_obj.get("product_keywords", []))]
        kos   = [_norm_str(k) for k in _to_list(any_obj.get("KO", []))]
        ecs   = [_norm_str(k) for k in _to_list(any_obj.get("EC", []))]
        return _finish(genes, prods, kos, ecs)

    # list[str] => genes
    if isinstance(any_obj, list) and all(isinstance(x, str) for x in any_obj):
        return _finish([_norm_lower(x) for x in any_obj], [], [], [])

    # single str => one gene
    if isinstance(any_obj, str):
        s = _norm_str(any_obj)
        return _finish([_norm_lower(s)] if s else [], [], [], [])

    # list[dict]
    if isinstance(any_obj, list) and all(isinstance(x, dict) for x in any_obj):
        genes, prods, kos, ecs = [], [], [], []
        for row in any_obj:
            for gkey in ("gene","Gene","name","Name","symbol","Symbol","locus","locus_tag"):
                if gkey in row and _norm_str(row[gkey]):
                    genes.append(_norm_lower(row[gkey]))
            if isinstance(row.get("genes"), list):
                genes.extend(_norm_lower(g) for g in row["genes"] if _norm_str(g))
            for pkey in ("product","Product","description","Description","function","Function","keyword","keywords"):
                v = row.get(pkey)
                if isinstance(v, str) and _norm_str(v):
                    prods.append(v)
                elif isinstance(v, list):
                    prods.extend(_norm_str(k) for k in v if _norm_str(k))
            for kkey in ("KO","ko"):
                v = row.get(kkey)
                if isinstance(v, str) and _norm_str(v):
                    kos.append(v)
                elif isinstance(v, list):
                    kos.extend(_norm_str(k) for k in v if _norm_str(k))
            for ekey in ("EC","ec","ec_number","EC_number"):
                v = row.get(ekey)
                if isinstance(v, str) and _norm_str(v):
                    ecs.append(v)
                elif isinstance(v, list):
                    ecs.extend(_norm_str(k) for k in v if _norm_str(k))
        return _finish(genes, prods, kos, ecs)

    # other dict shapes
    if isinstance(any_obj, dict):
        genes = any_obj.get("list") or any_obj.get("items") or any_obj.get("Genes") or any_obj.get("GENES")
        if genes:
            return _finish([_norm_lower(g) for g in _to_list(genes)], [], [], [])
        return out

    return out

def _merge_entries(a: Dict[str, List[str]], b: Dict[str, List[str]]) -> Dict[str, List[str]]:
    return {
        "genes":            sorted(set(a.get("genes",[]))            | set(b.get("genes",[]))),
        "product_keywords": sorted(set(a.get("product_keywords",[])) | set(b.get("product_keywords",[]))),
        "KO":               sorted(set(a.get("KO",[]))               | set(b.get("KO",[]))),
        "EC":               sorted(set(a.get("EC",[]))               | set(b.get("EC",[]))),
    }

# ---------------- Robust readers ----------------
def _read_table_auto(path: Path) -> Optional[pd.DataFrame]:
    try:
        if not path.exists():
            for alt in (path.with_suffix(".tsv"), path.with_suffix(".xlsx"), path.with_suffix(".xls")):
                if alt.exists():
                    path = alt
                    break
            else:
                return None
        if path.suffix.lower() in (".xlsx",".xls"):
            df = pd.read_excel(path)
        else:
            df = pd.read_csv(path, sep=None, engine="python", encoding_errors="ignore")
        df.columns = [str(c).strip() for c in df.columns]
        for c in df.columns:
            if pd.api.types.is_string_dtype(df[c]):
                df[c] = df[c].map(lambda x: x.strip() if isinstance(x, str) else x)
        return df
    except Exception:
        return None

def _read_safety_table(path: Path) -> Dict[str, List[str]]:
    df = _read_table_auto(path)
    out = {"genes": [], "product_keywords": [], "KO": [], "EC": []}
    if df is None or df.empty:
        return out
    cols_lower = {c.lower(): c for c in df.columns}
    gene_col = next((cols_lower[k] for k in ("gene","genes","name","symbol") if k in cols_lower), None)
    prod_col = next((cols_lower[k] for k in ("product","description","function") if k in cols_lower), None)

    genes, prods = [], []
    if gene_col:
        genes = [_norm_lower(x) for x in df[gene_col].fillna("").astype(str) if _norm_str(x)]
    if prod_col:
        prods_raw = [_norm_product(x) for x in df[prod_col].fillna("").astype(str) if _norm_str(x)]
        prods = [p for p in prods_raw if _product_is_specific(p)]

    return {"genes": sorted(set(genes)), "product_keywords": sorted(set(prods)), "KO": [], "EC": []}

def _read_benefit_csv(path: Path) -> Optional[pd.DataFrame]:
    df = _read_table_auto(path)
    if df is None:
        return None
    cols_lower = {c.lower(): c for c in df.columns}
    def colget(*names):
        for n in names:
            if n in cols_lower: return cols_lower[n]
        return None
    gc = colget("gene"); pc = colget("product","description","function")
    cc = colget("category"); tc = colget("tier")
    if gc is None: df["Gene"] = ""; gc = "Gene"
    if pc is None: df["Product"] = ""; pc = "Product"
    if cc is None: df["Category"] = ""; cc = "Category"
    if tc is None: df["Tier"] = ""; tc = "Tier"
    df = df.rename(columns={gc:"Gene", pc:"Product", cc:"Category", tc:"Tier"})
    for c in ("Gene","Product","Category","Tier"):
        if pd.api.types.is_string_dtype(df[c]):
            df[c] = df[c].map(lambda x: x.strip() if isinstance(x, str) else x)
    return df

def _build_module_from_csv(csv_path: Path) -> Dict[str, Any]:
    df = _read_benefit_csv(csv_path)
    out: Dict[str, Any] = {"Subcategories": {}, "Cap": 0.0, "CapList": []}
    if df is None or df.empty:
        return out

    cap_total = 0.0
    cap_weights: List[float] = []

    for subcat, g in df.groupby("Category"):
        sub = _norm_str(subcat) or "Misc"

        genes: Set[str] = set()
        keywords: Set[str] = set()
        tiers_map: Dict[str, str] = {}

        for _, row in g.iterrows():
            gene = _norm_lower(row.get("Gene",""))
            prod = _norm_product(row.get("Product",""))
            tier = _norm_lower(row.get("Tier",""))
            if tier not in TIER_WEIGHTS:
                tier = "supportive"
            if gene:
                genes.add(gene)
                tiers_map[gene] = tier
                cap_weights.append(TIER_WEIGHTS[tier])
            if _product_is_specific(prod):
                keywords.add(prod)

        out["Subcategories"][sub] = {
            "genes": sorted(genes),
            "product_keywords": sorted(keywords),
            "KO": [],
            "EC": [],
            "tiers": tiers_map
        }
        cap_total += len(genes)  # integer capacity for module tables

    out["Cap"] = float(cap_total)
    out["CapList"] = sorted(cap_weights, reverse=True)
    return out

# ---------------- Builders ----------------
def _build_safety() -> Dict[str, Any]:
    args_entry = _read_safety_table(ARGS_PATH)
    vfs_entry  = _read_safety_table(VFS_PATH)
    ta_entry   = _read_safety_table(TA_PATH)
    return {"Subcategories": {
        "ARGs":               args_entry,
        "Virulence Factors":  vfs_entry,
        "Toxin-Antitoxin":    ta_entry,
    }}

def _build_adaptation() -> Dict[str, Any]:
    return _build_module_from_csv(ADAPT_CSV)

def _build_antibacterial() -> Dict[str, Any]:
    return _build_module_from_csv(ANTIBACT_CSV)

def _build_antifungal() -> Dict[str, Any]:
    return _build_module_from_csv(ANTIFUNG_CSV)

# ---------------- Public: load DB ----------------
def load_trait_db() -> Dict[str, Any]:
    db: Dict[str, Any] = {}
    db["Safety"]          = _build_safety()
    db["DairyAdaptation"] = _build_adaptation()
    db["Antibacterial"]   = _build_antibacterial()
    db["Antifungal"]      = _build_antifungal()
    return db

# ---------------- Matching utils ----------------
def _get_live_db(TRAIT_DB: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if TRAIT_DB is not None:
        return TRAIT_DB
    try:
        from flask import current_app
        return current_app.config.get("TRAIT_DB", {}) or {}
    except Exception:
        return {}

def get_module_cap(category: str, TRAIT_DB: Optional[Dict[str, Any]] = None) -> float:
    db = _get_live_db(TRAIT_DB)
    try:
        return float((db.get(category) or {}).get("Cap", 0.0))
    except Exception:
        return 0.0

def get_module_ref_cap(category: str, top_k: int = 40, TRAIT_DB: Optional[Dict[str, Any]] = None) -> float:
    """Reference cap = sum of top-K highest gene weights in the module DB."""
    db = _get_live_db(TRAIT_DB)
    try:
        caps = list((db.get(category) or {}).get("CapList", []))
    except Exception:
        caps = []
    if not caps:
        return get_module_cap(category, TRAIT_DB)
    k = max(1, min(int(top_k), len(caps)))
    return float(sum(caps[:k]))

def get_trait_entry(category: str, trait: str, TRAIT_DB: Optional[Dict[str,Any]]=None) -> Dict[str, Any]:
    db = _get_live_db(TRAIT_DB)
    try:
        raw = ((db.get(category, {}) or {}).get("Subcategories", {}) or {}).get(trait)
    except Exception:
        raw = None
    entry = _coerce_entry(raw)
    tiers = {}
    if isinstance(raw, dict) and isinstance(raw.get("tiers"), dict):
        tiers = {str(k).lower(): str(v).lower() for k,v in raw["tiers"].items() if str(k)}
    entry["tiers"] = tiers
    return entry

def match_feature_to_trait(feature: Dict[str, Any], trait_entry: Dict[str, Any], *, is_benefit: bool) -> Tuple[Optional[str], str, float, bool]:
    """
    Returns (disp_name, kind, weight, is_gene)
    Exact-only:
      - prefer exact gene match (case-insensitive)
      - else exact product match (normalized)
    Safety: weight=1.0
    Benefit: gene weight from Tier; product weight=0.5
    """
    gene    = _norm_lower(feature.get("gene",""))
    product = _norm_product(feature.get("product",""))

    genes = trait_entry.get("genes", []) or []
    if gene and gene in genes:
        if is_benefit:
            label = (trait_entry.get("tiers", {}) or {}).get(gene, "supportive")
            w = float(TIER_WEIGHTS.get(label, 0.6))
        else:
            w = 1.0
        return gene, "gene", w, True

    prods = trait_entry.get("product_keywords", []) or []
    if product and product in prods and _product_is_specific(product):
        w = PRODUCT_MATCH_WEIGHT if is_benefit else 1.0
        return product, "product", w, False

    return None, "", 0.0, False

def build_detection_table_and_hits(category: str, features: List[Dict[str, Any]], genome_name: str,
                                   TRAIT_DB: Optional[Dict[str,Any]]=None) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    For module pages:
      - Detected = integer unique count (no decimals)
    For Results:
      - hits Weight carries tier/product weights (benefit only) so weighted sums are possible.
    """
    db = _get_live_db(TRAIT_DB)
    cat_blob = db.get(category, {}) or {}
    subcats = cat_blob.get("Subcategories", {}) or {}
    if isinstance(subcats, list) or not isinstance(subcats, dict):
        subcats = {}

    is_benefit_cat = category in ("DairyAdaptation","Antibacterial","Antifungal")

    rows, hits_rows = [], []

    for trait in sorted(subcats.keys()):
        entry = get_trait_entry(category, trait, db)

        # best weight per unique name; track whether name came from a gene (priority)
        best_weight: Dict[str, float] = {}
        is_gene_name: Dict[str, bool] = {}
        raw_rows: Dict[str, Dict[str, Any]] = {}

        for f in features or []:
            disp, kind, w, is_gene = match_feature_to_trait(f, entry, is_benefit=is_benefit_cat)
            if not disp:
                continue
            # keep the *max* weight for this name
            if w > best_weight.get(disp, 0.0):
                best_weight[disp] = w
                is_gene_name[disp] = is_gene
                raw_rows[disp] = {
                    "Genome": genome_name,
                    "Trait": trait,
                    "Category": category,
                    "Hit": disp,
                    "Product": f.get("product",""),
                    "Kind": kind,
                    "TierLabel": "" if not is_benefit_cat else ("gene" if is_gene else "product"),
                    "Weight": w,
                    "Locus": f.get("locus_tag",""),
                    "Start": f.get("start",0),
                    "End": f.get("end",0),
                    "Strand": f.get("strand",0)
                }

        # apply cap with gene-first priority
        ordered = sorted(best_weight.keys(), key=lambda n: (not is_gene_name.get(n, False), n))
        if len(ordered) > MAX_PER_TRAIT:
            ordered = ordered[:MAX_PER_TRAIT]

        # emit one hit per kept unique name
        for name in ordered:
            hits_rows.append(raw_rows[name])

        detected_int = int(len(ordered))
        rows.append({
            "Trait": trait,
            "Detected": float(detected_int),                 # table compatibility
            "Genes": ", ".join(sorted(ordered))[:2000]
        })

    summary_df = pd.DataFrame(rows).sort_values("Trait").reset_index(drop=True) if rows else \
                 pd.DataFrame({"Trait": [], "Detected": [], "Genes": []})
    hits_df = pd.DataFrame(hits_rows) if hits_rows else pd.DataFrame(
        {"Genome": [], "Trait": [], "Category": [], "Hit": [], "Product": [], "Kind": [],
         "TierLabel": [], "Weight": [], "Locus": [], "Start": [], "End": [], "Strand": []})
    return summary_df, hits_df

# ---- Categories helper ----
ALL_CATEGORIES = ["Safety", "DairyAdaptation", "Antibacterial", "Antifungal"]

def category_trait_map(TRAIT_DB: Optional[Dict[str, Any]] = None) -> Dict[str, List[str]]:
    db = _get_live_db(TRAIT_DB)
    out: Dict[str, List[str]] = {}
    for cat in ALL_CATEGORIES:
        sub = {}
        try:
            sub = (db or {}).get(cat, {}).get("Subcategories", {}) or {}
        except Exception:
            sub = {}
        if isinstance(sub, list):
            out[cat] = ["Misc"]
        elif isinstance(sub, dict):
            out[cat] = sorted(list(sub.keys()))
        else:
            out[cat] = []
    return out

# Back-compat alias
def build_detection_tables(category: str,
                           features: List[Dict[str, Any]],
                           genome_name: str,
                           TRAIT_DB: Optional[Dict[str, Any]] = None):
    return build_detection_table_and_hits(category, features, genome_name, TRAIT_DB)

