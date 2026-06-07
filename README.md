# Techmart — Assistant Sémantique de Réserve

Système de recherche intelligent pour les employés d'un magasin de matériel informatique. Permet de **localiser** n'importe quel article dans la réserve et de **recommander des produits** adaptés au besoin d'un client — sans API externe, entièrement basé sur un modèle fine-tuné localement.

---

## Stack

| Couche | Technologie |
|---|---|
| Modèle | Sentence-transformer fine-tuné (`paraphrase-multilingual-MiniLM-L12-v2`) |
| Base de données | MongoDB Atlas — base `techmart` |
| Backend | Python 3.11 |
| Interface | Streamlit |
| Entraînement | `sentence-transformers` · `MultipleNegativesRankingLoss` |

---

## Installation

```bash
# 1. Cloner le repo
git clone https://github.com/your-org/techmart.git && cd techmart

# 2. Créer le venv et installer les dépendances
python3 -m venv .venv
source .venv/bin/activate          # Windows : .venv\Scripts\activate
pip install -r requirements.txt

# 3. Configurer la base de données
cp .env.example .env
# → Renseigner MONGODB_URI dans .env

# 4. Lancer l'application
streamlit run app.py
```

---

## Fonctionnalités

### 🔍 Mode Localisation
> *« Où est la RTX 4080 MSI ? »*

Retrouve l'emplacement exact d'un article dans la réserve :
- Zone · Rayon · Étagère · Position (ex : `D-2-5-6`)
- Quantité en stock
- SKU et prix

### 💡 Mode Conseil Client
> *« Un client veut monter un PC gaming avec 800€, que lui proposer ? »*

Recommande les produits adaptés selon :
- L'usage (gaming, bureautique, montage vidéo, streaming…)
- Le budget (filtrage par prix min/max)
- La disponibilité en stock

### ⚖️ Comparaison
> *« SSD NVMe Samsung vs WD, lequel choisir ? »*

Présente plusieurs produits côte à côte avec leurs specs.

---

## Architecture

```
Requête employé (langage naturel)
        │
        ▼
backend/retriever.py
  ├── Extraction automatique des filtres
  │     (budget, catégorie, tri demandé)
  ├── Encodage sémantique de la requête
  ├── Cosine similarity sur les embeddings produits
  └── Jointure MongoDB → stock + emplacement
        │
        ▼
backend/llm_agent.py
  ├── Détection d'intention (localisation / conseil / comparaison)
  └── Formatage Markdown de la réponse
        │
        ▼
app.py — Interface Streamlit
  ├── Onglet "🔍 Assistant"  (chat)
  └── Onglet "📈 Entraînement" (métriques live)
```

---

## Structure MongoDB (`techmart`)

| Collection | Contenu | Volume |
|---|---|---|
| `products` | Catalogue (SKU, nom, prix, specs) | 1 000 |
| `inventory` | Stock + lien produit↔emplacement | 1 000 |
| `locations` | Emplacements physiques (Zone-R-E-P) | 2 400 |
| `product_embeddings` | Texte encodé + vecteurs modèle | 1 000 |
| `training_data` | Paires (query, product_text) | 3 253 |
| `training_runs` | Métriques d'entraînement par epoch | — |
| `search_logs` | Historique des recherches | — |
| `categories` | 20 catégories de produits | 20 |
| `brands` | 42 marques | 42 |

---

## Pipeline d'entraînement

```bash
# Fine-tuner le modèle (3 epochs, batch 16)
python training/train.py --epochs 3 --batch-size 16

# Évaluer sans ré-entraîner
python training/evaluate.py
```

```
training_data (MongoDB · 3 253 paires)
        │  prepare_data.py — split 80/20
        ▼
  Train : 2 602  |  Val : 651
        │
        ▼  train.py
  Modèle de base : paraphrase-multilingual-MiniLM-L12-v2
  Loss           : MultipleNegativesRankingLoss
  Évaluation     : Hit@1 · Hit@5 · MRR@10 après chaque epoch
  Log            : MongoDB training_runs (visible dans l'app)
  Sauvegarde     : models/techmart_retriever/
        │
        ▼
  product_embeddings mis à jour dans MongoDB
```

---

## Résultats d'entraînement

> **Run** : `run_20260607_195318` · **Durée** : 34m40s · **Machine** : CPU (MacBook, Apple Silicon) · **Date** : 2026-06-07

### Configuration

