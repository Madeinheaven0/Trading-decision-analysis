# Journal de trading Forex

App locale pour enregistrer tes analyses (indicateurs macro, lecture technique, prédictions) et suivre leur fiabilité dans le temps.

## Installation

```bash
pip install -r requirements.txt
```

## Lancement

```bash
streamlit run app.py
```

Ça ouvre automatiquement l'app dans ton navigateur (généralement http://localhost:8501).
La base de données (`forex_journal.db`) se crée automatiquement au premier lancement, dans le même dossier.

## Structure de l'app

- **➕ Nouvelle analyse** : saisis autant d'indicateurs que tu veux (un tableau extensible), ta synthèse macro (biais 2 semaines), ta lecture technique (RSI, support/résistance, biais 2 jours), les événements à risque, ton raisonnement, et tes deux prédictions.
- **📜 Historique** : retrouve toutes tes analyses passées, filtrables par paire, avec le détail complet de chacune.
- **✅ Vérifier les résultats** : reviens ici après 2 jours (ou 2 semaines) pour indiquer ce qui s'est réellement passé — l'app calcule automatiquement si ta prédiction était correcte.
- **📊 Statistiques** : ta précision globale par horizon, et surtout ta précision **selon ton niveau de confiance affiché** — c'est l'indicateur le plus utile pour savoir si ton intuition est bien calibrée (idéalement, plus tu es confiant, plus tu as raison).

## Fichiers

- `app.py` — l'interface Streamlit
- `db.py` — toute la logique de base de données (SQLite)
- `forex_journal.db` — ta base de données (créée automatiquement, à sauvegarder/versionner si tu veux garder ton historique)

## Idées d'évolution futures

- Export CSV de l'historique pour analyse dans Excel/Google Sheets
- Graphique d'évolution de la précision dans le temps
- Champ pour lier une capture d'écran à chaque analyse
- Ajout automatique de la date de vérification prévue (date + 2 jours / date + 2 semaines) avec rappel
