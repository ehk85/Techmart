import streamlit as st
from backend.database import lister_categories, stats_stock
from backend.retriever import get_retriever

st.set_page_config(
    page_title="Techmart — Recherche réserve",
    page_icon=None,
    layout="centered",
)

st.markdown("""
<style>
    /* Fond et texte */
    .stApp { background: #f5f5f5; }

    /* Carte produit */
    .product-card {
        background: white;
        border: 1px solid #ddd;
        border-radius: 6px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.75rem;
    }
    .product-name {
        font-size: 1rem;
        font-weight: 600;
        color: #1a1a1a;
        margin-bottom: 0.2rem;
    }
    .product-location {
        font-size: 1.3rem;
        font-weight: 700;
        color: #c0392b;
        letter-spacing: 0.05em;
    }
    .product-meta {
        font-size: 0.85rem;
        color: #555;
        margin-top: 0.3rem;
    }
    .stock-ok   { color: #27ae60; font-weight: 600; }
    .stock-low  { color: #e67e22; font-weight: 600; }
    .stock-zero { color: #c0392b; font-weight: 600; }

    /* Masquer le menu hamburger Streamlit */
    #MainMenu, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ── En-tête ──────────────────────────────────────────────────────────────────
st.markdown("## Recherche réserve — Techmart")
st.markdown("---")


# ── Filtres ───────────────────────────────────────────────────────────────────
col_search, col_cat, col_stock = st.columns([3, 2, 1])

with col_search:
    query = st.text_input(
        "Recherche",
        placeholder="Ex : RTX 4080, proc AMD, SSD Samsung...",
        label_visibility="collapsed",
    )

with col_cat:
    try:
        categories = ["Toutes les catégories"] + lister_categories()
    except Exception:
        categories = ["Toutes les catégories"]
    categorie = st.selectbox("Catégorie", categories, label_visibility="collapsed")

with col_stock:
    en_stock = st.checkbox("En stock", value=False)


# ── Résultats ─────────────────────────────────────────────────────────────────
if query.strip():
    try:
        retriever = get_retriever()

        # Construire la requête complète en intégrant les filtres UI
        full_query = query.strip()
        if categorie != "Toutes les catégories":
            full_query += f" {categorie}"
        if en_stock:
            full_query += " en stock"

        results = retriever.search(full_query, top_k=8)

        # Filtre en_stock côté Python si nécessaire
        if en_stock:
            results = [r for r in results if (r.get("stock") or 0) > 0]

        # Filtre catégorie côté Python si sélectionné
        if categorie != "Toutes les catégories":
            results = [
                r for r in results
                if r.get("category_name", "").lower() == categorie.lower()
            ]

        if not results:
            st.info("Aucun produit trouvé. Essayez avec des termes plus généraux.")
        else:
            st.markdown(f"**{len(results)} résultat(s)**")
            for r in results:
                stock = r.get("stock") or 0
                emplacement = r.get("emplacement") or "—"
                prix = r.get("price", 0)
                specs = r.get("specs") or {}

                if stock == 0:
                    stock_html = '<span class="stock-zero">Rupture de stock</span>'
                elif stock <= 3:
                    stock_html = f'<span class="stock-low">{stock} en stock</span>'
                else:
                    stock_html = f'<span class="stock-ok">{stock} en stock</span>'

                # Specs lisibles
                spec_parts = []
                if specs.get("socket"):     spec_parts.append(specs["socket"])
                if specs.get("cores"):      spec_parts.append(f"{specs['cores']} cœurs")
                if specs.get("memory"):     spec_parts.append(str(specs["memory"]))
                if specs.get("form_factor"):spec_parts.append(str(specs["form_factor"]))
                if specs.get("efficiency"): spec_parts.append(str(specs["efficiency"]))
                if specs.get("read"):       spec_parts.append(f"lect. {specs['read']}")
                specs_txt = " · ".join(spec_parts) if spec_parts else ""

                meta_parts = [f"{prix:.2f} €", r.get("brand_name", ""), r.get("category_name", "")]
                if specs_txt:
                    meta_parts.append(specs_txt)
                meta = " · ".join(p for p in meta_parts if p)

                st.markdown(f"""
<div class="product-card">
    <div class="product-name">{r['name']}</div>
    <div class="product-location">{emplacement}</div>
    <div class="product-meta">{meta} &nbsp;|&nbsp; {stock_html}</div>
    <div class="product-meta" style="color:#999;font-size:0.78rem;">SKU : {r.get('sku', '—')}</div>
</div>
""", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Erreur : {e}")

elif not query.strip():
    # Etat initial — stats rapides
    st.markdown(" ")
    try:
        stats = stats_stock()
        c1, c2, c3 = st.columns(3)
        c1.metric("Produits", stats["total_articles"])
        c2.metric("En stock", stats["en_stock"])
        c3.metric("Rupture", stats["rupture_de_stock"])
    except Exception:
        pass
