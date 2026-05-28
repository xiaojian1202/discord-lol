import pandas as pd
import sqlite3
import os
import argparse
from typing import Optional

def process_matchups(match_stats: pd.DataFrame, champions: pd.DataFrame, summoner_matches: pd.DataFrame, db_path: str):
    """
    Processes match statistics, champion data, and summoner-match links.
    """
    # 1. Prepare champions table
    # Standardize column name to ChampionID if it is ChampionId
    if 'ChampionId' in champions.columns:
        champions = champions.rename(columns={'ChampionId': 'ChampionID'})
        
    conn = sqlite3.connect(db_path)
    champions.to_sql('champions', conn, if_exists='replace', index=False)
    
    # 2. Merge match_stats with summoner_matches to get MatchID and ChampionID together
    # match_stats: SummonerMatchFk, Win
    # summoner_matches: SummonerMatchId, MatchFk, ChampionFk
    merged = pd.merge(
        match_stats[['SummonerMatchFk', 'Win']], 
        summoner_matches[['SummonerMatchId', 'MatchFk', 'ChampionFk']], 
        left_on='SummonerMatchFk', 
        right_on='SummonerMatchId'
    )
    merged = merged.rename(columns={'MatchFk': 'MatchID', 'ChampionFk': 'ChampionID'})
    
    # 3. Identify winners and losers per match
    winners = merged[merged['Win'] == 1][['MatchID', 'ChampionID']].rename(columns={'ChampionID': 'winner_id'})
    losers = merged[merged['Win'] == 0][['MatchID', 'ChampionID']].rename(columns={'ChampionID': 'loser_id'})
    
    # 4. Create pairs: (Winner, Loser) -> Winner won
    winning_pairs = pd.merge(winners, losers, on='MatchID')[['winner_id', 'loser_id']]
    
    # Aggregate winning pairs
    win_counts = winning_pairs.groupby(['winner_id', 'loser_id']).size().reset_index(name='wins')
    win_counts.columns = ['champion_id', 'opponent_id', 'wins']
    
    # 5. Create pairs: (Loser, Winner) -> Loser lost
    loss_counts = winning_pairs.copy().rename(columns={'winner_id': 'opponent_id', 'loser_id': 'champion_id'})
    loss_counts = loss_counts.groupby(['champion_id', 'opponent_id']).size().reset_index(name='losses')
    
    # 6. Merge win and loss counts
    matchups = pd.merge(win_counts, loss_counts, on=['champion_id', 'opponent_id'], how='outer').fillna(0)
    matchups['total_games'] = matchups['wins'] + matchups['losses']
    matchups['win_rate'] = matchups['wins'] / matchups['total_games']
    
    # Save to SQL
    matchups.to_sql('matchups', conn, if_exists='replace', index=False)
    
    # Add indexes
    cursor = conn.cursor()
    cursor.execute("CREATE INDEX idx_champion_id ON matchups(champion_id)")
    cursor.execute("CREATE INDEX idx_opponent_id ON matchups(opponent_id)")
    cursor.execute("CREATE INDEX idx_champion_name ON champions(ChampionName)")
    conn.commit()
    conn.close()

def main():
    parser = argparse.ArgumentParser(description="Initialize the LoL Matchup Database")
    parser.add_argument("--match-stats", type=str, required=True, help="Path to MatchStatsTbl.csv")
    parser.add_argument("--champions", type=str, required=True, help="Path to ChampionTbl.csv")
    parser.add_argument("--summoner-matches", type=str, required=True, help="Path to SummonerMatchTbl.csv")
    parser.add_argument("--db", type=str, default="data/matchups.db", help="Path to output SQLite DB")
    
    args = parser.parse_args()
    
    paths = [args.match_stats, args.champions, args.summoner_matches]
    for p in paths:
        if not os.path.exists(p):
            print(f"Error: {p} not found.")
            return
            
    print("Loading data...")
    match_stats = pd.read_csv(args.match_stats)
    champions = pd.read_csv(args.champions)
    summoner_matches = pd.read_csv(args.summoner_matches)
    
    print("Processing matchups (this may take a minute)...")
    process_matchups(match_stats, champions, summoner_matches, args.db)
    print(f"Database initialized at {args.db}")

if __name__ == "__main__":
    main()
