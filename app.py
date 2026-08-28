# -*- coding: utf-8 -*-
"""
Journal de trading Forex — saisie des indicateurs macro, synthèse et suivi des prédictions.
Lancer avec : streamlit run app.py
"""

import datetime as dt

import pandas as pd
import streamlit as st

import db

st.set_page_config(page_title="Journal de trading Forex", page_icon="📈", layout="wide")
db.init_db()

BIAS_OPTIONS = ["Haussier", "Baissier", "Neutre"]
SIGNAL_OPTIONS = ["+", "-", "="]

st.title("📈 Journal de trading Forex")
st.caption("Saisis tes indicateurs, ta synthèse et tes prédictions — puis reviens vérifier les résultats.")

page = st.sidebar.radio(
    "Navigation",
    ["➕ Nouvelle analyse", "📜 Historique", "✅ Vérifier les résultats", "📊 Statistiques"],
)

# ----------------------------------------------------------------------------------
# PAGE 1 — NOUVELLE ANALYSE
# ----------------------------------------------------------------------------------
if page == "➕ Nouvelle analyse":
    st.header("Nouvelle analyse")

    col1, col2, col3 = st.columns(3)
    with col1:
        pair = st.text_input("Paire", value="EUR/USD")
    with col2:
        analysis_date = st.date_input("Date", value=dt.date.today())
    with col3:
        price = st.number_input("Prix au moment de l'analyse", min_value=0.0, value=0.0, step=0.0001, format="%.5f")

    st.subheader("1. Indicateurs macro (une ligne par indicateur, autant que tu veux)")
    st.caption("Ajoute une ligne par indicateur regardé (ex. GDP, CPI, NFP, PMI, taux directeur...).")

    if "indicators_df" not in st.session_state:
        st.session_state.indicators_df = pd.DataFrame(
            [{"Devise": "", "Indicateur": "", "Actual": "", "Consensus": "", "Previous": "", "Signal": "="}]
        )

    indicators_df = st.data_editor(
        st.session_state.indicators_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Signal": st.column_config.SelectboxColumn("Signal", options=SIGNAL_OPTIONS, help="+ positif / - négatif / = neutre"),
        },
        key="indicators_editor",
    )

    st.subheader("2. Synthèse macro (horizon 2 semaines)")
    col1, col2 = st.columns(2)
    with col1:
        macro_bias = st.selectbox("Biais macro global", BIAS_OPTIONS, key="macro_bias")
    with col2:
        macro_confidence = st.slider("Confiance dans le biais macro", 1, 5, 3, key="macro_conf")

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

    st.subheader("4. Événements à risque (48h)")
    risk_events = st.text_area("Événements à surveiller", placeholder="Ex. FOMC Minutes, décision BCE, NFP...")

    st.subheader("5. Ton raisonnement")
    reasoning = st.text_area("Raisonnement en quelques lignes", height=100)

    st.subheader("6. Tes prédictions")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Horizon 2 jours**")
        prediction_2d = st.selectbox("Prédiction 2 jours", BIAS_OPTIONS, key="pred_2d")
        confidence_2d = st.slider("Confiance (2 jours)", 1, 5, 3, key="conf_2d")
    with col2:
        st.markdown("**Horizon 2 semaines**")
        prediction_2w = st.selectbox("Prédiction 2 semaines", BIAS_OPTIONS, key="pred_2w")
        confidence_2w = st.slider("Confiance (2 semaines)", 1, 5, 3, key="conf_2w")

    st.divider()
    if st.button("💾 Enregistrer cette analyse", type="primary"):
        if not pair.strip():
            st.error("Renseigne au moins la paire tradée.")
        else:
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
                "risk_events": risk_events,
                "reasoning": reasoning,
                "prediction_2d": prediction_2d,
                "confidence_2d": confidence_2d,
                "prediction_2w": prediction_2w,
                "confidence_2w": confidence_2w,
            }
            indicators = indicators_df.rename(columns={
                "Devise": "currency", "Indicateur": "indicator_name",
                "Actual": "actual", "Consensus": "consensus", "Previous": "previous", "Signal": "signal",
            }).to_dict("records")

            new_id = db.insert_prediction(data, indicators)
            st.success(f"Analyse enregistrée (id #{new_id}) ✅")
            st.session_state.indicators_df = pd.DataFrame(
                [{"Devise": "", "Indicateur": "", "Actual": "", "Consensus": "", "Previous": "", "Signal": "="}]
            )
            st.rerun()

