# -*- coding: utf-8 -*-
"""
Module de gestion de la base de données SQLite pour le journal de trading.
Deux tables :
  - predictions : une ligne par analyse (une paire, une date, la synthèse macro/technique, les prédictions)
  - indicators  : plusieurs lignes par analyse (les indicateurs macro saisis librement)
"""

import sqlite3
from contextlib import contextmanager

DB_PATH = "forex_journal.db"


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

                risk_events TEXT,
                reasoning TEXT,

                prediction_2d TEXT,
                confidence_2d INTEGER,
                prediction_2w TEXT,
                confidence_2w INTEGER,

                result_2d TEXT,
                correct_2d INTEGER,
                result_2w TEXT,
                correct_2w INTEGER,

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
                signal TEXT,
                FOREIGN KEY (prediction_id) REFERENCES predictions(id) ON DELETE CASCADE
            )
        """)


def insert_prediction(data: dict, indicators: list[dict]) -> int:
    with get_connection() as conn:
        cur = conn.execute("""
            INSERT INTO predictions (
                date, pair, price_at_analysis,
                macro_bias, macro_confidence,
                technical_bias, rsi_value, support_level, resistance_level,
                risk_events, reasoning,
                prediction_2d, confidence_2d,
                prediction_2w, confidence_2w
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data["date"], data["pair"], data["price_at_analysis"],
            data["macro_bias"], data["macro_confidence"],
            data["technical_bias"], data["rsi_value"], data["support_level"], data["resistance_level"],
            data["risk_events"], data["reasoning"],
            data["prediction_2d"], data["confidence_2d"],
            data["prediction_2w"], data["confidence_2w"],
        ))
        prediction_id = cur.lastrowid

        for ind in indicators:
            if not ind.get("indicator_name"):
                continue
            conn.execute("""
                INSERT INTO indicators (prediction_id, currency, indicator_name, actual, consensus, previous, signal)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                prediction_id, ind.get("currency", ""), ind.get("indicator_name", ""),
                ind.get("actual", ""), ind.get("consensus", ""), ind.get("previous", ""),
                ind.get("signal", ""),
            ))
        return prediction_id


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
    """horizon = '2d' ou '2w' -> renvoie les analyses dont le résultat n'est pas encore rempli."""
    col_result = "result_2d" if horizon == "2d" else "result_2w"
    with get_connection() as conn:
        rows = conn.execute(
            f"SELECT * FROM predictions WHERE {col_result} IS NULL ORDER BY date ASC"
        ).fetchall()
        return [dict(r) for r in rows]


def update_result(prediction_id: int, horizon: str, actual_result: str):
    """Enregistre le résultat réel et calcule automatiquement si la prédiction était correcte."""
    pred_col = "prediction_2d" if horizon == "2d" else "prediction_2w"
    result_col = "result_2d" if horizon == "2d" else "result_2w"
    correct_col = "correct_2d" if horizon == "2d" else "correct_2w"

    with get_connection() as conn:
        row = conn.execute(f"SELECT {pred_col} FROM predictions WHERE id = ?", (prediction_id,)).fetchone()
        predicted = row[0]
        is_correct = 1 if predicted == actual_result else 0
        conn.execute(f"""
            UPDATE predictions
            SET {result_col} = ?, {correct_col} = ?, result_updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (actual_result, is_correct, prediction_id))


def get_stats():
    with get_connection() as conn:
        stats = {}
        for horizon, correct_col, result_col in [("2 jours", "correct_2d", "result_2d"), ("2 semaines", "correct_2w", "result_2w")]:
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

        # Précision par paire
        pair_rows = conn.execute("""
            SELECT pair, COUNT(*) as total,
                   SUM(CASE WHEN result_2d IS NOT NULL THEN correct_2d ELSE 0 END) as correct_2d,
                   SUM(CASE WHEN result_2d IS NOT NULL THEN 1 ELSE 0 END) as evaluated_2d
            FROM predictions GROUP BY pair
        """).fetchall()
        stats["by_pair"] = [dict(r) for r in pair_rows]

        return stats
