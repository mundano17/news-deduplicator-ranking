# 1 FIX THE GODDAMN CLUSTERING
# 2 RANK EM CLUSTERS
# FIGURE OUT THE FORMAT FOR RANKING
# 3 DEDUPLICATE DONE ?
# 4 SCALE UP, MORE DATA.


import pandas as pd
import spacy
import torch
import torch.nn.functional as F
from sentence_transformers import SentenceTransformer
from sklearn.cluster import HDBSCAN

from models import Scrape

nlp = spacy.load("en_core_web_sm")


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
        self.embeddings = F.normalize(self.embeddings, p=2, dim=1)

    def clustering(self):
        clusterer = HDBSCAN(
            metric="cosine", min_cluster_size=2, cluster_selection_method="leaf"
        )
        cluster = clusterer.fit(self.embeddings.cpu().numpy())
        clusterframe = pd.DataFrame(
            {
                "text": [obj.text for obj in self.text],
                "cluster_id": cluster.labels_,
            }
        )
        print(clusterframe)
        print(f"DEBUG: Type of clusterframe is {type(clusterframe)}")
        return clusterframe

    def preprocessing(self, text: str):
        doc = nlp(text)
        op = [token.lemma_ for token in doc]
        return op

    def mtld(self, tokens: list[str], threshold: float = 0.74):
        def get_factors(tokens: list[str]):
            factors = 0
            proc_tokens = []
            for i in tokens:
                proc_tokens.append(i)
                ttr = len(set(proc_tokens)) / len(proc_tokens)
                if ttr < threshold:
                    factors += 1
                    proc_tokens = []

            if proc_tokens:
                ttr = len(set(proc_tokens)) / len(proc_tokens)
                factors += (1 - ttr) / (1 - threshold) if ttr < 1 else 0

            return max(factors, 1)

        x = get_factors(tokens)
        y = get_factors(tokens[::-1])
        return (x + y) / 2

    def ranking(self, clusterframe: pd.DataFrame):
        noiseless_frame = clusterframe[clusterframe["cluster_id"] != -1].copy()
        noiseless_frame["mtld_score"] = noiseless_frame["text"].apply(
            lambda x: self.mtld(self.preprocessing(x))
        )
        print(noiseless_frame)
        return noiseless_frame

    def __call__(self):
        clusterframe = self.clustering()
        ranked_frame = self.ranking(clusterframe)
        return ranked_frame
