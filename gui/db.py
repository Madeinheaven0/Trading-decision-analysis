# -*- coding: utf-8 -*-
"""
Module de gestion de la base de données SQLite pour le journal de trading.
Deux tables :
  - predictions : une ligne par analyse (une paire, une date, la synthèse macro/technique, les prédictions)
  - indicators  : plusieurs lignes par analyse (les indicateurs macro saisis librement)

Les nouvelles colonnes sont ajoutées (et les anciennes *_2w renommées en *_1m) automatiquement
sur les bases existantes (voir _migrate) : tu ne perds aucune donnée déjà saisie.
Attention : les anciennes prédictions "2 semaines" sont conservées mais apparaissent désormais
dans la colonne "1 mois" (même donnée, nouvel horizon).
"""

import sqlite3
from contextlib import contextmanager

from config import DB_PATH, direction_of

# Champs insérés dans la table predictions (l'ordre n'a pas d'importance, mais reste cohérent ici)
PREDICTION_FIELDS = [
    "date", "pair", "price_at_analysis",
    "macro_bias", "macro_confidence",
    "technical_bias", "rsi_value", "support_level", "resistance_level", "technical_context",
    "risk_events", "reasoning",
    "prediction_2d", "confidence_2d",
    "prediction_1m", "confidence_1m", "verdict_1m_nuance",
]

# Champs insérés dans la table indicators
INDICATOR_FIELDS = [
    "currency", "indicator_name", "actual", "consensus",
    "previous", "before_previous", "signal", "context",
]


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                pair TEXT NOT NULL,
                price_at_analysis REAL,

                macro_bias TEXT,
                macro_confidence INTEGER,

                technical_bias TEXT,
                rsi_value REAL,
                support_level REAL,
                resistance_level REAL,
                technical_context TEXT,

                risk_events TEXT,
                reasoning TEXT,

                prediction_2d TEXT,
                confidence_2d INTEGER,
                prediction_1m TEXT,
                confidence_1m INTEGER,
                verdict_1m_nuance TEXT,

                result_2d TEXT,
                correct_2d INTEGER,
                result_1m TEXT,
                correct_1m INTEGER,

                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                result_updated_at TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS indicators (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prediction_id INTEGER NOT NULL,
                currency TEXT,
                indicator_name TEXT,
                actual TEXT,
                consensus TEXT,
                previous TEXT,
                before_previous TEXT,
                signal TEXT,
                context TEXT,
                FOREIGN KEY (prediction_id) REFERENCES predictions(id) ON DELETE CASCADE
            )
        """)
        _migrate(conn)


def _ensure_column(conn, table: str, column: str, col_type: str):
    """Ajoute la colonne si elle n'existe pas encore (utile pour les bases créées avant cette version)."""
    existing = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}
    if column not in existing:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")


# Anciennes colonnes (horizon 2 semaines) -> nouvelles colonnes (horizon 1 mois)
_RENAMED_COLUMNS = {
    "prediction_2w": "prediction_1m",
    "confidence_2w": "confidence_1m",
    "result_2w": "result_1m",
    "correct_2w": "correct_1m",
    "verdict_2w_nuance": "verdict_1m_nuance",
}


def _rename_legacy_columns(conn):
    """Renomme les colonnes *_2w en *_1m sur une base créée avant le passage à l'horizon 1 mois."""
    existing = {row["name"] for row in conn.execute("PRAGMA table_info(predictions)")}
    for old, new in _RENAMED_COLUMNS.items():
        if old in existing and new not in existing:
            conn.execute(f"ALTER TABLE predictions RENAME COLUMN {old} TO {new}")


def _migrate(conn):
    _rename_legacy_columns(conn)
    _ensure_column(conn, "indicators", "before_previous", "TEXT")
    _ensure_column(conn, "indicators", "context", "TEXT")
    _ensure_column(conn, "predictions", "technical_context", "TEXT")
    _ensure_column(conn, "predictions", "verdict_1m_nuance", "TEXT")


