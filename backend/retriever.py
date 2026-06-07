"""
Moteur de recherche sémantique.
Charge le modèle fine-tuné (ou le modèle de base si non encore entraîné),
indexe les produits et répond aux requêtes en langage naturel.
"""
import os
import re
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

from backend.database import get_db, rechercher_produits

BASE_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
TRAINED_MODEL = os.path.join(os.path.dirname(__file__), "..", "models", "techmart_retriever")

# ── Extraction de filtres depuis la requête naturelle ─────────────────────────

_BUDGET_MAX_RE = re.compile(
    r"(?:moins de|max(?:imum)?|<|jusqu['’]?à|pas plus de)\s*(\d[\d\s]*(?:[.,]\d+)?)\s*€?",
    re.IGNORECASE,
)
_BUDGET_MIN_RE = re.compile(
    r"(?:plus de|min(?:imum)?|>|à partir de|au moins)\s*(\d[\d\s]*(?:[.,]\d+)?)\s*€?",
    re.IGNORECASE,
)
_PRICE_RE = re.compile(r"(\d[\d\s]*(?:[.,]\d+)?)\s*€", re.IGNORECASE)

_CATEGORY_MAP = {
    "Processeur":    ["processeur", "cpu", "proc", "ryzen", "core i", "threadripper", "xeon"],
    "Carte graphique": ["carte graphique", "gpu", "rtx", "rx ", "radeon", "geforce", "nvidia", "amd gpu"],
    "Mémoire RAM":   ["ram", "mémoire", "ddr4", "ddr5", "barrette"],
    "SSD NVMe":      ["ssd nvme", "nvme", "m.2"],
    "SSD SATA":      ["ssd sata", "ssd 2.5"],
    "Disque dur HDD":["hdd", "disque dur", "disque dure"],
    "Moniteur":      ["moniteur", "écran", "monitor", "4k", "1440p", "144hz"],
    "Clavier":       ["clavier", "keyboard"],
    "Souris":        ["souris", "mouse"],
    "Casque audio":  ["casque", "audio", "headset"],
    "Alimentation":  ["alimentation", "psu", "watt"],
    "Carte mère":    ["carte mère", "motherboard", "socket"],
    "Boîtier":       ["boîtier", "boitier", "tower", "atx", "itx"],
    "Refroidissement": ["refroidissement", "ventilateur", "ventirad", "aio", "watercooling"],
    "Webcam":        ["webcam", "caméra"],
    "Imprimante":    ["imprimante", "printer"],
}

_SORT_KEYWORDS = {
    "prix_croissant":  ["moins cher", "pas cher", "économique", "budget", "abordable", "entrée de gamme", "le moins"],
    "prix_decroissant":["plus cher", "haut de gamme", "premium", "puissant", "performant", "meilleur", "top"],
    "plus_recent":     ["récent", "nouveau", "dernière génération", "nouveauté"],
    "stock_decroissant":["dispo", "disponible", "en stock", "qu'est-ce qu'on a"],
}


def _parse_filters(query: str) -> dict:
    q = query.lower()
    filters: dict = {}

    # Budget max
    m = _BUDGET_MAX_RE.search(q)
    if m:
        filters["budget_max"] = float(m.group(1).replace(" ", "").replace(",", "."))
    # Budget min
    m = _BUDGET_MIN_RE.search(q)
    if m:
        filters["budget_min"] = float(m.group(1).replace(" ", "").replace(",", "."))
    # Prix seul (ex: "400€") → budget max si pas déjà trouvé
    if "budget_max" not in filters and "budget_min" not in filters:
        m = _PRICE_RE.search(q)
        if m:
            filters["budget_max"] = float(m.group(1).replace(" ", "").replace(",", "."))

    # En stock
    if any(k in q for k in ["en stock", "disponible", "dispo", "qu'est-ce qu'on a", "qu on a"]):
        filters["en_stock"] = True

    # Catégorie
    for cat, keywords in _CATEGORY_MAP.items():
        if any(k in q for k in keywords):
            filters["categorie"] = cat
            break

    # Tri
    for tri, keywords in _SORT_KEYWORDS.items():
        if any(k in q for k in keywords):
            filters["tri"] = tri
            break

    return filters


# ── Singleton Retriever ────────────────────────────────────────────────────────

