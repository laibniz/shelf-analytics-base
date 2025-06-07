from typing import List, Dict, DefaultDict
from collections import defaultdict
import math
import numpy as np
from sklearn.cluster import AgglomerativeClustering

from .img2vec_resnet18 import Img2VecResnet18

class ProductClusterer:
    """Generate embeddings and cluster product crops."""

    def __init__(self, n_clusters: int | None = None):
        self.img2vec = Img2VecResnet18()
        self.n_clusters = n_clusters

    def cluster(self, items: List[Dict], n_clusters: int | None = None) -> Dict[int, Dict]:
        """Return a mapping of cluster id to items with embeddings and representative index."""
        embeddings = []
        for item in items:
            vec = self.img2vec.getVec(item["image"])
            item["embedding"] = vec.tolist()
            embeddings.append(vec)

        if not embeddings:
            return {}

        embeddings_arr = np.array(embeddings)
        n_clusters = n_clusters or self.n_clusters or max(1, int(math.sqrt(len(embeddings))))
        clustering = AgglomerativeClustering(n_clusters=n_clusters)
        labels = clustering.fit_predict(embeddings_arr)

        groups: DefaultDict[int, List[Dict]] = defaultdict(list)
        for label, item in zip(labels, items):
            groups[int(label)].append(item)

        clusters: Dict[int, Dict] = {}
        for cid, cluster_items in groups.items():
            arr = np.array([i["embedding"] for i in cluster_items])
            center = arr.mean(axis=0)
            dists = np.linalg.norm(arr - center, axis=1)
            rep_idx = int(dists.argmin())
            clusters[cid] = {"items": cluster_items, "representative_index": rep_idx}

        return clusters