# ----------------------------------------------------------------------------------
# ÉCRITURE
# ----------------------------------------------------------------------------------
def insert_prediction(data: dict, indicators: list[dict]) -> int:
    placeholders = ", ".join("?" for _ in PREDICTION_FIELDS)
    columns = ", ".join(PREDICTION_FIELDS)
    values = [data.get(field) for field in PREDICTION_FIELDS]

    with get_connection() as conn:
        cur = conn.execute(
            f"INSERT INTO predictions ({columns}) VALUES ({placeholders})", values
        )
        prediction_id = cur.lastrowid

        ind_columns = ", ".join(["prediction_id"] + INDICATOR_FIELDS)
        ind_placeholders = ", ".join("?" for _ in range(len(INDICATOR_FIELDS) + 1))
        for ind in indicators:
            if not (ind.get("indicator_name") or "").strip():
                continue  # ligne vide -> ignorée
            conn.execute(
                f"INSERT INTO indicators ({ind_columns}) VALUES ({ind_placeholders})",
                [prediction_id] + [ind.get(field, "") for field in INDICATOR_FIELDS],
            )
        return prediction_id


def update_result(prediction_id: int, horizon: str, actual_result: str):
    """Enregistre le résultat réel et calcule si la DIRECTION prédite était correcte."""
    pred_col = "prediction_2d" if horizon == "2d" else "prediction_1m"
    result_col = "result_2d" if horizon == "2d" else "result_1m"
    correct_col = "correct_2d" if horizon == "2d" else "correct_1m"

    with get_connection() as conn:
        row = conn.execute(f"SELECT {pred_col} FROM predictions WHERE id = ?", (prediction_id,)).fetchone()
        predicted_dir = direction_of(row[0])
        actual_dir = direction_of(actual_result)
        is_correct = 1 if (predicted_dir is not None and predicted_dir == actual_dir) else 0
        conn.execute(f"""
            UPDATE predictions
            SET {result_col} = ?, {correct_col} = ?, result_updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (actual_result, is_correct, prediction_id))


# ----------------------------------------------------------------------------------
# LECTURE
# ----------------------------------------------------------------------------------
def get_all_predictions():
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM predictions ORDER BY date DESC, id DESC").fetchall()
        return [dict(r) for r in rows]


def get_prediction(prediction_id: int):
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM predictions WHERE id = ?", (prediction_id,)).fetchone()
        return dict(row) if row else None


def get_indicators_for(prediction_id: int):
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM indicators WHERE prediction_id = ? ORDER BY currency, id", (prediction_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def get_pending_results(horizon: str):
    """horizon = '2d' ou '1m' -> renvoie les analyses dont le résultat n'est pas encore rempli."""
    col_result = "result_2d" if horizon == "2d" else "result_1m"
    with get_connection() as conn:
        rows = conn.execute(
            f"SELECT * FROM predictions WHERE {col_result} IS NULL ORDER BY date ASC"
        ).fetchall()
        return [dict(r) for r in rows]


def get_stats():
    with get_connection() as conn:
        stats = {}
        for horizon, correct_col, result_col in [("2 jours", "correct_2d", "result_2d"), ("1 mois", "correct_1m", "result_1m")]:
            row = conn.execute(f"""
                SELECT COUNT(*) as total, SUM({correct_col}) as correct
                FROM predictions WHERE {result_col} IS NOT NULL
            """).fetchone()
            total = row["total"] or 0
            correct = row["correct"] or 0
            stats[horizon] = {
                "total": total,
                "correct": correct,
                "accuracy": round(100 * correct / total, 1) if total > 0 else None,
            }

        # Précision par niveau de confiance (2 jours)
        conf_rows = conn.execute("""
            SELECT confidence_2d as confidence, COUNT(*) as total, SUM(correct_2d) as correct
            FROM predictions WHERE result_2d IS NOT NULL
            GROUP BY confidence_2d ORDER BY confidence_2d
        """).fetchall()
        stats["by_confidence_2d"] = [dict(r) for r in conf_rows]

        # Précision par intensité du verdict long terme (1 mois)
        verdict_rows = conn.execute("""
            SELECT prediction_1m as verdict, COUNT(*) as total, SUM(correct_1m) as correct
            FROM predictions WHERE result_1m IS NOT NULL
            GROUP BY prediction_1m
        """).fetchall()
        stats["by_verdict_1m"] = [dict(r) for r in verdict_rows]

        # Précision par paire
        pair_rows = conn.execute("""
            SELECT pair, COUNT(*) as total,
                   SUM(CASE WHEN result_2d IS NOT NULL THEN correct_2d ELSE 0 END) as correct_2d,
                   SUM(CASE WHEN result_2d IS NOT NULL THEN 1 ELSE 0 END) as evaluated_2d
            FROM predictions GROUP BY pair
        """).fetchall()
        stats["by_pair"] = [dict(r) for r in pair_rows]

        return stats