| Paramètre | Valeur |
|---|---|
| Modèle de base | `paraphrase-multilingual-MiniLM-L12-v2` (22M params) |
| Loss | `MultipleNegativesRankingLoss` |
| Epochs | 5 |
| Batch size | 32 |
| Train samples | 2 602 paires (query, product_text) |
| Val samples | 651 paires |
| Produits uniques en val | 213 |
| Warmup steps | 8 (10% de l'epoch 1) |

### Métriques finales — modèle fine-tuné vs base

| Métrique | Modèle de base | Fine-tuné | Gain absolu | Gain relatif |
|---|---|---|---|---|
| **Hit@1** | 0.2826 | **0.4439** | +0.1613 | **+57%** |
| **Hit@5** | 0.5684 | **0.8618** | +0.2934 | **+52%** |
| **Hit@10** | 0.6851 | **0.9539** | +0.2688 | +39% |
| **MRR@10** | 0.4032 | **0.6214** | +0.2182 | **+54%** |

### Interprétation des résultats

#### Ce que mesurent ces métriques

- **Hit@k** : pour une requête donnée, le bon produit apparaît-il dans les k premiers résultats ?  
- **MRR@10** (*Mean Reciprocal Rank*) : si le bon produit est en position 3, le score est 1/3. Plus proche de 1 = plus le modèle place le bon produit en tête.

#### Lecture des chiffres

**Hit@1 = 44,4%** — Le bon produit est le 1er résultat dans 44% des cas. Ce score reflète la **difficulté intrinsèque** du corpus : 651 requêtes couvrent 213 produits distincts, dont beaucoup se ressemblent fortement (ex : plusieurs variantes de processeurs Intel i5 ou d'alimentations Corsair). Le modèle doit distinguer des produits très proches avec des requêtes parfois vagues comme *"le proc AMD"*.

**Hit@5 = 86,2%** — Pour un employé qui scanne 5 résultats, la bonne réponse est présente dans **86% des cas**. C'est le chiffre le plus pertinent pour l'usage réel : en quelques secondes de lecture, l'employé trouve l'article. Ce score passe de 57% (base) à 86% (fine-tuné), soit +29 points.

**Hit@10 = 95,4%** — Le modèle ne "rate" complètement" que 4,6% des requêtes — un score quasi-exhaustif qui confirme que le domaine est bien couvert.

**MRR@10 = 0,62** — Le bon produit se trouve en moyenne à la position **1/0,62 ≈ 1,6**. Avant fine-tuning, cette position était 1/0,40 ≈ 2,5. Le modèle a donc gagné ~1 rang en moyenne.

#### Pourquoi le fine-tuning est si efficace ici

Le modèle de base (`paraphrase-multilingual-MiniLM-L12-v2`) est entraîné sur du texte général multilingue — il ne "connaît" pas le jargon du matériel informatique ni les conventions de nommage des produits. Le fine-tuning sur les 2 602 paires du catalogue Techmart lui apprend :

1. **Le vocabulaire du domaine** — *"proc"*, *"gpu gaming"*, *"SSD nvme pas cher"* → produit informatique précis
2. **La langue informelle française** — les requêtes comme *"donne moi le ryzen 7"* ou *"dalle oled 1ms lg"* sont comprises
3. **La granularité produit** — distinguer un i5-12600K d'un i5-13400F à partir d'une description partielle

Le gain de +57% sur Hit@1 montre que **l'adaptation au domaine compte davantage que la taille du modèle** pour ce type de tâche spécialisée.

#### Limites et axes d'amélioration

| Limite observée | Cause probable | Solution envisageable |
|---|---|---|
| Hit@1 plafonne à 44% | Descriptions produits génériques (*"matériel informatique haute performance"*) | Enrichir `product_text` avec les specs (socket, mémoire, TDP…) |
| Confusion entre variantes proches | Pas de *hard negatives* dans l'entraînement | Ajouter `MultipleNegativesRankingLoss` avec négatifs difficiles |
| Pas de courbe de loss par epoch | Bug du callback (corrigé dans `train.py`) | Re-lancer avec `TechmartEvaluator` pour suivre la progression |
| 2 602 exemples seulement | Couverture inégale des 1 000 produits | Générer davantage de paires (augmentation de données) |

---

## Variables d'environnement

| Variable | Description |
|---|---|
| `MONGODB_URI` | URI de connexion MongoDB Atlas |

Aucune clé API externe requise.

---

## Structure du projet

```
Techmart/
├── app.py                    # Interface Streamlit (2 onglets)
├── requirements.txt
├── .env.example
├── backend/
│   ├── database.py           # Requêtes MongoDB + jointures
│   ├── retriever.py          # Moteur de recherche sémantique
│   ├── llm_agent.py          # Formatage des réponses
│   └── tools.py              # (réservé aux extensions futures)
├── training/
│   ├── prepare_data.py       # Chargement + split des données
│   ├── train.py              # Fine-tuning + logging MongoDB
│   └── evaluate.py           # Hit@k · MRR@10
├── scripts/
│   └── seed_db.py            # (données de démo initiales)
└── models/                   # Modèle fine-tuné (gitignored)
    └── techmart_retriever/
```
