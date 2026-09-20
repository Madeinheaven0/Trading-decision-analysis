# -*- coding: utf-8 -*-
"""
Journal de trading Forex — point d'entrée.
Lancer avec : streamlit run app.py

Ce fichier ne contient que la configuration et la navigation.
Chaque page vit dans son propre module, dans le dossier views/.
"""

import streamlit as st

import db
from views import history, new_analysis, stats, verify

st.set_page_config(page_title="Journal de trading Forex", page_icon="📈", layout="wide")
db.init_db()

PAGES = {
    "➕ Nouvelle analyse": new_analysis.render,
    "📜 Historique": history.render,
    "✅ Vérifier les résultats": verify.render,
    "📊 Statistiques": stats.render,
}

st.title("📈 Journal de trading Forex")
st.caption("Saisis tes indicateurs, ta synthèse et tes prédictions — puis reviens vérifier les résultats.")

choice = st.sidebar.radio("Navigation", list(PAGES.keys()))
PAGES[choice]()
