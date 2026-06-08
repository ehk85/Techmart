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
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ── Reset global ─────────────────────────────── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}
.stApp {
    background-color: #0f172a;
}
.block-container {
    padding: 0 !important;
    max-width: 100% !important;
}
#MainMenu, footer, .stDeployButton { visibility: hidden; }

/* ── Barre du haut ────────────────────────────── */
.topbar {
    background: #0f172a;
    border-bottom: 1px solid #1e293b;
    padding: 1rem 2.5rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.topbar-brand {
    font-size: 1.1rem;
    font-weight: 700;
    color: #f8fafc;
    letter-spacing: -0.02em;
}
.topbar-brand span {
    color: #3b82f6;
}
.topbar-right {
    font-size: 0.78rem;
    color: #475569;
}

/* ── Zone principale ──────────────────────────── */
.main-wrap {
    padding: 2rem 2.5rem;
}

/* ── Recherche ────────────────────────────────── */
.stTextInput > div > div > input {
    background: #1e293b !important;
    border: 1.5px solid #334155 !important;
    border-radius: 10px !important;
    color: #f1f5f9 !important;
    font-size: 1rem !important;
    padding: 0.75rem 1.1rem !important;
    box-shadow: none !important;
    caret-color: #3b82f6;
}
.stTextInput > div > div > input::placeholder {
    color: #475569 !important;
}
.stTextInput > div > div > input:focus {
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 3px rgba(59,130,246,0.15) !important;
}

/* ── Selectbox ────────────────────────────────── */
.stSelectbox > div > div {
    background: #1e293b !important;
    border: 1.5px solid #334155 !important;
    border-radius: 10px !important;
    color: #f1f5f9 !important;
}
.stSelectbox > div > div > div {
    color: #f1f5f9 !important;
}

/* ── Checkbox ─────────────────────────────────── */
.stCheckbox label {
    color: #94a3b8 !important;
    font-size: 0.875rem !important;
}
.stCheckbox > div {
    align-items: center !important;
    padding-top: 0.5rem;
}

/* ── Compteur résultats ───────────────────────── */
.count-label {
    font-size: 0.78rem;
    font-weight: 500;
    color: #475569;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin: 1.25rem 0 0.75rem 0;
}

/* ── Carte produit ────────────────────────────── */
.card {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 1.1rem 1.3rem;
    margin-bottom: 0.6rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    transition: border-color 0.15s, background 0.15s;
    cursor: default;
}
.card:hover {
    background: #243147;
    border-color: #3b82f6;
}

.card-left {
    flex: 1;
    min-width: 0;
}
.card-name {
    font-size: 0.95rem;
    font-weight: 600;
    color: #f1f5f9;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    margin-bottom: 0.3rem;
}
.card-meta {
    font-size: 0.8rem;
    color: #64748b;
    display: flex;
    align-items: center;
    gap: 0.4rem;
    flex-wrap: wrap;
}
.card-meta .sep { color: #334155; }
.card-price {
    font-weight: 600;
    color: #94a3b8;
}
.card-sku {
    font-size: 0.72rem;
    color: #475569;
    margin-top: 0.25rem;
    font-family: 'SF Mono', 'Fira Code', monospace;
}

.card-right {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 0.4rem;
    flex-shrink: 0;
}
.location-badge {
    font-size: 1rem;
    font-weight: 700;
    background: #1d4ed8;
    color: #fff;
    border-radius: 8px;
    padding: 0.3rem 0.75rem;
    letter-spacing: 0.05em;
    font-family: 'SF Mono', 'Fira Code', monospace;
}
.stock-badge {
    font-size: 0.72rem;
    font-weight: 600;
    border-radius: 20px;
    padding: 0.15rem 0.6rem;
    white-space: nowrap;
}
.ok   { background: rgba(34,197,94,0.12);  color: #4ade80; }
.low  { background: rgba(245,158,11,0.12); color: #fbbf24; }
.zero { background: rgba(239,68,68,0.12);  color: #f87171; }

/* ── Stats d'accueil ──────────────────────────── */
.stats-row {
    display: flex;
    gap: 1rem;
    margin-top: 3rem;
}
.stat-card {
    flex: 1;
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 1.5rem;
    text-align: center;
}
.stat-val {
    font-size: 2.4rem;
    font-weight: 700;
    color: #f1f5f9;
    letter-spacing: -0.03em;
    line-height: 1;
}
.stat-lbl {
    font-size: 0.78rem;
    color: #475569;
    margin-top: 0.5rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}

/* ── Message vide ─────────────────────────────── */
.empty-state {
    text-align: center;
    padding: 4rem 0;
    color: #334155;
    font-size: 0.9rem;
}
</style>
""", unsafe_allow_html=True)


# ── Topbar ────────────────────────────────────────────────────────────────────
try:
    stats = stats_stock()
    stats_txt = f"{stats['total_articles']} produits &nbsp;·&nbsp; {stats['en_stock']} en stock"
except Exception:
    stats_txt = ""

st.markdown(f"""
<div class="topbar">
    <span class="topbar-brand">Tech<span>mart</span></span>
    <span class="topbar-right">{stats_txt}</span>
</div>
<div class="main-wrap">
""", unsafe_allow_html=True)


# ── Recherche + filtres ───────────────────────────────────────────────────────
col_q, col_cat, col_stock = st.columns([5, 2, 1])

with col_q:
    query = st.text_input(
        "q",
        placeholder="Rechercher — nom, marque, référence, catégorie...",
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
            results = [r for r in results
                       if r.get("category_name", "").lower() == categorie.lower()]

        if not results:
            st.markdown('<div class="empty-state">Aucun résultat — essayez des termes plus généraux.</div>',
                        unsafe_allow_html=True)
        else:
            n = len(results)
            st.markdown(f'<p class="count-label">{n} résultat{"s" if n > 1 else ""}</p>',
                        unsafe_allow_html=True)

            for r in results:
                stock       = r.get("stock") or 0
                emplacement = r.get("emplacement") or "—"
                prix        = r.get("price", 0)
                specs       = r.get("specs") or {}
                brand       = r.get("brand_name", "")
                category    = r.get("category_name", "")
                name        = r.get("name", "")
                sku         = r.get("sku", "—")

                if stock == 0:
                    stock_html = '<span class="stock-badge zero">Rupture</span>'
                elif stock <= 3:
                    stock_html = f'<span class="stock-badge low">{stock} restant(s)</span>'
                else:
                    stock_html = f'<span class="stock-badge ok">{stock} en stock</span>'

                spec_parts = []
                if specs.get("socket"):      spec_parts.append(specs["socket"])
                if specs.get("cores"):       spec_parts.append(f"{specs['cores']} cœurs")
                if specs.get("memory"):      spec_parts.append(str(specs["memory"]))
                if specs.get("form_factor"): spec_parts.append(specs["form_factor"])
                if specs.get("efficiency"):  spec_parts.append(specs["efficiency"])
                if specs.get("read"):        spec_parts.append(f"lect. {specs['read']}")
                specs_str = " · ".join(spec_parts)

                meta_parts = []
                if brand:    meta_parts.append(f'<span class="card-price">{prix:.2f} €</span>')
                if category: meta_parts.append(category)
                if brand:    meta_parts.append(brand)
                if specs_str: meta_parts.append(specs_str)
                meta_html = ' <span class="sep">·</span> '.join(meta_parts)

                st.markdown(f"""
<div class="card">
    <div class="card-left">
        <div class="card-name">{name}</div>
        <div class="card-meta">{meta_html}</div>
        <div class="card-sku">{sku}</div>
    </div>
    <div class="card-right">
        <span class="location-badge">{emplacement}</span>
        {stock_html}
    </div>
</div>""", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Erreur : {e}")

else:
    # Page d'accueil
    try:
        stats = stats_stock()
        s = stats
        st.markdown(f"""
<div class="stats-row">
    <div class="stat-card">
        <div class="stat-val">{s['total_articles']}</div>
        <div class="stat-lbl">Produits</div>
    </div>
    <div class="stat-card">
        <div class="stat-val" style="color:#4ade80">{s['en_stock']}</div>
        <div class="stat-lbl">En stock</div>
    </div>
    <div class="stat-card">
        <div class="stat-val" style="color:#f87171">{s['rupture_de_stock']}</div>
        <div class="stat-lbl">En rupture</div>
    </div>
</div>""", unsafe_allow_html=True)
    except Exception:
        pass

st.markdown("</div>", unsafe_allow_html=True)
