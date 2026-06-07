TOOLS = [
    {
        "name": "rechercher_produits",
        "description": (
            "Recherche des produits dans le catalogue Techmart. "
            "Utilise cet outil pour : localiser un article, filtrer par budget, "
            "trier par prix ou nouveauté, vérifier le stock. "
            "Retourne nom, prix, specs, emplacement en réserve et quantité en stock."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Recherche textuelle libre sur le nom, la marque ou les specs. "
                        "Ex: 'RTX 4080', 'SSD Samsung 1To', 'clavier mécanique'"
                    ),
                },
                "categorie": {
                    "type": "string",
                    "description": (
                        "Filtrer par catégorie. Valeurs possibles : "
                        "Processeur, Carte graphique, Mémoire RAM, Carte mère, "
                        "Alimentation, Boîtier, Refroidissement, SSD NVMe, SSD SATA, "
                        "Disque dur HDD, Disque externe, Moniteur, Clavier, Souris, "
                        "Casque audio, Webcam, Carte réseau, Switch réseau, "
                        "Imprimante, Accessoire"
                    ),
                },
                "marque": {
                    "type": "string",
                    "description": "Filtrer par marque. Ex: Intel, AMD, Samsung, Corsair, ASUS...",
                },
                "budget_max": {
                    "type": "number",
                    "description": "Prix maximum en euros (inclus). Ex: 300 pour 'moins de 300€'",
                },
                "budget_min": {
                    "type": "number",
                    "description": "Prix minimum en euros (inclus). Ex: 500 pour 'haut de gamme à partir de 500€'",
                },
                "en_stock": {
                    "type": "boolean",
                    "description": "Si true, ne retourne que les articles disponibles en stock (quantité > 0)",
                },
                "tri": {
                    "type": "string",
                    "enum": ["pertinence", "prix_croissant", "prix_decroissant", "plus_recent", "stock_decroissant"],
                    "description": (
                        "Ordre de tri des résultats : "
                        "'pertinence' (défaut), "
                        "'prix_croissant' (moins cher en premier — pour budget serré), "
                        "'prix_decroissant' (plus cher en premier — pour haut de gamme), "
                        "'plus_recent' (nouveautés en premier), "
                        "'stock_decroissant' (le plus dispo en premier)"
                    ),
                },
                "limit": {
                    "type": "integer",
                    "description": "Nombre maximum de résultats (défaut 6, max 10)",
                },
            },
        },
    },
    {
        "name": "comparer_produits",
        "description": (
            "Compare côte à côte plusieurs produits (prix, specs, stock, emplacement). "
            "Utilise cet outil quand le client hésite entre plusieurs modèles "
            "ou quand tu veux présenter les meilleures options. "
            "Fournir les SKUs exacts des produits à comparer."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "skus": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Liste de 2 à 4 SKUs à comparer. Ex: ['P-INT-0001', 'P-AMD-0005']",
                }
            },
            "required": ["skus"],
        },
    },
    {
        "name": "get_produit_par_sku",
        "description": (
            "Récupère tous les détails d'un produit par son SKU : "
            "prix, specs techniques, stock disponible, emplacement exact en réserve. "
            "Utilise cet outil quand l'employé connaît la référence exacte."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "sku": {
                    "type": "string",
                    "description": "Le SKU du produit. Ex: P-INT-0001, P-AMD-0023",
                }
            },
            "required": ["sku"],
        },
    },
    {
        "name": "lister_categories",
        "description": "Liste toutes les catégories de produits disponibles dans le magasin.",
        "input_schema": {"type": "object", "properties": {}},
    },
]
