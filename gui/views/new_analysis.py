# -*- coding: utf-8 -*-
"""Page 1 — Nouvelle analyse."""

import datetime as dt

import pandas as pd
import streamlit as st

import db
from compat import STRETCH
from config import BIAS_OPTIONS, LONG_TERM_DEFAULT_INDEX, LONG_TERM_OPTIONS, SIGNAL_OPTIONS

# Nom de colonne affiché dans le tableau -> nom de colonne en base
COLUMN_TO_DB = {
    "Devise": "currency",
    "Indicateur": "indicator_name",
    "Actual": "actual",
    "Consensus": "consensus",
    "Previous": "previous",
    "Avant-Previous": "before_previous",
    "Signal": "signal",
    "Contexte": "context",
}


def _empty_indicators_df() -> pd.DataFrame:
    return pd.DataFrame([{
        "Devise": "", "Indicateur": "", "Actual": "", "Consensus": "",
        "Previous": "", "Avant-Previous": "", "Signal": "=", "Contexte": "",
    }])


def _indicators_to_records(df: pd.DataFrame) -> list[dict]:
    """Convertit le tableau saisi en liste de dicts prêts pour la base (None -> chaîne vide)."""
    cleaned = df.fillna("").astype(str)
    return cleaned.rename(columns=COLUMN_TO_DB).to_dict("records")


def _section_indicators():
    st.subheader("1. Indicateurs macro (une ligne par indicateur, autant que tu veux)")
    st.caption(
        "Ajoute une ligne par indicateur regardé (GDP, CPI, NFP, PMI, taux directeur...). "
        "**Avant-Previous** est optionnel : remplis-le seulement si la valeur d'avant le Previous existe. "
        "**Contexte** : une phrase pour expliquer pourquoi ce chiffre compte (ou pas)."
    )

    if "indicators_df" not in st.session_state:
        st.session_state.indicators_df = _empty_indicators_df()
    if "form_version" not in st.session_state:
        st.session_state.form_version = 0

    return st.data_editor(
        st.session_state.indicators_df,
        num_rows="dynamic",
        **STRETCH,
        column_config={
            "Devise": st.column_config.TextColumn("Devise", width="small"),
            "Indicateur": st.column_config.TextColumn("Indicateur", width="medium"),
            "Actual": st.column_config.TextColumn("Actual", width="small"),
            "Consensus": st.column_config.TextColumn("Consensus", width="small"),
            "Previous": st.column_config.TextColumn("Previous", width="small"),
            "Avant-Previous": st.column_config.TextColumn(
                "Avant-Previous", width="small",
                help="Optionnel : valeur de la publication précédant le Previous",
            ),
            "Signal": st.column_config.SelectboxColumn(
                "Signal", options=SIGNAL_OPTIONS, width="small",
                help="+ positif / - négatif / = neutre",
            ),
            "Contexte": st.column_config.TextColumn(
                "Contexte", width="large",
                help="Petit texte explicatif : pourquoi ce chiffre est important, dans quel contexte il sort...",
            ),
        },
        key=f"indicators_editor_{st.session_state.form_version}",
    )


def _section_macro_summary():
    st.subheader("2. Synthèse macro (horizon 1 mois)")
    col1, col2 = st.columns(2)
    with col1:
        macro_bias = st.selectbox("Biais macro global", BIAS_OPTIONS, key="macro_bias")
    with col2:
        macro_confidence = st.slider("Confiance dans le biais macro", 1, 5, 3, key="macro_conf")
    return macro_bias, macro_confidence


def _section_technical():
    st.subheader("3. Lecture technique (horizon 2 jours)")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        technical_bias = st.selectbox("Biais technique", BIAS_OPTIONS, key="tech_bias")
    with col2:
        rsi_value = st.number_input("RSI", min_value=0.0, max_value=100.0, value=50.0, step=0.1)
    with col3:
        support_level = st.number_input("Support proche", min_value=0.0, value=0.0, step=0.0001, format="%.5f")
    with col4:
        resistance_level = st.number_input("Résistance proche", min_value=0.0, value=0.0, step=0.0001, format="%.5f")

    technical_context = st.text_area(
        "Contexte technique",
        height=100,
        placeholder="Ex. Cassure de la MM50 sur H4, divergence RSI, retest de la résistance, volumes faibles...",
    )
    return technical_bias, rsi_value, support_level, resistance_level, technical_context


def _section_predictions():
    st.subheader("6. Tes prédictions")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Horizon 2 jours**")
        prediction_2d = st.selectbox("Prédiction 2 jours", BIAS_OPTIONS, key="pred_2d")
        confidence_2d = st.slider("Confiance (2 jours)", 1, 5, 3, key="conf_2d")
    with col2:
        st.markdown("**Horizon 1 mois — verdict long terme**")
        prediction_1m = st.selectbox(
            "Verdict 1 mois", LONG_TERM_OPTIONS,
            index=LONG_TERM_DEFAULT_INDEX, key="pred_1m",
        )
        confidence_1m = st.slider("Confiance (1 mois)", 1, 5, 3, key="conf_1m")
        verdict_1m_nuance = st.text_area(
            "Nuance / conditions du verdict",
            height=100, key="nuance_1m",
            placeholder="Ex. Haussier tant que 1.0850 tient ; à revoir si le NFP déçoit...",
        )
    return prediction_2d, confidence_2d, prediction_1m, confidence_1m, verdict_1m_nuance


def render():
    st.header("Nouvelle analyse")

    col1, col2, col3 = st.columns(3)
    with col1:
        pair = st.text_input("Paire", value="EUR/USD")
    with col2:
        analysis_date = st.date_input("Date", value=dt.date.today())
    with col3:
        price = st.number_input("Prix au moment de l'analyse", min_value=0.0, value=0.0, step=0.0001, format="%.5f")

    indicators_df = _section_indicators()
    macro_bias, macro_confidence = _section_macro_summary()
    technical_bias, rsi_value, support_level, resistance_level, technical_context = _section_technical()

    st.subheader("4. Événements à risque (48h)")
    risk_events = st.text_area("Événements à surveiller", placeholder="Ex. FOMC Minutes, décision BCE, NFP...")

    st.subheader("5. Ton raisonnement")
    reasoning = st.text_area("Raisonnement en quelques lignes", height=100)

    prediction_2d, confidence_2d, prediction_1m, confidence_1m, verdict_1m_nuance = _section_predictions()

    st.divider()
    if st.button("💾 Enregistrer cette analyse", type="primary"):
        if not pair.strip():
            st.error("Renseigne au moins la paire tradée.")
            return

        data = {
            "date": analysis_date.isoformat(),
            "pair": pair.strip().upper(),
            "price_at_analysis": price,
            "macro_bias": macro_bias,
            "macro_confidence": macro_confidence,
            "technical_bias": technical_bias,
            "rsi_value": rsi_value,
            "support_level": support_level,
            "resistance_level": resistance_level,
            "technical_context": technical_context,
            "risk_events": risk_events,
            "reasoning": reasoning,
            "prediction_2d": prediction_2d,
            "confidence_2d": confidence_2d,
            "prediction_1m": prediction_1m,
            "confidence_1m": confidence_1m,
            "verdict_1m_nuance": verdict_1m_nuance,
        }
        new_id = db.insert_prediction(data, _indicators_to_records(indicators_df))
        st.toast(f"Analyse enregistrée (id #{new_id})", icon="✅")  # survit au st.rerun() contrairement à st.success

        # Repart d'un tableau d'indicateurs vierge
        st.session_state.indicators_df = _empty_indicators_df()
        st.session_state.form_version += 1
        st.rerun()
