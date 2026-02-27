import torch
from sentence_transformers import SentenceTransformer
from sklearn.cluster import HDBSCAN

from models import Scrape


class Clustering:
    def __init__(self, text: list[Scrape]):
        self.text = text
        self.device = "cpu"
        if torch.cuda.is_available():
            self.device = "cuda"
        if torch.backends.mps.is_available():
            self.device = "mps"
        self.model = SentenceTransformer("all-mpnet-base-v2", device=self.device)
        self.embeddings = self.model.encode(
            [i.text for i in self.text],
            batch_size=32,
            show_progress_bar=True,
            convert_to_tensor=True,
        )

    def clustering(self):
        clusterer = HDBSCAN(metric="cosine")
        cluster = clusterer.fit(self.embeddings.cpu().numpy())
        return cluster

    def __call__(self):
        self.clustering()
        pass
