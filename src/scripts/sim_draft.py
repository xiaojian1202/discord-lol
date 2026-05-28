import asyncio
import random
import logging
import sqlite3
import os
from typing import Dict, List, Optional
from src.main import Orchestrator
from src.database.query import get_counters

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Viable Champions per Role (Popular examples)
ROLE_CHAMPIONS = {
    "Top": ["Darius", "Garen", "Fiora", "Jax", "Malphite", "Aatrox", "Camille", "Sett", "Mordekaiser", "Ornn"],
    "Jng": ["Lee Sin", "Jarvan IV", "Vi", "Kha'Zix", "Sejuani", "Zac", "Elise", "Hecarim", "Kayn", "Kindred"],
    "Mid": ["Ahri", "Zed", "Yasuo", "Orianna", "Syndra", "LeBlanc", "Katarina", "Viktor", "Akali", "Annie"],
    "ADC": ["Caitlyn", "Ezreal", "Kai'Sa", "Jinx", "Vayne", "Lucian", "Ashe", "Jhin", "Tristana", "Miss Fortune"],
    "Sup": ["Thresh", "Lulu", "Leona", "Nami", "Blitzcrank", "Morgana", "Janna", "Pyke", "Karma", "Nautilus"]
}

ROLES = ["Top", "Jng", "Mid", "ADC", "Sup"]

class DraftSimulator:
    def __init__(self):
        self.orchestrator = Orchestrator()
        self.db_path = self.orchestrator.db_path
        self.blue_team = {}  # role -> champion_name
        self.red_team = {}   # role -> champion_name
        self.user_team = ""  # "Blue" or "Red"
        self.user_lane = ""
        self.user_slot = -1  # 0-4
        
        # Mapping names to IDs for Orchestrator
        self.name_to_id = self._load_champion_ids()

    def _load_champion_ids(self) -> Dict[str, int]:
        if not os.path.exists(self.db_path):
            return {}
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT ChampionName, ChampionID FROM champions")
        mapping = {row[0]: row[1] for row in cursor.fetchall()}
        conn.close()
        return mapping

    def get_id(self, name: str) -> int:
        return self.name_to_id.get(name, 0)

    def get_viable_pick(self, role: str, team: Dict[str, str], opponent_team: Dict[str, str]) -> str:
        """Determines a pick based on role and opponent."""
        # Check if opponent in the same lane has picked
        opponent_pick = opponent_team.get(role)
        
        if opponent_pick:
            # Try to counterpick using DB
            counters = get_counters(opponent_pick, db_path=self.db_path, limit=10)
            if counters:
                # Filter counters to only include those viable for the role
                role_viable = ROLE_CHAMPIONS[role]
                potential_counters = [c['name'] for c in counters if c['name'] in role_viable]
                
                # Exclude already picked champions
                all_picked = list(self.blue_team.values()) + list(self.red_team.values())
                available = [c for c in potential_counters if c not in all_picked]
                
                if available:
                    return random.choice(available[:3]) # Pick from top 3 available counters

        # Default: Pick a random viable champion for the role that hasn't been picked
        all_picked = list(self.blue_team.values()) + list(self.red_team.values())
        available = [c for c in ROLE_CHAMPIONS[role] if c not in all_picked]
        return random.choice(available) if available else "Unknown"

    async def run(self):
        print("=== League of Legends Draft Simulator ===")
        
        # 1. Lane Selection
        while True:
            choice = input(f"Select your lane ({', '.join(ROLES)}): ").strip().title()
            if choice == "Adc": choice = "ADC"
            if choice == "Jungle": choice = "Jng"
            if choice in ROLES:
                self.user_lane = choice
                break
            print("Invalid lane. Please try again.")

        # 2. Team and Slot Assignment
        # User is never Blue 1 (First pick overall)
        self.user_team = random.choice(["Blue", "Red"])
        if self.user_team == "Blue":
            self.user_slot = random.randint(1, 4) # Slots 1-4 (B2-B5)
        else:
            self.user_slot = random.randint(0, 4) # Slots 0-4 (R1-R5)

        print(f"\nYou are on the {self.user_team} Team playing {self.user_lane}!")
        
        # Randomize lanes for bots
        blue_lanes = ROLES.copy()
        random.shuffle(blue_lanes)
        red_lanes = ROLES.copy()
        random.shuffle(red_lanes)

        # Map pick slots to (Team, Role)
        # B1, R1-R2, B2-B3, R3-R4, B4-B5, R5
        draft_order = [
            ("Blue", 0), 
            ("Red", 0), ("Red", 1), 
            ("Blue", 1), ("Blue", 2),
            ("Red", 2), ("Red", 3),
            ("Blue", 3), ("Blue", 4),
            ("Red", 4)
        ]

        # Process Draft
        # Standard tournament draft order: B1, R1-R2, B2-B3, R3-R4, B4-B5, R5
        draft_phases = [
            [("Blue", 0)], # B1
            [("Red", 0), ("Red", 1)], # R1-R2
            [("Blue", 1), ("Blue", 2)], # B2-B3
            [("Red", 2), ("Red", 3)], # R3-R4
            [("Blue", 3), ("Blue", 4)], # B4-B5
            [("Red", 4)] # R5
        ]

        total_picks = 0
        for phase in draft_phases:
            for team_side, slot_index in phase:
                total_picks += 1
                team_dict = self.blue_team if team_side == "Blue" else self.red_team
                opp_dict = self.red_team if team_side == "Blue" else self.blue_team
                current_lane = blue_lanes[slot_index] if team_side == "Blue" else red_lanes[slot_index]

                print(f"\n[{total_picks}/10] {team_side} Team is picking for {current_lane}...")

                # Is it the user?
                if team_side == self.user_team and current_lane == self.user_lane:
                    while True:
                        pick = input(f"--> YOUR TURN! Enter your champion for {current_lane}: ").strip().title()
                        # Handle some common name variations
                        if pick == "Kaisa": pick = "Kai'Sa"
                        if pick == "Khazix": pick = "Kha'Zix"
                        
                        all_picked = list(self.blue_team.values()) + list(self.red_team.values())
                        if pick in all_picked:
                            print(f"{pick} is already picked. Choose another.")
                        else:
                            team_dict[current_lane] = pick
                            break
                else:
                    # Bot pick
                    pick = self.get_viable_pick(current_lane, team_dict, opp_dict)
                    team_dict[current_lane] = pick
                    print(f"--> {team_side} Bot picked {pick}")

                # If it's an ENEMY pick, trigger Orchestrator
                if team_side != self.user_team:
                    user_side_dict = self.blue_team if self.user_team == "Blue" else self.red_team
                    enemy_side_dict = self.red_team if self.user_team == "Blue" else self.blue_team
                    
                    real_state = {
                        "our_team": [self.get_id(c) for c in user_side_dict.values()],
                        "enemy_team": [self.get_id(c) for c in enemy_side_dict.values()],
                        "last_enemy_pick": self.get_id(pick)
                    }
                    await self.orchestrator.handle_enemy_pick(real_state)
                
                # If there's only one pick in this phase, or it's the last pick of a double-pick phase, pause.
                # However, the user requested a pause after EVERY lock in.
                print("Waiting 5 seconds for draft to stabilize...")
                await asyncio.sleep(5)

        print("\n=== Draft Summary ===")
        print(f"Blue Team: {', '.join([f'{r}: {c}' for r, c in self.blue_team.items()])}")
        print(f"Red Team:  {', '.join([f'{r}: {c}' for r, c in self.red_team.items()])}")
        print("======================")

if __name__ == "__main__":
    sim = DraftSimulator()
    asyncio.run(sim.run())
