"""
Fine-tune un sentence-transformer sur les paires query→produit Techmart.
Logge chaque epoch dans MongoDB (collection training_runs).
Sauvegarde le modèle dans models/techmart_retriever/.

Usage :
    python training/train.py [--epochs 3] [--batch-size 16]
"""
import os
import sys
import argparse
import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from torch.utils.data import DataLoader
from sentence_transformers import SentenceTransformer, losses
from sentence_transformers.evaluation import SentenceEvaluator

from training.prepare_data import load_pairs, split, to_input_examples
from training.evaluate import compute_metrics
from backend.database import get_db

BASE_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
MODEL_SAVE_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "techmart_retriever")


def _init_run(db, config: dict) -> str:
    run_id = datetime.datetime.utcnow().strftime("run_%Y%m%d_%H%M%S")
    db.training_runs.insert_one({
        "run_id": run_id,
        "model_base": BASE_MODEL,
        "model_save_path": MODEL_SAVE_PATH,
        "started_at": datetime.datetime.utcnow(),
        "completed_at": None,
        "config": config,
        "epochs_log": [],
        "status": "running",
    })
    return run_id


def _finish_run(db, run_id: str, status: str = "completed"):
    db.training_runs.update_one(
        {"run_id": run_id},
        {"$set": {"status": status, "completed_at": datetime.datetime.utcnow()}},
    )


class TechmartEvaluator(SentenceEvaluator):
    """
    Évaluateur personnalisé appelé par sentence-transformers à la fin de chaque epoch.
    Calcule Hit@1, Hit@5, MRR@10 et logge dans MongoDB.
    """

    def __init__(self, val_pairs: list, db, run_id: str):
        self.val_pairs = val_pairs
        self.db = db
        self.run_id = run_id
        self._epoch = 0

    def __call__(self, model, output_path=None, epoch: int = -1, steps: int = -1) -> float:
        self._epoch += 1
        print(f"\n  [Éval epoch {self._epoch}] Calcul des métriques sur {len(self.val_pairs)} exemples…")
        metrics = compute_metrics(model, self.val_pairs)

        entry = {"epoch": self._epoch, **metrics}
        self.db.training_runs.update_one(
            {"run_id": self.run_id},
            {"$push": {"epochs_log": entry}},
        )

        line = " | ".join(f"{k}: {v:.4f}" for k, v in metrics.items())
        print(f"  Epoch {self._epoch} → {line}")
        return metrics.get("mrr@10", 0.0)


def _reindex_products(model: SentenceTransformer, db):
    """Recalcule les embeddings pour tous les produits et les stocke en MongoDB."""
    docs = list(db.product_embeddings.find({}, {"sku": 1, "text": 1}))
    texts = [d["text"] for d in docs]

    print(f"\n=== Mise à jour des embeddings produits ({len(texts)}) ===")
    embeddings = model.encode(texts, batch_size=64, show_progress_bar=True, convert_to_numpy=True)

    for doc, emb in zip(docs, embeddings):
        db.product_embeddings.update_one(
            {"_id": doc["_id"]},
            {"$set": {"embedding": emb.tolist(), "indexed": True}},
        )
    print(f"  ✅ {len(docs)} embeddings mis à jour.")


def train(epochs: int = 3, batch_size: int = 16):
    db = get_db()
    os.makedirs(os.path.dirname(MODEL_SAVE_PATH), exist_ok=True)

    print("=== Chargement des données ===")
    pairs = load_pairs()
    train_pairs, val_pairs = split(pairs)
    print(f"Train : {len(train_pairs)} | Val : {len(val_pairs)}")

    config = {
        "epochs": epochs,
        "batch_size": batch_size,
        "train_samples": len(train_pairs),
        "val_samples": len(val_pairs),
    }

    print(f"\n=== Chargement du modèle de base : {BASE_MODEL} ===")
    model = SentenceTransformer(BASE_MODEL)

    run_id = _init_run(db, config)
    print(f"Run ID : {run_id}\n")

    train_examples = to_input_examples(train_pairs)
    dataloader = DataLoader(train_examples, shuffle=True, batch_size=batch_size)
    loss_fn = losses.MultipleNegativesRankingLoss(model=model)
    evaluator = TechmartEvaluator(val_pairs, db, run_id)

    print("=== Entraînement ===")
    try:
        model.fit(
            train_objectives=[(dataloader, loss_fn)],
            epochs=epochs,
            warmup_steps=int(len(dataloader) * 0.1),
            evaluator=evaluator,
            evaluation_steps=0,       # 0 = évaluer uniquement en fin d'epoch
            show_progress_bar=True,
            output_path=None,
        )
        model.save(MODEL_SAVE_PATH)
        _finish_run(db, run_id, "completed")
        print(f"\n✅ Modèle sauvegardé : {MODEL_SAVE_PATH}")
        _reindex_products(model, db)

    except Exception as e:
        _finish_run(db, run_id, "failed")
        print(f"\n❌ Entraînement échoué : {e}")
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fine-tune Techmart retriever")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=16)
    args = parser.parse_args()
    train(epochs=args.epochs, batch_size=args.batch_size)
