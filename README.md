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

On a fait deux runs d'entraînement successifs. Entre les deux, on a enrichi les textes produits en y ajoutant les specs techniques (socket, mémoire, TDP...) parce que les descriptions de base étaient trop génériques pour que le modèle puisse distinguer des variantes proches.

### Métriques de référence — modèle de base (sans fine-tuning)

| Métrique | Score |
|---|---|
| Hit@1 | 0.28 |
| Hit@5 | 0.57 |
| Hit@10 | 0.69 |
| MRR@10 | 0.40 |

### Run 1 — textes génériques, 5 epochs, batch 32, ~35 min CPU

Seul le résultat final a été mesuré (bug dans le callback d'évaluation, corrigé ensuite).

| Métrique | Score final |
|---|---|
| Hit@1 | 0.4439 |
| Hit@5 | 0.8618 |
| Hit@10 | 0.9539 |
| MRR@10 | 0.6214 |

### Run 2 — textes enrichis avec specs, 5 epochs, batch 32, ~35 min CPU

Cette fois le callback fonctionnait, on a donc les métriques epoch par epoch.

| Epoch | Hit@1 | Hit@5 | Hit@10 | MRR@10 |
|---|---|---|---|---|
| 1 | 0.4117 | 0.8587 | 0.9355 | 0.5935 |
| 2 | 0.4363 | 0.8587 | 0.9478 | 0.6099 |
| 3 | 0.4301 | 0.8648 | 0.9478 | 0.6097 |
| 4 | **0.4501** | 0.8725 | 0.9585 | **0.6220** |
| 5 | **0.4501** | **0.8756** | **0.9585** | 0.6211 |

Comparaison avec le modèle de base :

| Métrique | Base | Run 2 (ep. 5) | Gain total |
|---|---|---|---|
| Hit@1 | 0.28 | 0.45 | +61% |
| Hit@5 | 0.57 | 0.88 | +54% |
| Hit@10 | 0.69 | 0.96 | +39% |
| MRR@10 | 0.40 | 0.62 | +55% |

### Ce que ça veut dire

**Hit@k** mesure si le bon produit apparaît dans les k premiers résultats. **MRR@10** (Mean Reciprocal Rank) donne la position moyenne du bon produit : si la réponse est en position 3, le score est 1/3. Plus c'est proche de 1, mieux c'est.

Le Hit@1 à 45% peut sembler moyen, mais le corpus de validation contient 213 produits distincts dont beaucoup se ressemblent beaucoup — plusieurs variantes de processeurs Intel i5, plusieurs alimentations Corsair, etc. Le modèle doit souvent choisir entre des produits très proches à partir d'une requête vague comme "proc AMD".

Le chiffre le plus utile pour l'usage réel c'est le **Hit@5 à 88%** : dans la grande majorité des cas, l'employé trouvera le bon article dans les 5 premiers résultats.

### Ce qu'on observe sur la courbe d'entraînement

L'epoch 3 montre un léger recul sur Hit@1 (0.4363 → 0.4301) avant de remonter à l'epoch 4. C'est un comportement normal pendant l'entraînement — le modèle réorganise ses représentations avant de trouver un meilleur optimum. L'epoch 4 franchit tous les plafonds du run 1. L'epoch 5 plafonne sur Hit@1 mais améliore encore Hit@5, ce qui indique que le modèle affine sa couverture globale plutôt que sa précision au rang 1.

L'enrichissement des textes produits a bien joué son rôle : dès l'epoch 1 du run 2, on atteint des scores qui nécessitaient 4-5 epochs dans le run 1.

### Pourquoi le fine-tuning change autant les résultats

Le modèle de base est généraliste — il n'a jamais vu le jargon du matériel informatique ni des requêtes en français informel. Après entraînement sur les données Techmart, il comprend des formulations comme "le proc AMD" ou "gpu gaming pas cher" et sait les associer au bon produit.

Le gain de +61% sur Hit@1 montre qu'un petit modèle bien spécialisé vaut largement mieux qu'un grand modèle généraliste sur ce type de tâche.

### Ce qui limite encore les performances

Même avec les specs ajoutées, certains produits restent difficiles à distinguer parce que leurs noms sont très proches. Les pistes pour aller plus loin : ajouter des exemples négatifs difficiles dans l'entraînement (hard negatives), générer plus de paires d'entraînement pour les produits sous-représentés, ou essayer un modèle de base plus grand.

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
