# -*- coding: utf-8 -*-
"""Constantes partagées par toute l'application."""

DB_PATH = "forex_journal.db"

# Choix simples : biais macro, biais technique, prédiction à 2 jours
BIAS_OPTIONS = ["Haussier", "Baissier", "Neutre"]

# Verdict long terme (1 mois) : échelle nuancée, de la plus haussière à la plus baissière
LONG_TERM_OPTIONS = [
    "Fortement haussier",
    "Haussier modéré",
    "Neutre / Range",
    "Baissier modéré",
    "Fortement baissier",
]
LONG_TERM_DEFAULT_INDEX = 2  # "Neutre / Range"

SIGNAL_OPTIONS = ["+", "-", "="]

# Sert à comparer une prédiction nuancée à un résultat : seule la DIRECTION compte
# pour savoir si la prédiction était correcte. Les anciennes valeurs ("Haussier",
# "Baissier", "Neutre") restent donc compatibles.
_DIRECTIONS = {
    "Haussier": "Haussier",
    "Fortement haussier": "Haussier",
    "Haussier modéré": "Haussier",
    "Baissier": "Baissier",
    "Fortement baissier": "Baissier",
    "Baissier modéré": "Baissier",
    "Neutre": "Neutre",
    "Neutre / Range": "Neutre",
}


def direction_of(label):
    """Renvoie 'Haussier', 'Baissier' ou 'Neutre' (ou None si le libellé est inconnu)."""
    return _DIRECTIONS.get(label)
