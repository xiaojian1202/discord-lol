import os
import sqlite3
import logging
import asyncio
import traceback
from typing import Dict
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

    async def handle_enemy_pick(self, state: dict):
        last_pick_id = state.get("last_enemy_pick")
        if not last_pick_id:
            return

        # 1. Resolve champion ID to name
        champion_name = self.resolve_champion_name(last_pick_id)
        if not champion_name:
            logging.warning(f"Could not resolve champion name for ID: {last_pick_id}")
            return

        logging.info(f"Processing recommendation for enemy pick: {champion_name}")

        # 2. Get our and enemy team names for context
        our_team_names = [self.resolve_champion_name(cid) for cid in state.get("our_team", [])]
        enemy_team_names = [self.resolve_champion_name(cid) for cid in state.get("enemy_team", [])]
        
        draft_state_names = {
            "our_team": [n for n in our_team_names if n],
            "enemy_team": [n for n in enemy_team_names if n]
        }

        # 3. Get top counters from SQLite
        counters = get_counters(champion_name, db_path=self.db_path)
        if not counters:
            logging.info(f"No specific counter data found for {champion_name}")
            # We can still ask the AI for general advice
        
        # 4. Generate AI recommendation
        try:
            recommendation = get_ai_recommendation(draft_state_names, counters)
            logging.info(f"AI Recommendation: {recommendation}")
            
            # 5. Send to Discord
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
    
    # Create the orchestrator - this should no longer trigger a RuntimeError
    # since Connector() is now lazy-loaded in listener.py
    orchestrator = Orchestrator()
    
    try:
        orchestrator.run()
    except KeyboardInterrupt:
        logging.info("Bot stopped by user.")
