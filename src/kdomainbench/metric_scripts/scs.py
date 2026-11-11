"""Spatial coherence score (SCS) for one clustering result.

Usage: python3 metric/scs.py <dataset.h5ad> <cluster_results.csv> <scs.csv>

The PASTE section is copied unchanged from the authors' code (Zeira et al.,
Nature Methods 2022), cell "Calculate spatial coherence score" of
https://github.com/raphael-group/paste_reproducibility/blob/53e27aed07f2c000920d5cf38cd1a6b9d712fead/notebooks/visium-scc-analysis.ipynb
The score is the absolute value of its Z-score, as the authors report it.
"""
import math
import sys
import warnings
from pathlib import Path

import anndata
import numpy as np
import pandas as pd

# ----- PASTE, copied unchanged -----
import networkx as nx
from scipy.spatial import distance_matrix
import random

def create_graph(adata, degree = 4):
        """
        Converts spatial coordinates into graph using networkx library.
        
        param: adata - ST Slice 
        param: degree - number of edges per vertex

        return: 1) G - networkx graph
                2) node_dict - dictionary mapping nodes to spots
        """
        D = distance_matrix(adata.obsm['spatial'], adata.obsm['spatial'])
        # Get column indexes of the degree+1 lowest values per row
        idx = np.argsort(D, 1)[:, 0:degree+1]
        # Remove first column since it results in self loops
        idx = idx[:, 1:]

        G = nx.Graph()
        for r in range(len(idx)):
            for c in idx[r]:
                G.add_edge(r, c)

        node_dict = dict(zip(range(adata.shape[0]), adata.obs.index))
        return G, node_dict
    
def generate_graph_from_labels(adata, labels_dict):
    """
    Creates and returns the graph and dictionary {node: cluster_label} for specified layer
    """
    
    g, node_to_spot = create_graph(adata)
    spot_to_cluster = labels_dict

    # remove any nodes that are not mapped to a cluster
    removed_nodes = []
    for node in node_to_spot.keys():
        if (node_to_spot[node] not in spot_to_cluster.keys()):
            removed_nodes.append(node)

    for node in removed_nodes:
        del node_to_spot[node]
        g.remove_node(node)
        
    labels = dict(zip(g.nodes(), [spot_to_cluster[node_to_spot[node]] for node in g.nodes()]))
    return g, labels

def spatial_coherence_score(graph, labels):
    g, l = graph, labels
    true_entropy = spatial_entropy(g, l)
    entropies = []
    for i in range(1000):
        new_l = list(l.values())
        random.shuffle(new_l)
        labels = dict(zip(l.keys(), new_l))
        entropies.append(spatial_entropy(g, labels))
        
    return (true_entropy - np.mean(entropies))/np.std(entropies)

def spatial_entropy(g, labels):
    """
    Calculates spatial entropy of graph  
    """
    # construct contiguity matrix C which counts pairs of cluster edges
    cluster_names = np.unique(list(labels.values()))
    C = pd.DataFrame(0,index=cluster_names, columns=cluster_names)

    for e in g.edges():
        C[labels[e[0]]][labels[e[1]]] += 1

    # calculate entropy from C
    C_sum = C.values.sum()
    H = 0
    for i in range(len(cluster_names)):
        for j in range(i, len(cluster_names)):
            if (i == j):
                z = C[cluster_names[i]][cluster_names[j]]
            else:
                z = C[cluster_names[i]][cluster_names[j]] + C[cluster_names[j]][cluster_names[i]]
            if z != 0:
                H += -(z/C_sum)*math.log(z/C_sum)
    return H

# ----- end of PASTE -----


def main(h5ad, prediction, out):
    warnings.simplefilter("ignore")  # PASTE's pandas code warns once per edge
    adata = anndata.read_h5ad(h5ad)
    clusters = pd.read_csv(prediction, dtype=str).set_index("spot_id")["cluster"]
    assert sorted(clusters.index) == sorted(adata.obs_names), "Prediction IDs do not match the dataset."
    g, l = generate_graph_from_labels(adata, clusters)
    random.seed(1)
    scs = abs(spatial_coherence_score(g, l))
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"metric": ["SCS"], "value": [scs]}).to_csv(out, index=False)


main(*sys.argv[1:4])
