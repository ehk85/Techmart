"""Peuple la base MongoDB avec un catalogue d'articles pour Techmart."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv

load_dotenv()

from backend.database import get_collection

ARTICLES = [
    # ── PROCESSEURS (CPU) ─────────────────────────────────────────────────
    {
        "reference": "TM-CPU-001",
        "nom": "Processeur Intel Core i7-13700K",
        "categorie": "CPU",
        "marque": "Intel",
        "modele": "Core i7-13700K",
        "description": "16 cœurs, 3.4 GHz boost 5.4 GHz, socket LGA1700, sans ventilateur",
        "prix": 389.99,
        "stock": 8,
        "emplacement": {"rayon": "A", "etagere": 1, "position": 2},
        "tags": ["processeur", "cpu", "intel", "i7", "13ème génération", "lga1700"],
    },
    {
        "reference": "TM-CPU-002",
        "nom": "Processeur AMD Ryzen 5 7600X",
        "categorie": "CPU",
        "marque": "AMD",
        "modele": "Ryzen 5 7600X",
        "description": "6 cœurs 12 threads, 4.7 GHz boost 5.3 GHz, socket AM5",
        "prix": 249.99,
        "stock": 12,
        "emplacement": {"rayon": "A", "etagere": 1, "position": 4},
        "tags": ["processeur", "cpu", "amd", "ryzen", "5", "am5"],
    },
    {
        "reference": "TM-CPU-003",
        "nom": "Processeur Intel Core i9-13900K",
        "categorie": "CPU",
        "marque": "Intel",
        "modele": "Core i9-13900K",
        "description": "24 cœurs, 3.0 GHz boost 5.8 GHz, socket LGA1700, haut de gamme",
        "prix": 589.99,
        "stock": 3,
        "emplacement": {"rayon": "A", "etagere": 1, "position": 1},
        "tags": ["processeur", "cpu", "intel", "i9", "haut de gamme", "lga1700"],
    },
    {
        "reference": "TM-CPU-004",
        "nom": "Processeur AMD Ryzen 9 7950X",
        "categorie": "CPU",
        "marque": "AMD",
        "modele": "Ryzen 9 7950X",
        "description": "16 cœurs 32 threads, 4.5 GHz boost 5.7 GHz, socket AM5, workstation",
        "prix": 699.99,
        "stock": 2,
        "emplacement": {"rayon": "A", "etagere": 1, "position": 3},
        "tags": ["processeur", "cpu", "amd", "ryzen", "9", "workstation", "am5"],
    },
    # ── RAM ───────────────────────────────────────────────────────────────
    {
        "reference": "TM-RAM-001",
        "nom": "RAM Corsair Vengeance 16 Go DDR5",
        "categorie": "RAM",
        "marque": "Corsair",
        "modele": "Vengeance DDR5-5600 16 Go",
        "description": "2x8 Go DDR5 5600 MHz, CL36, compatible Intel XMP 3.0",
        "prix": 79.99,
        "stock": 20,
        "emplacement": {"rayon": "B", "etagere": 1, "position": 1},
        "tags": ["ram", "mémoire", "corsair", "vengeance", "ddr5", "16go"],
    },
    {
        "reference": "TM-RAM-002",
        "nom": "RAM Kingston Fury Beast 32 Go DDR4",
        "categorie": "RAM",
        "marque": "Kingston",
        "modele": "Fury Beast DDR4-3200 32 Go",
        "description": "2x16 Go DDR4 3200 MHz, CL16, noir",
        "prix": 64.99,
        "stock": 15,
        "emplacement": {"rayon": "B", "etagere": 1, "position": 2},
        "tags": ["ram", "mémoire", "kingston", "fury", "beast", "ddr4", "32go"],
    },
    {
        "reference": "TM-RAM-003",
        "nom": "RAM G.Skill Trident Z5 64 Go DDR5",
        "categorie": "RAM",
        "marque": "G.Skill",
        "modele": "Trident Z5 DDR5-6000 64 Go",
        "description": "2x32 Go DDR5 6000 MHz, CL30, RGB, haute performance",
        "prix": 199.99,
        "stock": 6,
        "emplacement": {"rayon": "B", "etagere": 1, "position": 3},
        "tags": ["ram", "mémoire", "gskill", "trident", "ddr5", "64go", "rgb"],
    },
    # ── SSD ───────────────────────────────────────────────────────────────
    {
        "reference": "TM-SSD-001",
        "nom": "SSD Samsung 980 Pro 1 To NVMe",
        "categorie": "SSD",
        "marque": "Samsung",
        "modele": "980 Pro 1 To",
        "description": "PCIe 4.0 NVMe M.2, 7000 Mo/s lecture, 5000 Mo/s écriture",
        "prix": 89.99,
        "stock": 18,
        "emplacement": {"rayon": "B", "etagere": 2, "position": 1},
        "tags": ["ssd", "samsung", "980 pro", "nvme", "m2", "pcie4", "1to"],
    },
    {
        "reference": "TM-SSD-002",
        "nom": "SSD WD Black SN850X 2 To NVMe",
        "categorie": "SSD",
        "marque": "WD",
        "modele": "Black SN850X 2 To",
        "description": "PCIe 4.0 NVMe M.2, 7300 Mo/s lecture, idéal gaming",
        "prix": 149.99,
        "stock": 9,
        "emplacement": {"rayon": "B", "etagere": 2, "position": 2},
        "tags": ["ssd", "wd", "western digital", "black", "sn850x", "nvme", "2to", "gaming"],
    },
    {
        "reference": "TM-SSD-003",
        "nom": "SSD Crucial MX500 500 Go SATA",
        "categorie": "SSD",
        "marque": "Crucial",
        "modele": "MX500 500 Go",
        "description": "2.5 pouces SATA III, 560 Mo/s lecture, bon rapport qualité/prix",
        "prix": 44.99,
        "stock": 25,
        "emplacement": {"rayon": "B", "etagere": 2, "position": 3},
        "tags": ["ssd", "crucial", "mx500", "sata", "500go", "2.5 pouces"],
    },
    # ── DISQUES DURS (HDD) ────────────────────────────────────────────────
    {
        "reference": "TM-HDD-001",
        "nom": "Disque dur Seagate BarraCuda 4 To",
        "categorie": "HDD",
        "marque": "Seagate",
        "modele": "BarraCuda 4 To",
        "description": "3.5 pouces SATA III, 7200 tr/min, cache 256 Mo",
        "prix": 79.99,
        "stock": 10,
        "emplacement": {"rayon": "B", "etagere": 3, "position": 1},
        "tags": ["hdd", "disque dur", "seagate", "barracuda", "4to", "3.5 pouces"],
    },
    {
        "reference": "TM-HDD-002",
        "nom": "Disque dur WD Red Plus 8 To NAS",
        "categorie": "HDD",
        "marque": "WD",
        "modele": "Red Plus 8 To",
        "description": "3.5 pouces SATA, 5400 tr/min, optimisé pour NAS, CMR",
        "prix": 169.99,
        "stock": 5,
        "emplacement": {"rayon": "B", "etagere": 3, "position": 2},
        "tags": ["hdd", "disque dur", "wd", "red", "nas", "8to", "serveur"],
    },
    # ── CARTES GRAPHIQUES (GPU) ───────────────────────────────────────────
    {
        "reference": "TM-GPU-001",
        "nom": "Carte graphique NVIDIA RTX 4070 Ti 12 Go",
        "categorie": "GPU",
        "marque": "NVIDIA",
        "modele": "GeForce RTX 4070 Ti",
        "description": "12 Go GDDR6X, DLSS 3, ray tracing, 285W TDP",
        "prix": 799.99,
        "stock": 4,
        "emplacement": {"rayon": "C", "etagere": 1, "position": 1},
        "tags": ["gpu", "carte graphique", "nvidia", "rtx", "4070", "ti", "gaming", "dlss"],
    },
    {
        "reference": "TM-GPU-002",
        "nom": "Carte graphique AMD Radeon RX 7900 XTX 24 Go",
        "categorie": "GPU",
        "marque": "AMD",
        "modele": "Radeon RX 7900 XTX",
        "description": "24 Go GDDR6, FSR 3, 355W TDP, haut de gamme AMD",
        "prix": 999.99,
        "stock": 2,
        "emplacement": {"rayon": "C", "etagere": 1, "position": 2},
        "tags": ["gpu", "carte graphique", "amd", "radeon", "rx 7900", "xtx", "haut de gamme"],
    },
    {
        "reference": "TM-GPU-003",
        "nom": "Carte graphique NVIDIA RTX 4060 8 Go",
        "categorie": "GPU",
        "marque": "NVIDIA",
        "modele": "GeForce RTX 4060",
        "description": "8 Go GDDR6, DLSS 3, 115W TDP, excellent rapport qualité/prix",
        "prix": 299.99,
        "stock": 11,
        "emplacement": {"rayon": "C", "etagere": 1, "position": 3},
        "tags": ["gpu", "carte graphique", "nvidia", "rtx", "4060", "gaming", "milieu de gamme"],
    },
    # ── CARTES MÈRES ──────────────────────────────────────────────────────
    {
        "reference": "TM-MB-001",
        "nom": "Carte mère ASUS ROG Strix Z790-E",
        "categorie": "Carte mère",
        "marque": "ASUS",
        "modele": "ROG Strix Z790-E Gaming WiFi",
        "description": "Socket LGA1700, DDR5, ATX, WiFi 6E, Bluetooth 5.3, USB4",
        "prix": 449.99,
        "stock": 5,
        "emplacement": {"rayon": "A", "etagere": 2, "position": 1},
        "tags": ["carte mère", "motherboard", "asus", "rog", "z790", "lga1700", "ddr5"],
    },
    {
        "reference": "TM-MB-002",
        "nom": "Carte mère MSI MAG B650 Tomahawk WiFi",
        "categorie": "Carte mère",
        "marque": "MSI",
        "modele": "MAG B650 Tomahawk WiFi",
        "description": "Socket AM5, DDR5, ATX, WiFi 6E, bon rapport qualité/prix",
        "prix": 229.99,
        "stock": 7,
        "emplacement": {"rayon": "A", "etagere": 2, "position": 2},
        "tags": ["carte mère", "motherboard", "msi", "mag", "b650", "am5", "ddr5", "tomahawk"],
    },
    # ── ALIMENTATIONS (PSU) ───────────────────────────────────────────────
    {
        "reference": "TM-PSU-001",
        "nom": "Alimentation Corsair RM850x 850W",
        "categorie": "Alimentation",
        "marque": "Corsair",
        "modele": "RM850x 850W",
        "description": "850W, 80+ Gold, modulaire, silencieux, 10 ans garantie",
        "prix": 129.99,
        "stock": 9,
        "emplacement": {"rayon": "D", "etagere": 1, "position": 1},
        "tags": ["alimentation", "psu", "corsair", "rm850x", "850w", "gold", "modulaire"],
    },
    {
        "reference": "TM-PSU-002",
        "nom": "Alimentation be quiet! Dark Power Pro 1000W",
        "categorie": "Alimentation",
        "marque": "be quiet!",
        "modele": "Dark Power Pro 1000W",
        "description": "1000W, 80+ Titanium, modulaire, ultra silencieux",
        "prix": 229.99,
        "stock": 3,
        "emplacement": {"rayon": "D", "etagere": 1, "position": 2},
        "tags": ["alimentation", "psu", "be quiet", "dark power", "1000w", "titanium", "silencieux"],
    },
    # ── BOÎTIERS ─────────────────────────────────────────────────────────
    {
        "reference": "TM-CASE-001",
        "nom": "Boîtier NZXT H510 Flow",
        "categorie": "Boîtier",
        "marque": "NZXT",
        "modele": "H510 Flow",
        "description": "Mid-tower ATX, façade mesh, 2 ventilateurs inclus, USB-C, noir",
        "prix": 89.99,
        "stock": 6,
        "emplacement": {"rayon": "D", "etagere": 2, "position": 1},
        "tags": ["boîtier", "case", "nzxt", "h510", "atx", "mid tower", "mesh"],
    },
    {
        "reference": "TM-CASE-002",
        "nom": "Boîtier Fractal Design Torrent",
        "categorie": "Boîtier",
        "marque": "Fractal Design",
        "modele": "Torrent ATX",
        "description": "Mid-tower ATX, airflow optimisé, 2x180mm + 3x140mm ventilateurs, blanc",
        "prix": 169.99,
        "stock": 4,
        "emplacement": {"rayon": "D", "etagere": 2, "position": 2},
        "tags": ["boîtier", "case", "fractal design", "torrent", "atx", "airflow"],
    },
    # ── REFROIDISSEMENT ───────────────────────────────────────────────────
    {
        "reference": "TM-COOL-001",
        "nom": "Ventirad Noctua NH-D15",
        "categorie": "Refroidissement",
        "marque": "Noctua",
        "modele": "NH-D15",
        "description": "Double tour, 2x ventilateurs 140mm NF-A15, compatible LGA1700/AM5",
        "prix": 99.99,
        "stock": 8,
        "emplacement": {"rayon": "E", "etagere": 1, "position": 1},
        "tags": ["refroidissement", "ventirad", "noctua", "nh-d15", "air cooling", "silencieux"],
    },
    {
        "reference": "TM-COOL-002",
        "nom": "AIO Corsair iCUE H150i Elite 360mm",
        "categorie": "Refroidissement",
        "marque": "Corsair",
        "modele": "iCUE H150i Elite Capellix XT 360mm",
        "description": "Watercooling AIO 360mm, 3x ventilateurs RGB 120mm, LCD display",
        "prix": 199.99,
        "stock": 0,
        "emplacement": {"rayon": "E", "etagere": 1, "position": 2},
        "tags": ["refroidissement", "aio", "watercooling", "corsair", "icue", "h150i", "360mm", "rgb"],
    },
    # ── PÉRIPHÉRIQUES ─────────────────────────────────────────────────────
    {
        "reference": "TM-PERI-001",
        "nom": "Clavier Logitech MX Keys",
        "categorie": "Périphérique",
        "marque": "Logitech",
        "modele": "MX Keys",
        "description": "Clavier sans fil rétroéclairé, multi-appareils, USB-C, Bluetooth",
        "prix": 109.99,
        "stock": 14,
        "emplacement": {"rayon": "E", "etagere": 2, "position": 1},
        "tags": ["clavier", "keyboard", "logitech", "mx keys", "sans fil", "bluetooth"],
    },
    {
        "reference": "TM-PERI-002",
        "nom": "Souris Razer DeathAdder V3",
        "categorie": "Périphérique",
        "marque": "Razer",
        "modele": "DeathAdder V3",
        "description": "Souris gaming filaire, 30000 DPI, ergonomique, 59g ultra légère",
        "prix": 79.99,
        "stock": 10,
        "emplacement": {"rayon": "E", "etagere": 2, "position": 2},
        "tags": ["souris", "mouse", "razer", "deathadder", "gaming", "filaire"],
    },
]


def seed():
    col = get_collection()

    # Supprime les données existantes pour repartir propre
    deleted = col.delete_many({})
    print(f"🗑️  {deleted.deleted_count} article(s) existant(s) supprimé(s).")

    result = col.insert_many(ARTICLES)
    print(f"✅ {len(result.inserted_ids)} articles insérés avec succès.")

    # Résumé par catégorie
    categories = col.distinct("categorie")
    print("\n📦 Articles par catégorie :")
    for cat in sorted(categories):
        count = col.count_documents({"categorie": cat})
        print(f"   {cat:<20} : {count} article(s)")


if __name__ == "__main__":
    seed()
