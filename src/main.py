import os
import sqlite3
import logging
import asyncio
import traceback
from typing import Dict, Optional
from dotenv import load_dotenv
from src.lcu.listener import LCUListener
from src.database.query import get_counters
from src.ai.client import get_ai_recommendation
from src.discord.webhook import send_discord_message

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()

class Orchestrator:
    def __init__(self):
        self.db_path = os.getenv("DATABASE_PATH", "data/matchups.db")
        self.listener = LCUListener(on_enemy_pick=self.handle_enemy_pick)
        self.name_cache: Dict[int, str] = {}

    async def handle_enemy_pick(self, state: dict, target_role: Optional[str] = None):
        # 1. Resolve names for teams
        our_team_ids = state.get("our_team", {})
        enemy_team_ids = state.get("enemy_team", {})
        
        our_team_names = {role: self.resolve_champion_name(cid) for role, cid in our_team_ids.items()}
        enemy_team_names = {role: self.resolve_champion_name(cid) for role, cid in enemy_team_ids.items()}
        
        # Filter out None names
        our_team_names = {r: n for r, n in our_team_names.items() if n}
        enemy_team_names = {r: n for r, n in enemy_team_names.items() if n}

        # If target_role is passed from listener, use it
        target_role = target_role or state.get("target_role")

        # 2. Get top counters from SQLite for ALL enemy picks
        all_counters = []
        seen_counters = set()
        for enemy_role, enemy_name in enemy_team_names.items():
            # Get top 3 counters per enemy pick to keep the prompt size reasonable
            enemy_counters = get_counters(enemy_name, db_path=self.db_path, limit=3)
            for c in enemy_counters:
                if c['name'] not in seen_counters:
                    # Enrich counter info with which champion it counters
                    c['counters_who'] = enemy_name
                    all_counters.append(c)
                    seen_counters.add(c['name'])
        
        # 3. Generate AI recommendation
        try:
            recommendation = get_ai_recommendation(
                our_team_names, 
                enemy_team_names, 
                all_counters, 
                target_role=target_role
            )
            logging.info(f"AI Recommendation: {recommendation}")
            
            # 4. Send to Discord
            send_discord_message(recommendation)
        except Exception as e:
            logging.error(f"Error generating or sending recommendation: {e}")
            logging.error(traceback.format_exc())

    def resolve_champion_name(self, champion_id: int) -> str:
        if champion_id in self.name_cache:
            return self.name_cache[champion_id]

        if not os.path.exists(self.db_path):
            return str(champion_id)
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT ChampionName FROM champions WHERE ChampionID = ?", (champion_id,))
            row = cursor.fetchone()
            name = row[0] if row else None
            if name:
                self.name_cache[champion_id] = name
            return name
        finally:
            conn.close()

    def run(self):
        logging.info("Starting LCU Listener...")
        self.listener.start()

if __name__ == "__main__":
    if not os.path.exists("data/matchups.db"):
        logging.warning("Database data/matchups.db not found. Please run src/scripts/init_db.py first.")
    
    # Create and set a new event loop for the current thread
    # This resolves the 'no current event loop' error in Python 3.10+
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    orchestrator = Orchestrator()
    
    try:
        orchestrator.run()
    except KeyboardInterrupt:
        logging.info("Bot stopped by user.")
    finally:
        loop.close()