# ----------------------------------------------------------------------------------
# PAGE 2 — HISTORIQUE
# ----------------------------------------------------------------------------------
elif page == "📜 Historique":
    st.header("Historique des analyses")

    predictions = db.get_all_predictions()
    if not predictions:
        st.info("Aucune analyse enregistrée pour l'instant.")
    else:
        df = pd.DataFrame(predictions)
        pairs = ["Toutes"] + sorted(df["pair"].unique().tolist())
        selected_pair = st.selectbox("Filtrer par paire", pairs)
        if selected_pair != "Toutes":
            df = df[df["pair"] == selected_pair]

        display_cols = [
            "id", "date", "pair", "price_at_analysis",
            "macro_bias", "prediction_2d", "prediction_2w",
            "result_2d", "correct_2d", "result_2w", "correct_2w",
        ]
        st.dataframe(df[display_cols], use_container_width=True, hide_index=True)

        st.subheader("Détail d'une analyse")
        selected_id = st.selectbox("Choisir une analyse (par id)", df["id"].tolist())
        if selected_id:
            pred = db.get_prediction(selected_id)
            indicators = db.get_indicators_for(selected_id)

            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Paire :** {pred['pair']}  \n**Date :** {pred['date']}  \n**Prix :** {pred['price_at_analysis']}")
                st.markdown(f"**Biais macro :** {pred['macro_bias']} (confiance {pred['macro_confidence']}/5)")
                st.markdown(f"**Biais technique :** {pred['technical_bias']}  \n**RSI :** {pred['rsi_value']}")
                st.markdown(f"**Support :** {pred['support_level']}  \n**Résistance :** {pred['resistance_level']}")
            with col2:
                st.markdown(f"**Prédiction 2j :** {pred['prediction_2d']} (confiance {pred['confidence_2d']}/5)")
                st.markdown(f"**Résultat 2j :** {pred['result_2d'] or '— pas encore vérifié'}")
                st.markdown(f"**Prédiction 2sem :** {pred['prediction_2w']} (confiance {pred['confidence_2w']}/5)")
                st.markdown(f"**Résultat 2sem :** {pred['result_2w'] or '— pas encore vérifié'}")

            if pred["risk_events"]:
                st.markdown(f"**Événements à risque :** {pred['risk_events']}")
            if pred["reasoning"]:
                st.markdown(f"**Raisonnement :** {pred['reasoning']}")

            if indicators:
                st.markdown("**Indicateurs saisis :**")
                ind_df = pd.DataFrame(indicators)[["currency", "indicator_name", "actual", "consensus", "previous", "signal"]]
                st.dataframe(ind_df, use_container_width=True, hide_index=True)

# ----------------------------------------------------------------------------------
# PAGE 3 — VÉRIFIER LES RÉSULTATS
# ----------------------------------------------------------------------------------
elif page == "✅ Vérifier les résultats":
    st.header("Vérifier les résultats")
    st.caption("Reviens ici quelques jours après une analyse pour comparer ta prédiction à ce qui s'est réellement passé.")

    tab_2d, tab_2w = st.tabs(["Résultats à 2 jours", "Résultats à 2 semaines"])

    for tab, horizon, label in [(tab_2d, "2d", "2 jours"), (tab_2w, "2w", "2 semaines")]:
        with tab:
            pending = db.get_pending_results(horizon)
            if not pending:
                st.info(f"Aucune analyse en attente de vérification ({label}).")
                continue

            for pred in pending:
                pred_field = "prediction_2d" if horizon == "2d" else "prediction_2w"
                with st.expander(f"#{pred['id']} — {pred['pair']} du {pred['date']} — prédiction : {pred[pred_field]}"):
                    st.markdown(f"**Raisonnement d'origine :** {pred['reasoning'] or '—'}")
                    actual = st.selectbox(
                        "Qu'est-ce qui s'est réellement passé ?",
                        BIAS_OPTIONS,
                        key=f"actual_{horizon}_{pred['id']}",
                    )
                    if st.button("Enregistrer le résultat", key=f"btn_{horizon}_{pred['id']}"):
                        db.update_result(pred["id"], horizon, actual)
                        st.success("Résultat enregistré ✅")
                        st.rerun()

# ----------------------------------------------------------------------------------
# PAGE 4 — STATISTIQUES
# ----------------------------------------------------------------------------------
elif page == "📊 Statistiques":
    st.header("Statistiques de fiabilité")

    stats = db.get_stats()

    col1, col2 = st.columns(2)
    for col, horizon in zip([col1, col2], ["2 jours", "2 semaines"]):
        s = stats[horizon]
        with col:
            st.metric(
                f"Précision — {horizon}",
                f"{s['accuracy']}%" if s["accuracy"] is not None else "—",
                help=f"{s['correct']} correctes sur {s['total']} évaluées",
            )

    st.divider()
    st.subheader("Précision selon ton niveau de confiance (horizon 2 jours)")
    conf_data = stats["by_confidence_2d"]
    if conf_data:
        conf_df = pd.DataFrame(conf_data)
        conf_df["accuracy"] = (100 * conf_df["correct"] / conf_df["total"]).round(1)
        st.bar_chart(conf_df.set_index("confidence")["accuracy"])
        st.caption("Si ta précision augmente avec ta confiance affichée, c'est bon signe : ton intuition est calibrée.")
    else:
        st.info("Pas encore assez de résultats vérifiés pour afficher ce graphique.")

    st.divider()
    st.subheader("Répartition par paire")
    pair_data = stats["by_pair"]
    if pair_data:
        pair_df = pd.DataFrame(pair_data)
        st.dataframe(pair_df, use_container_width=True, hide_index=True)
    else:
        st.info("Aucune donnée pour l'instant.")
