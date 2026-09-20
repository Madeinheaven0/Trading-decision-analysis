# -*- coding: utf-8 -*-
"""Page 2 — Historique des analyses."""

import pandas as pd
import streamlit as st

import db
from compat import STRETCH

INDICATOR_LABELS = {
    "currency": "Devise",
    "indicator_name": "Indicateur",
    "actual": "Actual",
    "consensus": "Consensus",
    "previous": "Previous",
    "before_previous": "Avant-Previous",
    "signal": "Signal",
    "context": "Contexte",
}


def _render_detail(prediction_id: int):
    pred = db.get_prediction(prediction_id)
    indicators = db.get_indicators_for(prediction_id)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Paire :** {pred['pair']}  \n**Date :** {pred['date']}  \n**Prix :** {pred['price_at_analysis']}")
        st.markdown(f"**Biais macro :** {pred['macro_bias']} (confiance {pred['macro_confidence']}/5)")
        st.markdown(f"**Biais technique :** {pred['technical_bias']}  \n**RSI :** {pred['rsi_value']}")
        st.markdown(f"**Support :** {pred['support_level']}  \n**Résistance :** {pred['resistance_level']}")
    with col2:
        st.markdown(f"**Prédiction 2j :** {pred['prediction_2d']} (confiance {pred['confidence_2d']}/5)")
        st.markdown(f"**Résultat 2j :** {pred['result_2d'] or '— pas encore vérifié'}")
        st.markdown(f"**Verdict 1 mois :** {pred['prediction_1m']} (confiance {pred['confidence_1m']}/5)")
        st.markdown(f"**Résultat 1 mois :** {pred['result_1m'] or '— pas encore vérifié'}")

    if pred.get("verdict_1m_nuance"):
        st.markdown(f"**Nuance du verdict long terme :** {pred['verdict_1m_nuance']}")
    if pred.get("technical_context"):
        st.markdown(f"**Contexte technique :** {pred['technical_context']}")
    if pred["risk_events"]:
        st.markdown(f"**Événements à risque :** {pred['risk_events']}")
    if pred["reasoning"]:
        st.markdown(f"**Raisonnement :** {pred['reasoning']}")

    if indicators:
        st.markdown("**Indicateurs saisis :**")
        ind_df = pd.DataFrame(indicators)[list(INDICATOR_LABELS.keys())].rename(columns=INDICATOR_LABELS)
        st.dataframe(ind_df, hide_index=True, **STRETCH)


def render():
    st.header("Historique des analyses")

    predictions = db.get_all_predictions()
    if not predictions:
        st.info("Aucune analyse enregistrée pour l'instant.")
        return

    df = pd.DataFrame(predictions)
    pairs = ["Toutes"] + sorted(df["pair"].unique().tolist())
    selected_pair = st.selectbox("Filtrer par paire", pairs)
    if selected_pair != "Toutes":
        df = df[df["pair"] == selected_pair]

    display_cols = [
        "id", "date", "pair", "price_at_analysis",
        "macro_bias", "prediction_2d", "prediction_1m",
        "result_2d", "correct_2d", "result_1m", "correct_1m",
    ]
    st.dataframe(df[display_cols], hide_index=True, **STRETCH)

    st.subheader("Détail d'une analyse")
    selected_id = st.selectbox("Choisir une analyse (par id)", df["id"].tolist())
    if selected_id:
        _render_detail(selected_id)
