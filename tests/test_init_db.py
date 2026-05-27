import pytest
import pandas as pd
import sqlite3
import os
from src.scripts.init_db import process_matchups

def test_process_matchups(tmp_path):
    # Setup mock data according to actual CSV schema
    match_stats = pd.DataFrame({
        'SummonerMatchFk': [1, 2],
        'Win': [1, 0]
    })
    
    summoner_matches = pd.DataFrame({
        'SummonerMatchId': [1, 2],
        'MatchFk': ['M1', 'M1'],
        'ChampionFk': [10, 20] # Champion 10 wins, 20 loses
    })
    
    champions = pd.DataFrame({
        'ChampionID': [10, 20],
        'ChampionName': ['Annie', 'Olaf']
    })
    
    db_path = tmp_path / "test_matchups.db"
    
    # Run processing
    process_matchups(match_stats, champions, summoner_matches, str(db_path))
    
    # Verify DB
    conn = sqlite3.connect(str(db_path))
    df = pd.read_sql("SELECT * FROM matchups", conn)
    
    # Champion 10 vs 20 should have 1 win, 1 total game
    c10_vs_20 = df[(df['champion_id'] == 10) & (df['opponent_id'] == 20)]
    assert len(c10_vs_20) == 1
    assert c10_vs_20.iloc[0]['wins'] == 1
    assert c10_vs_20.iloc[0]['total_games'] == 1
    
    # Champion 20 vs 10 should have 0 wins, 1 total game
    c20_vs_10 = df[(df['champion_id'] == 20) & (df['opponent_id'] == 10)]
    assert len(c20_vs_10) == 1
    assert c20_vs_10.iloc[0]['wins'] == 0
    assert c20_vs_10.iloc[0]['total_games'] == 1
    
    conn.close()
