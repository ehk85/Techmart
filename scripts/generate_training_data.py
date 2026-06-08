"""
Génère des paires (query, product_text) pour tous les produits du catalogue.

Deux stratégies selon la qualité du nom :
- Produit nommé (ex: "Samsung 970 EVO Plus 500Go") → requêtes riches sur le nom
- Produit générique (ex: "Ventilateur 120mm ARGB #206") → requêtes sur catégorie+marque+specs

Usage :
    python scripts/generate_training_data.py [--dry-run]
"""
import os, sys, re, argparse, random
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dotenv import load_dotenv
load_dotenv()
from backend.database import get_db
from scripts.enrich_product_texts import specs_to_text


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_generic(name: str) -> bool:
    return bool(re.search(r"#\d", name))

def _abbrev(name: str) -> str:
    tokens = name.split()
    return " ".join(tokens[-2:]) if len(tokens) >= 2 else name

def _price_bucket(price: float) -> str:
    if price < 80:    return "pas cher"
    if price < 200:   return "entrée de gamme"
    if price < 500:   return "milieu de gamme"
    return "haut de gamme"

def _cat_abbrevs(category: str) -> list[str]:
    mapping = {
        "processeur":     ["proc", "cpu", "processeur"],
        "carte graphique":["gpu", "carte graphique", "carte graph"],
        "mémoire ram":    ["ram", "mémoire", "barrette de ram"],
        "ssd nvme":       ["ssd", "nvme", "ssd nvme"],
        "ssd sata":       ["ssd", "disque ssd"],
        "disque dur hdd": ["disque dur", "hdd", "dd"],
        "disque externe": ["disque externe", "disque usb"],
        "carte mère":     ["carte mère", "mobo"],
        "alimentation":   ["alim", "psu", "alimentation"],
        "boîtier":        ["boîtier", "case"],
        "refroidissement":["refroidissement", "ventirad", "aio", "cooling"],
        "moniteur":       ["écran", "moniteur"],
        "clavier":        ["clavier"],
        "souris":         ["souris"],
        "casque audio":   ["casque", "audio"],
        "webcam":         ["webcam"],
        "imprimante":     ["imprimante"],
        "carte réseau":   ["carte réseau", "wifi"],
        "switch réseau":  ["switch", "switch réseau"],
        "accessoire":     ["accessoire", "câble"],
    }
    return mapping.get(category.lower(), [category.lower()])


# ---------------------------------------------------------------------------
# Produits avec un vrai nom
# ---------------------------------------------------------------------------

def _named_queries(name, brand, category, specs, price) -> list[str]:
    abbrev = _abbrev(name)
    tags = _cat_abbrevs(category)
    spec_toks = []
    if specs.get("socket"):   spec_toks.append(f"socket {specs['socket']}")
    if specs.get("cores"):    spec_toks.append(f"{specs['cores']} cœurs")
    if specs.get("memory"):   spec_toks.append(str(specs["memory"]))
    if specs.get("read"):     spec_toks.append(f"lecture {specs['read']}")

    bucket = _price_bucket(price)
    queries = [
        # Localisation
        f"où est le {name}",
        f"où trouver le {abbrev}",
        f"localise le {name}",
        f"emplacement {abbrev}",
        f"dans quel rayon est le {abbrev}",
        f"où se trouve le {name}",
        # Stock
        f"combien de {abbrev} en stock",
        f"stock {abbrev}",
        f"on a encore du {abbrev}",
        f"disponibilité {abbrev}",
        # Recherche directe
        f"le {abbrev}",
        f"{brand} {abbrev}",
        f"je cherche le {abbrev}",
        f"besoin du {name}",
        f"donne moi le {abbrev}",
        f"référence {abbrev}",
        # Par catégorie + marque
        f"un {tags[0]} {brand}",
        f"je veux un {tags[0]} {brand}",
        f"{tags[0]} {brand} {bucket}",
        f"{brand} {tags[0]}",
    ]
    # Variations informelles avec abréviations de catégorie
    for tag in tags[1:3]:
        queries.append(f"le {tag} {brand}")
        queries.append(f"{tag} {abbrev}")
    # Par spec
    for tok in spec_toks[:2]:
        queries.append(f"{brand} {tok}")
        queries.append(f"{tags[0]} {tok}")
    # Prix
    queries.append(f"{tags[0]} {brand} à {int(price)} euros")
    queries.append(f"un {tags[0]} {bucket}")

    return queries


# ---------------------------------------------------------------------------
# Produits génériques (nom avec #)
# ---------------------------------------------------------------------------

