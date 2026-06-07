"""
Évalue le modèle sur le set de validation.
Métriques : Hit@1, Hit@5, MRR@10
"""
import os
import sys
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()


def compute_metrics(
    model,
    val_pairs: list[tuple[str, str]],
    batch_size: int = 32,
    ks: list[int] = [1, 5, 10],
) -> dict[str, float]:
    """
    Évalue le modèle sur les paires de validation.

    Pour chaque query, le product_text correct doit apparaître dans les top-k
    des produits candidats (corpus = tous les product_texts uniques du val set).
    """
    queries = [q for q, _ in val_pairs]
    products = [p for _, p in val_pairs]
    unique_products = list(dict.fromkeys(products))  # dédoublonné, ordre préservé
    product_index = {p: i for i, p in enumerate(unique_products)}

    print(f"  Encodage de {len(queries)} queries et {len(unique_products)} produits uniques…")

    query_embs = model.encode(queries, batch_size=batch_size, show_progress_bar=False, convert_to_numpy=True)
    product_embs = model.encode(unique_products, batch_size=batch_size, show_progress_bar=False, convert_to_numpy=True)

    scores = cosine_similarity(query_embs, product_embs)  # (N, M)

    hits = {k: 0 for k in ks}
    mrr = 0.0

    for i, (_, correct_text) in enumerate(val_pairs):
        correct_idx = product_index[correct_text]
        ranked = np.argsort(-scores[i])  # tri décroissant

        rank = int(np.where(ranked == correct_idx)[0][0]) + 1  # 1-based

        for k in ks:
            if rank <= k:
                hits[k] += 1
        if rank <= 10:
            mrr += 1.0 / rank

    n = len(val_pairs)
    metrics = {f"hit@{k}": round(hits[k] / n, 4) for k in ks}
    metrics["mrr@10"] = round(mrr / n, 4)
    return metrics


if __name__ == "__main__":
    from sentence_transformers import SentenceTransformer
    from training.prepare_data import load_pairs, split

    MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "techmart_retriever")
    BASE_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

    path = MODEL_PATH if os.path.exists(MODEL_PATH) else BASE_MODEL
    print(f"Chargement du modèle : {path}")
    model = SentenceTransformer(path)

    _, val = split(load_pairs())
    metrics = compute_metrics(model, val)

    print("\n=== Résultats ===")
    for k, v in metrics.items():
        print(f"  {k}: {v:.4f}")
