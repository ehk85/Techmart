"""
Charge les paires (query, product_text) depuis MongoDB et prépare les splits train/val.
"""
import os
import sys
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from backend.database import get_db
from sentence_transformers import InputExample


def load_pairs(shuffle: bool = True, seed: int = 42) -> list[tuple[str, str]]:
    """Retourne toutes les paires (query, product_text) depuis training_data."""
    db = get_db()
    pairs = [
        (doc["query"], doc["product_text"])
        for doc in db.training_data.find({}, {"query": 1, "product_text": 1})
        if doc.get("query") and doc.get("product_text")
    ]
    if shuffle:
        random.seed(seed)
        random.shuffle(pairs)
    return pairs


def split(pairs: list, val_ratio: float = 0.2) -> tuple[list, list]:
    """Découpe en train / val."""
    cut = int(len(pairs) * (1 - val_ratio))
    return pairs[:cut], pairs[cut:]


def to_input_examples(pairs: list[tuple[str, str]]) -> list[InputExample]:
    """Convertit les paires en InputExample pour sentence-transformers."""
    return [InputExample(texts=[q, p]) for q, p in pairs]


if __name__ == "__main__":
    pairs = load_pairs()
    train, val = split(pairs)
    print(f"Total : {len(pairs)} paires")
    print(f"Train : {len(train)} | Val : {len(val)}")
    print(f"\nExemples train :")
    for q, p in train[:3]:
        print(f"  Q: {q!r}")
        print(f"  P: {p[:80]!r}")
        print()
