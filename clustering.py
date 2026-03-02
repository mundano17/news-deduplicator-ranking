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


class ClusteRanking:
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
                "url": [obj.url for obj in self.text],
                "headlines": [obj.headline for obj in self.text],
                "text": [obj.text for obj in self.text],
                "cluster_id": cluster.labels_,
            }
        )
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

        x = len(tokens) / get_factors(tokens)
        y = len(tokens) / get_factors(tokens[::-1])
        return (x + y) / 2

    def ranking(self, clusterframe: pd.DataFrame):
        noiseless_frame = clusterframe[clusterframe["cluster_id"] != -1].copy()
        noiseless_frame["mtld_score"] = noiseless_frame["text"].apply(
            lambda x: self.mtld(self.preprocessing(x))
        )
        return noiseless_frame

    def ranking_hl(self, clusterframe: pd.DataFrame):
        noiseless_frame = clusterframe[clusterframe["cluster_id"] != -1].copy()
        noiseless_frame["mtld_score"] = noiseless_frame["headlines"].apply(
            lambda x: self.mtld(self.preprocessing(x))
        )
        return noiseless_frame

    def de_duplication(self, ranked_frame: pd.DataFrame):
        ranked_frames = ranked_frame.sort_values(
            by=["cluster_id", "mtld_score"], ascending=[True, False]
        )
        ranked_frames = ranked_frames.drop_duplicates(
            subset=["cluster_id"], keep="first"
        )
        return ranked_frames

    def __call__(self):
        clusterframe = self.clustering()
        lonely_stories = clusterframe[clusterframe["cluster_id"] == -1].copy()
        ranked_frame = self.ranking(clusterframe)
        ranked_frames = self.de_duplication(ranked_frame)
        final_frames = pd.concat([ranked_frames, lonely_stories], ignore_index=True)

        print("### ORIGINAL CLUSTERING ###\n")
        print(clusterframe)

        print("### RANKED CLUSTERING ###")
        print(ranked_frame)

        print("### DEDUP + RANKED ###")
        print(final_frames)
        return final_frames