def _generic_queries(name, brand, category, specs, price) -> list[str]:
    tags = _cat_abbrevs(category)
    spec_toks = []
    if specs.get("socket"):      spec_toks.append(f"socket {specs['socket']}")
    if specs.get("cores"):       spec_toks.append(f"{specs['cores']} cœurs")
    if specs.get("memory"):      spec_toks.append(str(specs["memory"]))
    if specs.get("form_factor"): spec_toks.append(str(specs["form_factor"]))
    if specs.get("efficiency"):  spec_toks.append(str(specs["efficiency"]))
    if specs.get("read"):        spec_toks.append(f"lecture {specs['read']}")
    if specs.get("fans_included"): spec_toks.append(f"{specs['fans_included']} ventilateurs")

    bucket = _price_bucket(price)

    # Extraire info utile du nom générique (ex: "Ventilateur 120mm ARGB" depuis "#206")
    base_desc = re.sub(r"\s*#\d+$", "", name).strip()

    queries = [
        f"{brand} {tags[0]}",
        f"un {tags[0]} {brand}",
        f"je cherche un {tags[0]} {brand}",
        f"stock {brand} {tags[0]}",
        f"où est le {base_desc} {brand}",
        f"{base_desc} {brand}",
        f"{tags[0]} {brand} {bucket}",
        f"un {tags[0]} {bucket}",
    ]
    for tag in tags[1:2]:
        queries.append(f"{tag} {brand}")
        queries.append(f"un {tag} {brand}")
    for tok in spec_toks[:3]:
        queries.append(f"{tags[0]} {tok}")
        queries.append(f"{brand} {tok}")
    queries.append(f"{base_desc.lower()} en stock")
    queries.append(f"localise {base_desc.lower()} {brand}")

    return queries


# ---------------------------------------------------------------------------
# Génération principale
# ---------------------------------------------------------------------------

def generate_for_product(product: dict) -> list[dict]:
    name     = product.get("name", "")
    brand    = product.get("brand_name", "")
    category = product.get("category_name", "")
    specs    = product.get("specs") or {}
    price    = product.get("price", 0)

    if _is_generic(name):
        raw_queries = _generic_queries(name, brand, category, specs, price)
    else:
        raw_queries = _named_queries(name, brand, category, specs, price)

    # Nettoyer et dédoublonner
    seen, cleaned = set(), []
    for q in raw_queries:
        q = re.sub(r"\s+", " ", q.strip().lower())
        if q and q not in seen and len(q) > 4:
            seen.add(q)
            cleaned.append(q)

    specs_txt = specs_to_text(specs)
    product_text = f"{name} {brand} {category} {specs_txt}".strip()

    return [
        {
            "query": q,
            "product_id": product["_id"],
            "product_text": product_text,
            "product_name": name,
            "source": "rule_based_v2",
        }
        for q in cleaned
    ]


# ---------------------------------------------------------------------------
# Point d'entrée
# ---------------------------------------------------------------------------

def run(dry_run: bool = False):
    db = get_db()

    already = set(
        doc["product_id"]
        for doc in db.training_data.find({"source": "rule_based_v2"}, {"product_id": 1})
    )
    print(f"Produits déjà générés (rule_based_v2) : {len(already)}")

    products = list(db.products.find({}))
    to_process = [p for p in products if p["_id"] not in already]
    print(f"Produits à traiter : {len(to_process)}")

    named   = [p for p in to_process if not _is_generic(p.get("name", ""))]
    generic = [p for p in to_process if _is_generic(p.get("name", ""))]
    print(f"  Nommés : {len(named)} | Génériques : {len(generic)}")

    new_pairs = []
    for prod in to_process:
        new_pairs.extend(generate_for_product(prod))

    print(f"\nNouvelles paires : {len(new_pairs)}")

    if dry_run:
        print("\nDRY RUN — exemples produits nommés :")
        sample_named = [p for p in new_pairs if not _is_generic(p["product_name"])]
        for p in random.sample(sample_named, min(6, len(sample_named))):
            print(f"  [{p['product_name']}] '{p['query']}'")
        print("\nDRY RUN — exemples produits génériques :")
        sample_gen = [p for p in new_pairs if _is_generic(p["product_name"])]
        for p in random.sample(sample_gen, min(6, len(sample_gen))):
            print(f"  [{p['product_name']}] '{p['query']}'")
        return

    if new_pairs:
        db.training_data.insert_many(new_pairs)
        print(f"Insérées : {len(new_pairs)}")

    total   = db.training_data.count_documents({})
    covered = len(db.training_data.distinct("product_id"))
    print(f"\nEtat final : {total} paires | {covered}/{len(products)} produits couverts")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    run(dry_run=args.dry_run)
