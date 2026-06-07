"""
Enrichit les product_text dans product_embeddings en ajoutant les specs techniques.

Avant : "Intel Core i3-12100 Intel Processeur — matériel informatique haute performance."
Après : "Intel Core i3-12100 Intel Processeur socket LGA1700 coeurs 4 TDP 170W"

A relancer avant chaque entraînement si les specs ont changé en base.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dotenv import load_dotenv
load_dotenv()

from backend.database import get_db


def specs_to_text(specs: dict) -> str:
    if not specs:
        return ""
    labels = {
        "cores": "coeurs", "socket": "socket", "tdp": "TDP",
        "memory": "memoire", "read": "lecture", "write": "ecriture",
        "form_factor": "format", "efficiency": "efficacite",
        "modular": "modulaire", "fans_included": "ventilateurs",
        "rpm": "RPM", "panel": "dalle", "response": "reponse",
        "interface": "interface", "cache": "cache",
        "latency": "latence", "pcie_slots": "slots PCIe", "type": "type",
    }
    parts = []
    for k, v in specs.items():
        label = labels.get(k, k)
        if isinstance(v, bool):
            v = "oui" if v else "non"
        parts.append(f"{label} {v}")
    return " ".join(parts)


def enrich():
    db = get_db()
    products = {str(p["_id"]): p for p in db.products.find({}, {"_id": 1, "specs": 1})}

    updated = 0
    for doc in db.product_embeddings.find({}):
        prod = products.get(str(doc["product_id"]))
        if not prod:
            continue
        specs_txt = specs_to_text(prod.get("specs") or {})
        base = doc["text"].replace(" — matériel informatique haute performance.", "")
        new_text = (base + " " + specs_txt).strip()
        db.product_embeddings.update_one(
            {"_id": doc["_id"]},
            {"$set": {"text": new_text}}
        )
        updated += 1

    print(f"Mis à jour : {updated} product_text")
    example = db.product_embeddings.find_one({})
    print(f"Exemple : {example['text']}")


if __name__ == "__main__":
    enrich()
