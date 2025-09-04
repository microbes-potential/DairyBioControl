from typing import List, Dict, Tuple
import numpy as np
import pandas as pd

TIER_WEIGHTS = {"gene":1.0,"product":0.6,"ko":0.6,"ec":0.6,"context":0.3}

def normalize(s): return (s or "").strip().lower()
def fuzzy_contains_any(text, keywords):
    t = normalize(text); 
    return any((normalize(k) in t) and k for k in keywords)

def get_trait_entry(db, category, trait):
    sub = db.get(category,{}).get("Subcategories",{})
    val = sub.get(trait, [])
    out = {"genes":[],"product_keywords":[],"KO":[],"EC":[]}
    if isinstance(val, list):
        out["genes"] = [str(x) for x in val]
    elif isinstance(val, dict):
        out["genes"] = [str(x) for x in val.get("genes",[])]
        out["product_keywords"] = [str(x) for x in val.get("product_keywords",[])]
        out["KO"] = [str(x) for x in val.get("KO",[])]
        out["EC"] = [str(x) for x in val.get("EC",[])]
    return out

def match_feature_to_trait(feature, entry):
    g = normalize(feature.get("gene")); p = normalize(feature.get("product"))
    ko = feature.get("KO",""); ec = feature.get("EC","")
    genes = [normalize(x) for x in entry.get("genes",[])]
    if g and g in genes: return "gene"
    if p and fuzzy_contains_any(p, entry.get("product_keywords", [])): return "product"
    if ko and ko in entry.get("KO", []): return "ko"
    if ec and any(str(ec).startswith(prefix) for prefix in entry.get("EC", [])): return "ec"
    return None

def build_detection_table_and_hits(db, category, features, genome_name):
    subs = db.get(category,{}).get("Subcategories",{})
    rows=[]; hits=[]
    for trait in sorted(subs.keys()):
        entry = get_trait_entry(db, category, trait)
        matched=set(); count=0
        for f in features:
            tier = match_feature_to_trait(f, entry)
            if not tier: continue
            disp = f.get("gene") or f.get("product") or f.get("KO") or f.get("EC") or ""
            disp = (disp or "").strip()
            if disp: matched.add(disp)
            count+=1
            hits.append({
                "Genome":genome_name,"Trait":trait,"Category":category,
                "Hit":disp,"Product":f.get("product",""),"Tier":tier,
                "LengthAA":len(f.get("translation","") or ""),
                "Locus":f.get("locus_tag",""),"Start":f.get("start",0),
                "End":f.get("end",0),"Strand":f.get("strand",0)
            })
        rows.append({"Trait":trait,"Detected":int(count),"Genes":", ".join(sorted(matched))[:2000]})
    summary = pd.DataFrame(rows) if rows else pd.DataFrame({"Trait":[], "Detected":[], "Genes":[]})
    hitsdf = pd.DataFrame(hits) if hits else pd.DataFrame(
        {"Genome":[], "Trait":[], "Category":[], "Hit":[], "Product":[], "Tier":[],
         "LengthAA":[], "Locus":[], "Start":[], "End":[], "Strand":[]})
    return summary, hitsdf

def compute_ppri_counts(db, features):
    _, hits = build_detection_table_and_hits(db, "Safety", features, "query")
    buckets = {"ARGs":0,"Virulence Factors":0,"Toxins/Enterotoxins":0}
    for _,r in hits.iterrows():
        if r["Trait"] in buckets: buckets[r["Trait"]] += 1
    return {"ARGs": buckets["ARGs"], "VFs": buckets["Virulence Factors"], "PGs": buckets["Toxins/Enterotoxins"]}

def compute_pprs(ppri): 
    x,y,z = ppri.get("ARGs",0), ppri.get("VFs",0), ppri.get("PGs",0)
    return float(np.sqrt(x*x + y*y + z*z))

def norm01(x,k=1.0): return float(1.0 - np.exp(-k*max(0.0,x)))

def compute_evidence_scores(db, features):
    trait_rows=[]; S_by_cat={"DairyAdaptation":0.0,"Antibacterial":0.0,"Antifungal":0.0}
    for cat in list(S_by_cat.keys()):
        sub = db.get(cat,{}).get("Subcategories",{})
        for trait in sub.keys():
            entry = get_trait_entry(db, cat, trait)
            E=0.0
            for f in features:
                tier = match_feature_to_trait(f, entry)
                if tier: E += TIER_WEIGHTS.get(tier,0.3)*1.0
            trait_rows.append({"Trait":trait,"Category":cat,"E_trait":E})
            S_by_cat[cat] += norm01(E, k=0.8)
    trait_df = pd.DataFrame(trait_rows)
    ppri = compute_ppri_counts(db, features)
    risk_raw = ppri["ARGs"] + ppri["VFs"] + ppri["PGs"]
    PPRI_norm = risk_raw/(risk_raw+5.0) if risk_raw>=0 else 0.0
    benefit = sum(S_by_cat.values())
    BPI = benefit/(1.0 + 1.0*PPRI_norm)
    return trait_df, S_by_cat, BPI

def compute_mc_intervals(db, features, n=1000, seed=13):
    rng=np.random.default_rng(seed)
    cats=["DairyAdaptation","Antibacterial","Antifungal"]
    sims={c:[] for c in cats}; sims["BPI"]=[]
    for _ in range(n):
        w = {"gene":rng.uniform(0.9,1.0),"product":rng.uniform(0.5,0.7),
             "ko":rng.uniform(0.5,0.7),"ec":rng.uniform(0.5,0.7),"context":rng.uniform(0.2,0.4)}
        S={}
        for c in cats:
            Sval=0.0
            for trait in (db.get(c,{}).get("Subcategories",{})).keys():
                entry = get_trait_entry(db,c,trait)
                E=0.0
                for f in features:
                    tier = match_feature_to_trait(f,entry)
                    if tier: E += w.get(tier, w["context"])*1.0
                Sval += norm01(E, k=0.8)
            S[c]=Sval
        ppri = compute_ppri_counts(db, features)
        risk_raw = ppri["ARGs"]+ppri["VFs"]+ppri["PGs"]
        PPRI_norm = risk_raw/(risk_raw+5.0) if risk_raw>=0 else 0.0
        sims["BPI"].append(sum(S.values())/(1.0+PPRI_norm))
        for c in cats: sims[c].append(S[c])
    ci={}
    for k,arr in sims.items():
        lo,hi=np.percentile(arr,[2.5,97.5]); ci[k]=(float(lo),float(hi))
    return ci

