# utils/perf.py
from __future__ import annotations

import json
from functools import lru_cache
from typing import Any, Dict, List, Tuple

# lightweight in-memory blob store keyed by a short fingerprint
_blob_cache: Dict[str, List[Dict[str, Any]]] = {}

def _fingerprint_features(features: List[Dict[str, Any]]) -> str:
    """
    Build a short, stable fingerprint from a small slice of the features.
    Avoids hashing the entire file every time while still invalidating cache
    when user uploads a different genome.
    """
    if not features:
        return "empty:0"
    # take at most first/last 50 records and only the most discriminative fields
    head = features[:50]
    tail = features[-50:] if len(features) > 50 else []
    mini = []
    for f in (head + tail):
        mini.append({
            "g": (f.get("gene") or "").lower(),
            "p": (f.get("product") or "").lower(),
            "k": f.get("KO") or "",
            "e": f.get("EC") or "",
            "l": f.get("locus_tag") or ""
        })
    try:
        payload = json.dumps(mini, separators=(",", ":"), ensure_ascii=False)
    except Exception:
        payload = str(mini)
    # a tiny rolling hash
    h = 2166136261
    for ch in payload:
        h ^= ord(ch)
        h = (h * 16777619) & 0xFFFFFFFF
    return f"fp:{h:x}:{len(features)}"

def cached_build_detection(category: str,
                           features: List[Dict[str, Any]],
                           genome_name: str):
    """
    Cached wrapper around trait_db.build_detection_table_and_hits.
    Cache key = (category, genome, fingerprint(features)).
    """
    from utils.trait_db import build_detection_table_and_hits  # lazy import

    fp = _fingerprint_features(features or [])
    _blob_cache[fp] = features or []
    return _cached_core(category, genome_name, fp, build_detection_table_and_hits)

@lru_cache(maxsize=128)
def _cached_core(category: str,
                 genome_name: str,
                 fp: str,
                 _builder) -> Tuple[Any, Any]:
    feats = _blob_cache.get(fp, [])
    return _builder(category, feats, genome_name)

