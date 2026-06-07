# Techmart — Recherche d'articles en réserve

Ce projet est un assistant de recherche pour les employés d'un magasin de matériel informatique. L'idée de base c'est simple : au lieu de chercher un article à la main dans la réserve, l'employé tape sa question en langage naturel et le système lui dit où trouver le produit et combien il en reste en stock.

On a aussi ajouté un mode conseil pour aider les employés à recommander des produits à un client selon son budget et son usage.

Le tout tourne sans aucune API externe. Le modèle est entraîné directement sur les données du magasin.

---

## Stack technique

- Python 3.11
- MongoDB Atlas (base `techmart`)
- Streamlit pour l'interface
- sentence-transformers pour le modèle de recherche sémantique

---

## Installation

```bash
git clone https://github.com/ehk85/Techmart.git
cd Techmart

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# renseigner MONGODB_URI dans .env

streamlit run app.py
```

---

## Fonctionnement

L'employé pose une question en français — formel ou pas — et le système retrouve les produits correspondants avec leur emplacement en réserve (format Zone-Rayon-Etagere-Position, ex : `D-2-5-6`) et la quantité disponible.

Quelques exemples de requêtes qui marchent :

- "où est la RTX 4080 MSI"
- "le proc AMD pas cher"
- "un client veut monter un PC gaming avec 800 euros"
- "SSD samsung 1to en stock"

Sous le capot, la requête est encodée par le modèle, comparée par similarité cosinus aux embeddings de tous les produits, puis les résultats sont enrichis depuis MongoDB avec le stock et l'emplacement.

---

## Architecture

```
requête (texte libre)
        |
        v
backend/retriever.py
    - extraction des filtres (budget, catégorie, tri)
    - encodage de la requête
    - similarité cosinus sur les embeddings produits
    - jointure MongoDB pour récupérer stock + emplacement
        |
        v
backend/llm_agent.py
    - détection d'intention (localisation, conseil, comparaison)
    - formatage de la réponse
        |
        v
app.py  (Streamlit)
    - onglet assistant (chat)
    - onglet suivi d'entraînement
```

---

## Base de données

Toutes les collections sont dans la base MongoDB `techmart`.

| Collection | Contenu | Docs |
|---|---|---|
| products | catalogue produits (SKU, nom, prix, specs) | 1 000 |
| inventory | stock et liaison produit/emplacement | 1 000 |
| locations | emplacements physiques en réserve | 2 400 |
| product_embeddings | représentations vectorielles des produits | 1 000 |
| training_data | paires (requête, texte produit) pour l'entraînement | 3 253 |
| training_runs | métriques par run d'entraînement | — |
| search_logs | historique des recherches | — |

---

## Entraînement du modèle

On part du modèle `paraphrase-multilingual-MiniLM-L12-v2` (22M paramètres, multilingue) qu'on fine-tune sur les paires requête/produit stockées dans MongoDB. La loss utilisée est `MultipleNegativesRankingLoss`, qui apprend au modèle à rapprocher une requête de son produit cible dans l'espace vectoriel.

```bash
# lancer un entraînement
python training/train.py --epochs 5 --batch-size 32

# évaluer le modèle courant
python training/evaluate.py
```

Les métriques (Hit@1, Hit@5, MRR@10) sont loggées dans MongoDB à chaque epoch et visibles dans l'onglet "Suivi d'entraînement" de l'app.

---

## Résultats

**Run du 2026-06-07 — 5 epochs, batch 32, ~35 minutes sur CPU**

| Métrique | Modèle de base | Après fine-tuning | Gain |
|---|---|---|---|
| Hit@1 | 0.28 | 0.44 | +57% |
| Hit@5 | 0.57 | 0.86 | +52% |
| Hit@10 | 0.69 | 0.95 | +39% |
| MRR@10 | 0.40 | 0.62 | +54% |

### Ce que ça veut dire

**Hit@k** mesure si le bon produit apparaît dans les k premiers résultats. **MRR@10** (Mean Reciprocal Rank) donne la position moyenne du bon produit : si la réponse est en position 3, le score est 1/3. Plus c'est proche de 1, mieux c'est.

Le Hit@1 à 44% peut sembler moyen, mais il faut tenir compte du fait que le corpus de validation contient 213 produits distincts dont beaucoup se ressemblent (plusieurs variantes de processeurs Intel i5, plusieurs alimentations Corsair, etc.). Le modèle doit souvent choisir entre des produits très proches à partir d'une requête vague comme "proc AMD".

Le chiffre le plus utile pour l'usage réel c'est le **Hit@5 à 86%** : dans la grande majorité des cas, l'employé trouvera le bon article dans les 5 premiers résultats affichés.

### Pourquoi le fine-tuning change autant les résultats

Le modèle de base est généraliste — il n'a jamais vu le jargon du matériel informatique ni des requêtes en français informel. Après entraînement sur les données Techmart, il comprend des formulations comme "le proc AMD" ou "gpu gaming pas cher" et sait les associer au bon produit dans le catalogue.

Le gain de +57% sur Hit@1 montre qu'un petit modèle bien spécialisé vaut largement mieux qu'un grand modèle généraliste sur ce type de tâche.

### Ce qui limite encore les performances

Les descriptions produits en base de données sont très génériques ("matériel informatique haute performance"). Le modèle a du mal à distinguer deux produits similaires parce qu'ils ont des textes presque identiques. Enrichir ces descriptions avec les specs (socket, mémoire, TDP...) devrait significativement améliorer le Hit@1.

---

## Variables d'environnement

| Variable | Description |
|---|---|
| MONGODB_URI | URI de connexion MongoDB Atlas |

Pas de clé API externe nécessaire.

---

## Structure du projet

```
Techmart/
├── app.py
├── requirements.txt
├── .env.example
├── backend/
│   ├── database.py       # requêtes MongoDB
│   ├── retriever.py      # moteur de recherche sémantique
│   ├── llm_agent.py      # formatage des réponses
│   └── tools.py
├── training/
│   ├── prepare_data.py   # chargement et split des données
│   ├── train.py          # fine-tuning + logging
│   ├── evaluate.py       # calcul des métriques
│   └── log_results.py    # log post-training dans MongoDB
├── scripts/
│   └── seed_db.py
└── models/               # gitignored
    └── techmart_retriever/
```
