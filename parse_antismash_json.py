
import json

def parse_antismash_json(decoded_str):
    try:
        data = json.loads(decoded_str)
        traits = []
        if "records" in data:
            for record in data["records"]:
                for cluster in record.get("clusters", []):
                    product = cluster.get("product", "")
                    if product:
                        traits.append(product)
        elif "clusters" in data:
            for cluster in data["clusters"]:
                product = cluster.get("product", "")
                if product:
                    traits.append(product)
        return traits
    except Exception as e:
        print("Error parsing antiSMASH JSON:", e)
        return []
