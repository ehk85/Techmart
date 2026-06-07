import streamlit as st
from backend.database import lister_categories, stats_stock, get_training_runs
from backend.llm_agent import run_agent

st.set_page_config(
    page_title="Techmart — Assistant",
    page_icon="🖥️",
    layout="wide",
)

st.markdown(
    """
    <style>
    .main-header {
        background: linear-gradient(90deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        padding: 1.2rem 2rem;
        border-radius: 12px;
        margin-bottom: 1rem;
    }
    .main-header h1 { color: #e94560; margin: 0; font-size: 1.8rem; }
    .main-header p  { color: #a8b2d8; margin: 0.3rem 0 0; font-size: 0.9rem; }

    .metric-card {
        background: #1e2a3a;
        border: 1px solid #2d3f55;
        border-radius: 8px;
        padding: 0.8rem 1rem;
        text-align: center;
    }
    .metric-card .val  { font-size: 1.5rem; font-weight: bold; color: #e94560; }
    .metric-card .lbl  { font-size: 0.72rem; color: #a8b2d8; }

    .epoch-row { font-size: 0.85rem; }
    .status-running   { color: #ffc107; }
    .status-completed { color: #28a745; }
    .status-failed    { color: #dc3545; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🖥️ Techmart")
    st.divider()

    try:
        stats = stats_stock()
        st.markdown("#### 📊 Stock")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(
                f'<div class="metric-card"><div class="val">{stats["total_articles"]}</div>'
                '<div class="lbl">Produits</div></div>', unsafe_allow_html=True
            )
        with c2:
            st.markdown(
                f'<div class="metric-card"><div class="val">{stats["en_stock"]}</div>'
                '<div class="lbl">En stock</div></div>', unsafe_allow_html=True
            )
    except Exception as e:
        st.error(f"Stats indisponibles : {e}")

    st.divider()

    try:
        for cat in lister_categories():
            st.markdown(f"<small>· {cat}</small>", unsafe_allow_html=True)
    except Exception:
        pass

    st.divider()
    if st.button("🗑️ Vider la conversation"):
        st.session_state.messages = []
        st.rerun()

# ── Onglets ───────────────────────────────────────────────────────────────────
tab_chat, tab_training = st.tabs(["🔍 Assistant", "📈 Suivi d'entraînement"])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Assistant
# ═══════════════════════════════════════════════════════════════════════════════
with tab_chat:
    st.markdown(
        """
        <div class="main-header">
            <h1>🖥️ Techmart — Assistant</h1>
            <p>
                <b>Localisation</b> : retrouvez n'importe quel article dans la réserve. &nbsp;|&nbsp;
                <b>Conseil client</b> : recommandez les produits adaptés au besoin et au budget.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Suggestions rapides
    SUGGESTIONS = [
        ("📍", "Où est la RTX 4080 MSI ?"),
        ("💰", "GPU gaming moins de 400€ en stock"),
        ("🆕", "Processeurs AMD les plus récents"),
        ("🎯", "Client veut PC bureautique ~600€"),
        ("⚖️", "SSD NVMe Samsung vs WD"),
        ("🔝", "Cartes graphiques haut de gamme"),
    ]

    st.markdown("**Suggestions :**")
    cols = st.columns(len(SUGGESTIONS))
    for col, (icon, text) in zip(cols, SUGGESTIONS):
        with col:
            if st.button(f"{icon} {text}", key=f"sug_{text}", use_container_width=True):
                st.session_state.pending_query = text

    # Historique du chat
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if not st.session_state.messages:
        with st.chat_message("assistant"):
            st.markdown(
                "Bonjour ! Je suis l'assistant Techmart — propulsé par un modèle sémantique "
                "entraîné sur vos données.\n\n"
                "Je peux :\n"
                "- 📍 **Localiser** un article en réserve\n"
                "- 💡 **Conseiller** pour un client (budget, usage)\n"
                "- ⚖️ **Comparer** des produits\n"
                "- 💰 **Filtrer** par prix, marque ou disponibilité"
            )

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    def handle_query(query: str):
        st.session_state.messages.append({"role": "user", "content": query})
        with st.chat_message("user"):
            st.markdown(query)
        history = [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages[:-1]
        ]
        with st.chat_message("assistant"):
            with st.spinner("Recherche sémantique…"):
                response = run_agent(query, history)
            st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

    if "pending_query" in st.session_state:
        handle_query(st.session_state.pop("pending_query"))
        st.rerun()

    if prompt := st.chat_input("Ex : Client gaming 800€, que lui proposer ?"):
        handle_query(prompt)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Suivi d'entraînement
# ═══════════════════════════════════════════════════════════════════════════════
with tab_training:
    st.markdown("## 📈 Suivi d'entraînement du modèle")

    st.info(
        "Pour lancer un entraînement :\n"
        "```bash\n"
        "python training/train.py --epochs 3 --batch-size 16\n"
        "```\n"
        "Les métriques sont enregistrées automatiquement dans MongoDB et s'affichent ici.",
        icon="💡",
    )

    col_refresh, col_empty = st.columns([1, 5])
    with col_refresh:
        if st.button("🔄 Rafraîchir"):
            st.rerun()

    try:
        runs = get_training_runs(limit=10)
    except Exception as e:
        st.error(f"Impossible de charger les runs : {e}")
        runs = []

    if not runs:
        st.warning("Aucune run d'entraînement trouvée. Lancez d'abord `python training/train.py`.")
    else:
        for run in runs:
            status = run.get("status", "?")
            status_icon = {"running": "🟡", "completed": "✅", "failed": "❌"}.get(status, "❓")
            cfg = run.get("config", {})

            with st.expander(
                f"{status_icon} `{run['run_id']}` — "
                f"{cfg.get('epochs', '?')} epochs · "
                f"{cfg.get('train_samples', '?')} exemples · "
                f"statut : **{status}**",
                expanded=(status == "running"),
            ):
                # Infos générales
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.metric("Epochs", cfg.get("epochs", "—"))
                with c2:
                    st.metric("Batch size", cfg.get("batch_size", "—"))
                with c3:
                    st.metric("Train samples", cfg.get("train_samples", "—"))
                with c4:
                    st.metric("Val samples", cfg.get("val_samples", "—"))

                st.markdown(f"**Modèle de base :** `{run.get('model_base', '—')}`")

                # Tableau des métriques par epoch
                epochs_log = run.get("epochs_log", [])
                if epochs_log:
                    st.markdown("#### Métriques par epoch")

                    # Graphiques
                    import pandas as pd

                    df = pd.DataFrame(epochs_log)
                    df.set_index("epoch", inplace=True)

                    col_loss, col_metrics = st.columns(2)
                    with col_loss:
                        if "loss" in df.columns:
                            st.line_chart(df[["loss"]], use_container_width=True)
                            st.caption("Loss (↓ meilleur)")
                    with col_metrics:
                        metric_cols = [c for c in df.columns if c.startswith("hit") or c.startswith("mrr")]
                        if metric_cols:
                            st.line_chart(df[metric_cols], use_container_width=True)
                            st.caption("Hit@k / MRR@10 (↑ meilleur)")

                    # Tableau brut
                    st.dataframe(df.reset_index(), use_container_width=True)

                    # Meilleure epoch
                    if "hit@5" in df.columns:
                        best_epoch = df["hit@5"].idxmax()
                        best = df.loc[best_epoch]
                        st.success(
                            f"🏆 Meilleure epoch : **{best_epoch}** — "
                            f"Hit@1: {best.get('hit@1', '—')} | "
                            f"Hit@5: {best.get('hit@5', '—')} | "
                            f"MRR@10: {best.get('mrr@10', '—')}"
                        )
                else:
                    st.info("En attente des métriques… (entraînement en cours ou pas encore démarré)")

                started = run.get("started_at")
                completed = run.get("completed_at")
                if started:
                    st.caption(f"Démarré : {started}")
                if completed:
                    duration = completed - started if started else "—"
                    st.caption(f"Terminé : {completed} (durée : {duration})")
