# -*- coding: utf-8 -*-
"""Page 3 — Vérifier les résultats."""

import streamlit as st

import db
from config import BIAS_OPTIONS, LONG_TERM_DEFAULT_INDEX, LONG_TERM_OPTIONS


def _render_pending(horizon: str, label: str, options: list[str], default_index: int):
    pending = db.get_pending_results(horizon)
    if not pending:
        st.info(f"Aucune analyse en attente de vérification ({label}).")
        return

    pred_field = "prediction_2d" if horizon == "2d" else "prediction_1m"
    for pred in pending:
        with st.expander(f"#{pred['id']} — {pred['pair']} du {pred['date']} — prédiction : {pred[pred_field]}"):
            st.markdown(f"**Raisonnement d'origine :** {pred['reasoning'] or '—'}")
            if horizon == "1m" and pred.get("verdict_1m_nuance"):
                st.markdown(f"**Nuance du verdict :** {pred['verdict_1m_nuance']}")

            actual = st.selectbox(
                "Qu'est-ce qui s'est réellement passé ?",
                options,
                index=default_index,
                key=f"actual_{horizon}_{pred['id']}",
            )
            if st.button("Enregistrer le résultat", key=f"btn_{horizon}_{pred['id']}"):
                db.update_result(pred["id"], horizon, actual)
                st.toast("Résultat enregistré", icon="✅")
                st.rerun()


def render():
    st.header("Vérifier les résultats")
    st.caption(
        "Reviens ici une fois l'horizon écoulé (2 jours, 1 mois) pour comparer ta prédiction à ce qui s'est réellement passé. "
        "Pour le long terme, seule la **direction** (haussier / baissier / neutre) compte pour savoir si tu avais raison ; "
        "l'intensité sert à affiner tes statistiques."
    )

    tab_2d, tab_1m = st.tabs(["Résultats à 2 jours", "Résultats à 1 mois"])
    with tab_2d:
        _render_pending("2d", "2 jours", BIAS_OPTIONS, default_index=0)
    with tab_1m:
        _render_pending("1m", "1 mois", LONG_TERM_OPTIONS, default_index=LONG_TERM_DEFAULT_INDEX)
