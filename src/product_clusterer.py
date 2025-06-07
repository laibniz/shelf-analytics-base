from typing import List, Dict, DefaultDict
from collections import defaultdict
import math
import numpy as np
from sklearn.cluster import KMeans

from .img2vec_resnet18 import Img2VecResnet18

class ProductClusterer:
    """Generate embeddings and cluster product crops."""

    def __init__(self, n_clusters: int | None = None):
        self.img2vec = Img2VecResnet18()
        self.n_clusters = n_clusters

    def cluster(self, items: List[Dict]) -> Dict[int, List[Dict]]:
        """Return a mapping of cluster id to items with embeddings."""
        embeddings = []
        for item in items:
            vec = self.img2vec.getVec(item["image"])
            item["embedding"] = vec.tolist()
            embeddings.append(vec)

        if not embeddings:
            return {}

        embeddings_arr = np.array(embeddings)
        n_clusters = self.n_clusters or max(1, int(math.sqrt(len(embeddings))))
        kmeans = KMeans(n_clusters=n_clusters, random_state=0, n_init=10)
        labels = kmeans.fit_predict(embeddings_arr)

        clusters: DefaultDict[int, List[Dict]] = defaultdict(list)
        for label, item in zip(labels, items):
            clusters[int(label)].append(item)
        return clusters
