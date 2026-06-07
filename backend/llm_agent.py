"""
Moteur de réponse Techmart — sans API externe.
Utilise le retriever sémantique (sentence-transformer fine-tuné) + MongoDB.
"""
from backend.retriever import get_retriever
from backend.database import log_search

# ── Formatage des résultats ───────────────────────────────────────────────────

def _fmt_specs(specs: dict) -> str:
    if not specs:
        return ""
    parts = []
    labels = {
        "cores": "Cœurs", "socket": "Socket", "tdp": "TDP",
        "memory": "Mémoire", "read": "Lecture", "write": "Écriture",
        "form_factor": "Format", "efficiency": "Efficacité", "modular": "Modulaire",
        "fans_included": "Ventilateurs", "rpm": "RPM", "panel": "Dalle",
        "response": "Réponse", "interface": "Interface", "cache": "Cache",
        "latency": "Latence", "pcie_slots": "Slots PCIe", "type": "Type",
    }
    for k, v in specs.items():
        label = labels.get(k, k)
        if isinstance(v, bool):
            v = "Oui" if v else "Non"
        parts.append(f"{label}: {v}")
    return " | ".join(parts)


def _fmt_product(i: int, p: dict) -> str:
    emplacement = p.get("emplacement") or "—"
    stock = p.get("stock", 0)
    stock_txt = f"{stock} unité(s)" if stock else "**⚠️ Rupture de stock**"
    specs_txt = _fmt_specs(p.get("specs") or {})

    lines = [
        f"**{i}. {p['name']}** — {p['price']:.2f} €",
        f"   📍 Emplacement : **{emplacement}** | Stock : {stock_txt}",
        f"   SKU : `{p['sku']}`",
    ]
    if specs_txt:
        lines.append(f"   🔧 {specs_txt}")
    return "\n".join(lines)


def _detect_intent(query: str) -> str:
    q = query.lower()
    if any(k in q for k in ["client", "conseille", "recommande", "proposition", "besoin", "usage", "utilisation"]):
        return "conseil"
    if any(k in q for k in ["comparer", "vs", "ou bien", "différence", "lequel", "laquelle"]):
        return "comparaison"
    if any(k in q for k in ["où est", "localise", "trouver", "réserve", "emplacement", "rayon"]):
        return "localisation"
    return "recherche"


def _build_response(query: str, results: list[dict], intent: str) -> str:
    if not results:
        return (
            "Aucun produit trouvé pour cette recherche.\n\n"
            "💡 Essayez de reformuler ou d'élargir votre recherche "
            "(ex: supprimer un filtre de budget ou de marque)."
        )

    blocks = [_fmt_product(i + 1, p) for i, p in enumerate(results)]
    body = "\n\n".join(blocks)

    headers = {
        "conseil":      f"💡 **{len(results)} recommandation(s)** pour votre client :\n\n",
        "comparaison":  f"⚖️ **Comparaison de {len(results)} produit(s)** :\n\n",
        "localisation": f"📍 **{len(results)} résultat(s) trouvé(s)** :\n\n",
        "recherche":    f"🔍 **{len(results)} produit(s) trouvé(s)** :\n\n",
    }

    header = headers.get(intent, headers["recherche"])

    footer = ""
    if intent == "conseil":
        footer = (
            "\n\n---\n*Conseil : privilégiez les articles avec le stock le plus élevé "
            "pour une disponibilité immédiate.*"
        )

    return header + body + footer


# ── Point d'entrée ────────────────────────────────────────────────────────────

def run_agent(user_query: str, chat_history: list[dict] | None = None) -> str:
    """Recherche sémantique + formatage de la réponse. Pas d'API externe."""
    try:
        retriever = get_retriever()
        results = retriever.search(user_query, top_k=5)
        log_search(user_query, results)
        intent = _detect_intent(user_query)
        return _build_response(user_query, results, intent)
    except Exception as e:
        return f"❌ Erreur lors de la recherche : {e}"
