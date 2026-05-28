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
        last_pick_id = state.get("last_enemy_pick")
        # If we have a target_role, we might not have a last_enemy_pick (e.g. if we are first and asking for advice)
        # but for now logic is triggered on pick.
        
        champion_name = None
        if last_pick_id:
            champion_name = self.resolve_champion_name(last_pick_id)
            if champion_name:
                logging.info(f"Processing recommendation for enemy pick: {champion_name}")
            else:
                logging.warning(f"Could not resolve champion name for ID: {last_pick_id}")

        # 2. Convert ID dictionaries to name dictionaries
        our_team_ids = state.get("our_team", {})
        enemy_team_ids = state.get("enemy_team", {})
        
        our_team_names = {role: self.resolve_champion_name(cid) for role, cid in our_team_ids.items()}
        enemy_team_names = {role: self.resolve_champion_name(cid) for role, cid in enemy_team_ids.items()}
        
        # Filter out None names
        our_team_names = {r: n for r, n in our_team_names.items() if n}
        enemy_team_names = {r: n for r, n in enemy_team_names.items() if n}

        # 3. Get top counters from SQLite for the last enemy pick
        counters = []
        if champion_name:
            counters = get_counters(champion_name, db_path=self.db_path)
        
        # 4. Generate AI recommendation
        try:
            recommendation = get_ai_recommendation(
                our_team_names, 
                enemy_team_names, 
                counters, 
                target_role=target_role
            )
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
