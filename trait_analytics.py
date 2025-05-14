
import pandas as pd
import networkx as nx

def get_cooccurrence_network(trait_results):
    traits = [t['trait'] for t in trait_results if t['status'] == 'Detected']
    pairs = [(traits[i], traits[j]) for i in range(len(traits)) for j in range(i + 1, len(traits))]
    G = nx.Graph()
    for a, b in pairs:
        if G.has_edge(a, b):
            G[a][b]['weight'] += 1
        else:
            G.add_edge(a, b, weight=1)
    return G

    detected_traits = [t for t in trait_results if t['status'] == 'Detected']
    categories = list(set(t['category'] for t in detected_traits))
    score = len(detected_traits) * 5 + len(categories) * 10
    return min(score, 100)
