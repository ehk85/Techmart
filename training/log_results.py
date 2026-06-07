"""
Évalue le modèle entraîné et met à jour le document training_run dans MongoDB.
Utiliser après un run dont les métriques per-epoch n'ont pas été capturées.

Usage :
    python training/log_results.py [--run-id run_20260607_195318]
"""
import os, sys, argparse, datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dotenv import load_dotenv
load_dotenv()

from sentence_transformers import SentenceTransformer
from training.prepare_data import load_pairs, split
from training.evaluate import compute_metrics
from backend.database import get_db

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "techmart_retriever")
BASE_MODEL  = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def log_results(run_id: str | None = None):
    db = get_db()

    # Trouver le run
    query = {"run_id": run_id} if run_id else {}
    run = db.training_runs.find_one(query, sort=[("started_at", -1)])
    if not run:
        print("Aucun run trouvé.")
        return

    print(f"Run : {run['run_id']} | Status : {run['status']}")

    path = MODEL_PATH if os.path.isdir(MODEL_PATH) else BASE_MODEL
    print(f"Chargement du modèle : {path}")
    model = SentenceTransformer(path)

    _, val_pairs = split(load_pairs())
    print(f"Évaluation sur {len(val_pairs)} exemples…")
    metrics = compute_metrics(model, val_pairs)

    entry = {"epoch": "final", **metrics}
    db.training_runs.update_one(
        {"_id": run["_id"]},
        {
            "$push": {"epochs_log": entry},
            "$set": {
                "status": "completed",
                "completed_at": datetime.datetime.utcnow(),
            },
        },
    )
    print("\n=== Résultats finaux ===")
    for k, v in metrics.items():
        print(f"  {k}: {v:.4f}")
    print(f"\nLoggé dans MongoDB — run_id : {run['run_id']}")
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", type=str, default=None)
    args = parser.parse_args()
    log_results(args.run_id)
