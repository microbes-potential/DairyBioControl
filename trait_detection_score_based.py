
import re

def detect_traits_with_score(gene_annotations, trait_db, max_hits_per_trait=3):
    clean_genes = [str(g).lower().strip() for g in gene_annotations if g and isinstance(g, str)]
    trait_results = []
    total_score = 0
    max_score = len(trait_db) * max_hits_per_trait

    for trait in trait_db:
        hit_count = 0
        all_keywords = [kw.lower() for kw in (trait["keywords"] + trait["reference_genes"])]
        for keyword in all_keywords:
            for gene in clean_genes:
                if keyword in gene:
                    hit_count += 1
        trait_score = min(hit_count, max_hits_per_trait)
        total_score += trait_score

        trait_results.append({
            "category": trait["category"],
            "trait": trait["trait"],
            "hits": hit_count,
            "score": trait_score,
            "status": "Detected" if hit_count > 0 else "Not Detected"
        })

    biocontrol_score = round((total_score / max_score) * 100)
    return biocontrol_score, trait_results
