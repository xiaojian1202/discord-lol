import sqlite3
import os
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

DEFAULT_DB_PATH = os.getenv("DATABASE_PATH", "data/matchups.db")

def get_counters(champion_name: str, db_path: str = DEFAULT_DB_PATH, limit: int = 5, min_games: int = 50) -> List[Dict[str, Any]]:
    """
    Retrieves top counter picks for a given champion name.
    A counter pick is a champion that has a high win rate against the target champion.
    """
    if not os.path.exists(db_path):
        return []

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # 1. Get the ID of the target champion
        cursor.execute("SELECT ChampionID FROM champions WHERE ChampionName = ?", (champion_name,))
        row = cursor.fetchone()
        if not row:
            return []
        
        target_id = row['ChampionID']

        # 2. Query matchups where opponent is target_id, sorted by win_rate
        query = """
            SELECT c.ChampionName, m.win_rate, m.total_games
            FROM matchups m
            JOIN champions c ON m.champion_id = c.ChampionID
            WHERE m.opponent_id = ? AND m.total_games >= ?
            ORDER BY m.win_rate DESC
            LIMIT ?
        """
        cursor.execute(query, (target_id, min_games, limit))
        rows = cursor.fetchall()

        results = [
            {
                "name": row['ChampionName'],
                "win_rate": row['win_rate'],
                "total_games": row['total_games']
            }
            for row in rows
        ]
        return results

    finally:
        conn.close()
