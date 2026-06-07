import os
import certifi
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

_client: MongoClient | None = None

SORT_MAP = {
    "prix_croissant": [("price", 1)],
    "prix_decroissant": [("price", -1)],
    "plus_recent": [("created_at", -1)],
    "stock_decroissant": [("stock", -1)],
}

# Agrégation de base : products → inventory → locations
_BASE_PIPELINE = [
    {
        "$lookup": {
            "from": "inventory",
            "localField": "_id",
            "foreignField": "product_id",
            "as": "_inv",
        }
    },
    {"$unwind": {"path": "$_inv", "preserveNullAndEmptyArrays": True}},
    {
        "$lookup": {
            "from": "locations",
            "localField": "_inv.location_id",
            "foreignField": "_id",
            "as": "_loc",
        }
    },
    {"$unwind": {"path": "$_loc", "preserveNullAndEmptyArrays": True}},
    {
        "$addFields": {
            "stock": "$_inv.quantity",
            "emplacement": "$_loc.label",
        }
    },
    {"$project": {"_inv": 0, "_loc": 0, "brand_id": 0, "category_id": 0}},
]


def get_db():
    global _client
    if _client is None:
        _client = MongoClient(os.getenv("MONGODB_URI"), tlsCAFile=certifi.where())
    return _client["techmart"]


def _serialize(doc: dict) -> dict:
    doc["_id"] = str(doc["_id"])
    return doc


# ── Fonctions exposées aux outils Claude ─────────────────────────────────────

def rechercher_produits(
    query: str = None,
    categorie: str = None,
    marque: str = None,
    budget_max: float = None,
    budget_min: float = None,
    en_stock: bool = False,
    tri: str = "pertinence",
    limit: int = 6,
) -> list[dict]:
    """Recherche multi-critères avec jointure inventory + location."""
    db = get_db()
    filtre: dict = {}

    if query:
        regex = {"$regex": query, "$options": "i"}
        filtre["$or"] = [
            {"name": regex},
            {"brand_name": regex},
            {"category_name": regex},
            {"sku": regex},
            {"description": regex},
        ]

    if categorie:
        filtre["category_name"] = {"$regex": categorie, "$options": "i"}

    if marque:
        filtre["brand_name"] = {"$regex": marque, "$options": "i"}

    if budget_max is not None:
        filtre.setdefault("price", {})["$lte"] = budget_max

    if budget_min is not None:
        filtre.setdefault("price", {})["$gte"] = budget_min

    pipeline = [{"$match": filtre}] + _BASE_PIPELINE

    if en_stock:
        pipeline.append({"$match": {"stock": {"$gt": 0}}})

    if tri in SORT_MAP:
        pipeline.append({"$sort": dict(SORT_MAP[tri])})

    pipeline.append({"$limit": limit})

    return [_serialize(r) for r in db.products.aggregate(pipeline)]


def get_produit_par_sku(sku: str) -> dict | None:
    """Récupère un produit par son SKU avec stock et emplacement."""
    db = get_db()
    pipeline = [{"$match": {"sku": {"$regex": f"^{sku}$", "$options": "i"}}}] + _BASE_PIPELINE
    results = list(db.products.aggregate(pipeline))
    return _serialize(results[0]) if results else None


def comparer_produits(skus: list[str]) -> list[dict]:
    """Retourne les détails complets de plusieurs produits pour comparaison."""
    db = get_db()
    pipeline = [
        {"$match": {"sku": {"$in": [s.upper() for s in skus]}}},
    ] + _BASE_PIPELINE
    return [_serialize(r) for r in db.products.aggregate(pipeline)]


def lister_categories() -> list[str]:
    db = get_db()
    return sorted(db.products.distinct("category_name"))


# ── Training runs ─────────────────────────────────────────────────────────────

def get_training_runs(limit: int = 20) -> list[dict]:
    """Retourne les dernières runs d'entraînement (plus récentes en premier)."""
    db = get_db()
    docs = list(
        db.training_runs.find({})
        .sort("started_at", -1)
        .limit(limit)
    )
    for d in docs:
        d["_id"] = str(d["_id"])
    return docs


def get_latest_run() -> dict | None:
    db = get_db()
    doc = db.training_runs.find_one({}, sort=[("started_at", -1)])
    if doc:
        doc["_id"] = str(doc["_id"])
    return doc


# ── Logs de recherche ─────────────────────────────────────────────────────────

def log_search(query: str, results: list[dict]):
    """Enregistre une recherche pour analyse et futur réentraînement."""
    db = get_db()
    import datetime
    db.search_logs.insert_one({
        "query": query,
        "results": [{"name": r.get("name"), "sku": r.get("sku")} for r in results[:5]],
        "timestamp": datetime.datetime.utcnow(),
        "confirmed": False,
    })


def stats_stock() -> dict:
    db = get_db()
    col = db.products
    pipeline_join = _BASE_PIPELINE + [
        {
            "$group": {
                "_id": None,
                "total": {"$sum": 1},
                "en_stock": {"$sum": {"$cond": [{"$gt": ["$stock", 0]}, 1, 0]}},
                "rupture": {"$sum": {"$cond": [{"$eq": ["$stock", 0]}, 1, 0]}},
            }
        }
    ]
    result = list(col.aggregate(pipeline_join))
    if result:
        r = result[0]
        return {
            "total_articles": r["total"],
            "en_stock": r["en_stock"],
            "rupture_de_stock": r["rupture"],
        }
    return {"total_articles": 0, "en_stock": 0, "rupture_de_stock": 0}
