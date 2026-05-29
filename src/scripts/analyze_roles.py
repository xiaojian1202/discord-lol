import pandas as pd
import json

def analyze_roles(min_threshold=0.15):
    # Load data
    match_stats = pd.read_csv('data/raw/MatchStatsTbl.csv')
    summoner_matches = pd.read_csv('data/raw/SummonerMatchTbl.csv')
    champions = pd.read_csv('data/raw/ChampionTbl.csv')

    # Merge to get ChampionName and Lane
    df = match_stats.merge(summoner_matches, left_on='SummonerMatchFk', right_on='SummonerMatchId')
    df = df.merge(champions, left_on='ChampionFk', right_on='ChampionId')

    # Filter out 'NONE' lanes if any
    df = df[df['Lane'] != 'NONE']
    
    # Map raw CSV lanes to standard ROLES
    lane_map = {
        'TOP': 'Top',
        'JUNGLE': 'Jng',
        'MIDDLE': 'Mid',
        'BOTTOM': 'ADC', # This is usually ADC or Sup in stats, let's see
        'UTILITY': 'Sup'
    }
    # Some datasets use BOTTOM for both ADC and Sup, let's check roles
    # In this dataset, BOTTOM might be ambiguous. Let's see if we can distinguish.
    # Usually 'UTILITY' is Sup.
    
    df['StandardLane'] = df['Lane'].map(lane_map)
    
    # Group by Champion and Lane
    role_counts = df.groupby(['ChampionName', 'StandardLane']).size().unstack(fill_value=0)
    
    final_roles = {}
    flex_champions = {}
    
    for champion, counts in role_counts.iterrows():
        total = counts.sum()
        if total == 0: continue
        
        # Sort roles by frequency
        sorted_roles = counts.sort_values(ascending=False)
        percentages = sorted_roles / total
        
        top_role = sorted_roles.index[0]
        final_roles.setdefault(top_role, []).append(champion)
        
        # Check for flex (secondary role > threshold)
        if len(percentages) > 1 and percentages.iloc[1] >= min_threshold:
            secondary_role = percentages.index[1]
            flex_champions[champion] = [top_role, secondary_role]

    # Save to JSON for simulator to use
    data = {
        "ROLE_CHAMPIONS": final_roles,
        "FLEX_CHAMPIONS": flex_champions
    }
    
    with open('src/scripts/role_data.json', 'w') as f:
        json.dump(data, f, indent=4)
    
    print(f"Analysis complete. Found {len(flex_champions)} flex champions.")

if __name__ == "__main__":
    analyze_roles()
