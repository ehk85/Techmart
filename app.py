import streamlit as st
from backend.database import lister_categories, stats_stock
from backend.retriever import get_retriever

st.set_page_config(
    page_title="Techmart",
    page_icon=None,
    layout="wide",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background-color: #f9fafb;
    }

    /* Header */
    .app-header {
        padding: 2rem 0 1.5rem 0;
        border-bottom: 1px solid #e5e7eb;
        margin-bottom: 2rem;
    }
    .app-title {
        font-size: 1.4rem;
        font-weight: 700;
        color: #111827;
        margin: 0;
        letter-spacing: -0.02em;
    }
    .app-subtitle {
        font-size: 0.875rem;
        color: #6b7280;
        margin: 0.2rem 0 0 0;
    }

    /* Barre de recherche */
    .stTextInput > div > div > input {
        border-radius: 8px;
        border: 1.5px solid #d1d5db;
        padding: 0.65rem 1rem;
        font-size: 0.95rem;
        background: white;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        transition: border-color 0.15s;
    }
    .stTextInput > div > div > input:focus {
        border-color: #2563eb;
        box-shadow: 0 0 0 3px rgba(37,99,235,0.1);
    }

    /* Selectbox */
    .stSelectbox > div > div {
        border-radius: 8px;
        border: 1.5px solid #d1d5db;
        background: white;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }

    /* Carte produit */
    .card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        padding: 1.1rem 1.3rem;
        margin-bottom: 0.75rem;
        box-shadow: 0 1px 4px rgba(0,0,0,0.05);
        transition: box-shadow 0.15s;
    }
    .card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        border-color: #d1d5db;
    }

    .card-top {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 0.5rem;
    }
    .card-name {
        font-size: 0.95rem;
        font-weight: 600;
        color: #111827;
        flex: 1;
        margin-right: 1rem;
    }
    .card-location {
        font-size: 1rem;
        font-weight: 700;
        color: #2563eb;
        background: #eff6ff;
        border: 1px solid #bfdbfe;
        border-radius: 6px;
        padding: 0.2rem 0.65rem;
        white-space: nowrap;
        letter-spacing: 0.03em;
    }

    .card-bottom {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        flex-wrap: wrap;
    }
    .card-price {
        font-size: 0.85rem;
        font-weight: 600;
        color: #374151;
    }
    .card-meta {
        font-size: 0.82rem;
        color: #9ca3af;
    }
    .card-sku {
        font-size: 0.78rem;
        color: #9ca3af;
        margin-top: 0.35rem;
    }
    .badge {
        display: inline-block;
        font-size: 0.75rem;
        font-weight: 600;
        border-radius: 20px;
        padding: 0.15rem 0.55rem;
    }
    .badge-ok   { background: #dcfce7; color: #166534; }
    .badge-low  { background: #fef3c7; color: #92400e; }
    .badge-zero { background: #fee2e2; color: #991b1b; }

    .dot {
        display: inline-block;
        width: 4px; height: 4px;
        border-radius: 50%;
        background: #d1d5db;
        vertical-align: middle;
        margin: 0 0.3rem;
    }

    /* Stats initiales */
    .stat-block {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        padding: 1.2rem 1.5rem;
        text-align: center;
    }
    .stat-val {
        font-size: 2rem;
        font-weight: 700;
        color: #111827;
        line-height: 1;
    }
    .stat-lbl {
        font-size: 0.82rem;
        color: #6b7280;
        margin-top: 0.3rem;
    }

    /* Résultat count */
    .result-count {
        font-size: 0.82rem;
        color: #6b7280;
        margin-bottom: 1rem;
    }

    /* Masquer éléments Streamlit */
    #MainMenu, footer, .stDeployButton { visibility: hidden; }
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
</style>
""", unsafe_allow_html=True)


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
    <p class="app-title">Techmart</p>
    <p class="app-subtitle">Recherche en réserve</p>
</div>
""", unsafe_allow_html=True)


# ── Barre de recherche + filtres ──────────────────────────────────────────────
col_q, col_cat, col_stock = st.columns([4, 2, 1])

with col_q:
    query = st.text_input(
        "q",
        placeholder="Rechercher un article — nom, marque, référence...",
        label_visibility="collapsed",
    )

with col_cat:
    try:
        cats = ["Toutes catégories"] + lister_categories()
    except Exception:
        cats = ["Toutes catégories"]
    categorie = st.selectbox("cat", cats, label_visibility="collapsed")

with col_stock:
    en_stock = st.checkbox("En stock", value=False)


# ── Résultats ─────────────────────────────────────────────────────────────────
if query.strip():
    try:
        retriever = get_retriever()

        full_query = query.strip()
        if categorie != "Toutes catégories":
            full_query += f" {categorie}"

        results = retriever.search(full_query, top_k=10)

        if en_stock:
            results = [r for r in results if (r.get("stock") or 0) > 0]
        if categorie != "Toutes catégories":
            results = [r for r in results if r.get("category_name", "").lower() == categorie.lower()]

        if not results:
            st.markdown("""
<div style="text-align:center;padding:3rem 0;color:#9ca3af;">
    Aucun résultat. Essayez avec des termes plus généraux.
</div>
""", unsafe_allow_html=True)
        else:
            st.markdown(f'<p class="result-count">{len(results)} résultat(s)</p>', unsafe_allow_html=True)

            for r in results:
                stock      = r.get("stock") or 0
                emplacement = r.get("emplacement") or "—"
                prix       = r.get("price", 0)
                specs      = r.get("specs") or {}
                brand      = r.get("brand_name", "")
                category   = r.get("category_name", "")

                if stock == 0:
                    badge = '<span class="badge badge-zero">Rupture</span>'
                elif stock <= 3:
                    badge = f'<span class="badge badge-low">{stock} restant(s)</span>'
                else:
                    badge = f'<span class="badge badge-ok">{stock} en stock</span>'

                spec_parts = []
                if specs.get("socket"):      spec_parts.append(specs["socket"])
                if specs.get("cores"):       spec_parts.append(f"{specs['cores']} cœurs")
                if specs.get("memory"):      spec_parts.append(str(specs["memory"]))
                if specs.get("form_factor"): spec_parts.append(specs["form_factor"])
                if specs.get("efficiency"):  spec_parts.append(specs["efficiency"])
                if specs.get("read"):        spec_parts.append(f"lect. {specs['read']}")
                specs_str = " · ".join(spec_parts)

                meta_line = f"{brand}"
                if category:
                    meta_line += f'<span class="dot"></span>{category}'
                if specs_str:
                    meta_line += f'<span class="dot"></span>{specs_str}'

                st.markdown(f"""
<div class="card">
    <div class="card-top">
        <div class="card-name">{r['name']}</div>
        <div class="card-location">{emplacement}</div>
    </div>
    <div class="card-bottom">
        <span class="card-price">{prix:.2f} €</span>
        <span class="dot"></span>
        <span class="card-meta">{meta_line}</span>
        <span class="dot"></span>
        {badge}
    </div>
    <div class="card-sku">SKU : {r.get('sku', '—')}</div>
</div>
""", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Erreur : {e}")

else:
    # Page d'accueil — stats
    st.markdown("<br>", unsafe_allow_html=True)
    try:
        stats = stats_stock()
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"""
<div class="stat-block">
    <div class="stat-val">{stats['total_articles']}</div>
    <div class="stat-lbl">Produits au catalogue</div>
</div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
<div class="stat-block">
    <div class="stat-val">{stats['en_stock']}</div>
    <div class="stat-lbl">Disponibles en stock</div>
</div>""", unsafe_allow_html=True)
        with c3:
            st.markdown(f"""
<div class="stat-block">
    <div class="stat-val" style="color:#dc2626">{stats['rupture_de_stock']}</div>
    <div class="stat-lbl">En rupture</div>
</div>""", unsafe_allow_html=True)
    except Exception:
        pass