class _Retriever:
    def __init__(self):
        self._model: SentenceTransformer | None = None
        self._embs: np.ndarray | None = None          # (N, D)
        self._skus: list[str] = []                    # aligné avec _embs
        self._ready = False

    def _load(self):
        path = TRAINED_MODEL if os.path.isdir(TRAINED_MODEL) else BASE_MODEL
        print(f"[Retriever] Chargement du modèle : {path}")
        self._model = SentenceTransformer(path)
        self._build_index()
        self._ready = True

    def _build_index(self):
        """Charge les embeddings stockés en MongoDB (ou les calcule à la volée)."""
        db = get_db()
        docs = list(db.product_embeddings.find({"indexed": True}, {"sku": 1, "embedding": 1, "text": 1}))

        has_embs = [d for d in docs if d.get("embedding")]
        if has_embs:
            print(f"[Retriever] Chargement de {len(has_embs)} embeddings depuis MongoDB…")
            self._skus = [d["sku"] for d in has_embs]
            self._embs = np.array([d["embedding"] for d in has_embs], dtype=np.float32)
        else:
            # Calcul à la volée avec le modèle courant
            print(f"[Retriever] Calcul des embeddings pour {len(docs)} produits…")
            texts = [d["text"] for d in docs]
            self._skus = [d["sku"] for d in docs]
            self._embs = self._model.encode(
                texts, batch_size=64, show_progress_bar=True, convert_to_numpy=True
            ).astype(np.float32)

        print(f"[Retriever] Index prêt — {len(self._skus)} produits.")

    def reload(self):
        """Force le rechargement (après un entraînement)."""
        self._ready = False
        self._load()

    def search(self, query: str, top_k: int = 6) -> list[dict]:
        """
        Recherche sémantique + filtres MongoDB extraits de la requête.
        Retourne une liste de produits enrichis (nom, prix, specs, stock, emplacement).
        """
        if not self._ready:
            self._load()

        filters = _parse_filters(query)

        # Recherche sémantique → top candidats SKU
        q_emb = self._model.encode([query], convert_to_numpy=True)
        scores = cosine_similarity(q_emb, self._embs)[0]
        top_indices = np.argsort(-scores)[: top_k * 3]  # marge pour le filtrage MongoDB
        candidate_skus = [self._skus[i] for i in top_indices]

        # Filtrage + enrichissement via MongoDB
        db = get_db()
        from bson import ObjectId
        from backend.database import _BASE_PIPELINE

        mongo_filter: dict = {"sku": {"$in": candidate_skus}}
        if filters.get("categorie"):
            mongo_filter["category_name"] = {"$regex": filters["categorie"], "$options": "i"}
        if filters.get("budget_max") is not None:
            mongo_filter.setdefault("price", {})["$lte"] = filters["budget_max"]
        if filters.get("budget_min") is not None:
            mongo_filter.setdefault("price", {})["$gte"] = filters["budget_min"]

        pipeline = [{"$match": mongo_filter}] + _BASE_PIPELINE

        if filters.get("en_stock"):
            pipeline.append({"$match": {"stock": {"$gt": 0}}})

        sort_field = filters.get("tri", "pertinence")
        if sort_field == "prix_croissant":
            pipeline.append({"$sort": {"price": 1}})
        elif sort_field == "prix_decroissant":
            pipeline.append({"$sort": {"price": -1}})
        elif sort_field == "stock_decroissant":
            pipeline.append({"$sort": {"stock": -1}})

        pipeline.append({"$limit": top_k})

        results = list(db.products.aggregate(pipeline))
        for r in results:
            r["_id"] = str(r["_id"])
            r["_score"] = float(scores[candidate_skus.index(r["sku"])]) if r["sku"] in candidate_skus else 0.0

        # Si aucun résultat avec filtres stricts → fallback sans filtre catégorie/budget
        if not results:
            pipeline_fallback = [{"$match": {"sku": {"$in": candidate_skus}}}] + _BASE_PIPELINE + [{"$limit": top_k}]
            results = list(db.products.aggregate(pipeline_fallback))
            for r in results:
                r["_id"] = str(r["_id"])

        return results


_instance: _Retriever | None = None


def get_retriever() -> _Retriever:
    global _instance
    if _instance is None:
        _instance = _Retriever()
    return _instance
