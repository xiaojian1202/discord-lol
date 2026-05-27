import pytest
import sqlite3
import pandas as pd
from src.database.query import get_counters

@pytest.fixture
def mock_db(tmp_path):
    db_path = tmp_path / "matchups.db"
    conn = sqlite3.connect(str(db_path))
    
    # Create tables
    conn.execute("CREATE TABLE champions (ChampionID INTEGER, ChampionName TEXT)")
    conn.execute("CREATE TABLE matchups (champion_id INTEGER, opponent_id INTEGER, wins INTEGER, total_games INTEGER, win_rate REAL)")
    
    # Insert mock champions
    champs = [
        (1, 'Annie'),
        (2, 'Olaf'),
        (3, 'Aatrox'),
        (4, 'Ahri'),
        (5, 'Zed')
    ]
    conn.executemany("INSERT INTO champions VALUES (?, ?)", champs)
    
    # Insert mock matchups
    # Annie (1) vs others
    # Olaf (2) wins against Annie (1) with 80%
    # Aatrox (3) wins against Annie (1) with 70%
    matchups = [
        (2, 1, 80, 100, 0.8), # Olaf vs Annie
        (3, 1, 70, 100, 0.7), # Aatrox vs Annie
        (4, 1, 40, 100, 0.4), # Ahri vs Annie
        (5, 1, 90, 100, 0.9)  # Zed vs Annie
    ]
    conn.executemany("INSERT INTO matchups VALUES (?, ?, ?, ?, ?)", matchups)
    conn.commit()
    conn.close()
    return str(db_path)

def test_get_counters(mock_db):
    # Zed (0.9), Olaf (0.8), Aatrox (0.7) should be top counters for Annie
    counters = get_counters("Annie", db_path=mock_db, limit=3)
    
    assert len(counters) == 3
    assert counters[0]['name'] == 'Zed'
    assert counters[0]['win_rate'] == 0.9
    assert counters[1]['name'] == 'Olaf'
    assert counters[2]['name'] == 'Aatrox'

def test_get_counters_no_data(mock_db):
    counters = get_counters("NonExistent", db_path=mock_db)
    assert len(counters) == 0
