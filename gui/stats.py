# -*- coding: utf-8 -*-
"""Page 4 — Statistiques de fiabilité."""

import pandas as pd
import streamlit as st

import db
from compat import STRETCH
from config import LONG_TERM_OPTIONS


def _accuracy(correct, total):
    return round(100 * (correct or 0) / total, 1) if total else None


def render():
    st.header("Statistiques de fiabilité")

    stats = db.get_stats()

    col1, col2 = st.columns(2)
    for col, horizon in zip([col1, col2], ["2 jours", "1 mois"]):
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
    st.subheader("Précision selon l'intensité du verdict long terme (1 mois)")
    verdict_data = stats["by_verdict_1m"]
    if verdict_data:
        # Trie de "Fortement haussier" à "Fortement baissier" ; les anciens libellés vont à la fin
        order = {label: i for i, label in enumerate(LONG_TERM_OPTIONS)}
        verdict_data = sorted(verdict_data, key=lambda r: order.get(r["verdict"], 99))
        verdict_df = pd.DataFrame(verdict_data)
        verdict_df["correct"] = verdict_df["correct"].fillna(0).astype(int)
        verdict_df["accuracy_%"] = [_accuracy(c, t) for c, t in zip(verdict_df["correct"], verdict_df["total"])]
        st.dataframe(verdict_df, hide_index=True, **STRETCH)
        st.caption("Tes verdicts « fortement » sont-ils plus fiables que tes verdicts « modérés » ? C'est ici que tu le vois.")
    else:
        st.info("Pas encore de verdict long terme vérifié.")

    st.divider()
    st.subheader("Répartition par paire")
    pair_data = stats["by_pair"]
    if pair_data:
        pair_df = pd.DataFrame(pair_data)
        pair_df["accuracy_2d_%"] = [_accuracy(c, e) for c, e in zip(pair_df["correct_2d"], pair_df["evaluated_2d"])]
        st.dataframe(pair_df, hide_index=True, **STRETCH)
    else:
        st.info("Aucune donnée pour l'instant.")
