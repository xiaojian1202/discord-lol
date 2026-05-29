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

import json

# Load Role Data from JSON
try:
    with open('src/scripts/role_data.json', 'r') as f:
        ROLE_DATA = json.load(f)
        ROLE_CHAMPIONS = ROLE_DATA['ROLE_CHAMPIONS']
        FLEX_CHAMPIONS = ROLE_DATA['FLEX_CHAMPIONS']
except FileNotFoundError:
    logging.warning("role_data.json not found. Run analyze_roles.py first. Using empty defaults.")
    ROLE_CHAMPIONS = {r: [] for r in ["Top", "Jng", "Mid", "ADC", "Sup"]}
    FLEX_CHAMPIONS = {}

ROLES = ["Top", "Jng", "Mid", "ADC", "Sup"]

class DraftSimulator:
    def __init__(self):
        self.orchestrator = Orchestrator()
        self.db_path = self.orchestrator.db_path
        self.blue_team = {}  # role -> champion_name
        self.red_team = {}   # role -> champion_name
        self.blue_bans = []
        self.red_bans = []
        
        # In a real game, you only know your own team's roles for sure (due to LCU)
        # For the enemy, you just see a list of champions picked.
        self.enemy_picks = [] # List of champion names in order picked
        
        self.user_team = ""  # "Blue" or "Red"
        self.user_lane = ""
        self.user_slot = -1  # 0-4
        self.enable_bans = False
        
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

    def predict_enemy_roles(self, enemy_picks: List[str]) -> Dict[str, str]:
        """
        Attempts to assign roles to enemy picks based on typical roles and flex potential.
        Returns a dict of role -> champion_name.
        """
        assigned = {}
        unassigned = enemy_picks.copy()
        remaining_roles = set(ROLES)

        # 1. First, assign obvious single-role champions
        for champ in unassigned[:]:
            primary_roles = [role for role, champs in ROLE_CHAMPIONS.items() if champ in champs]
            if len(primary_roles) == 1 and primary_roles[0] in remaining_roles:
                assigned[primary_roles[0]] = champ
                unassigned.remove(champ)
                remaining_roles.remove(primary_roles[0])

        # 2. Handle Flex picks with the remaining roles
        for champ in unassigned[:]:
            potential = FLEX_CHAMPIONS.get(champ, [])
            valid_potential = [r for r in potential if r in remaining_roles]
            if valid_potential:
                role = valid_potential[0] # Greedy assignment
                assigned[role] = champ
                unassigned.remove(champ)
                remaining_roles.remove(role)

        # 3. Fill the rest by checking any role they might fit
        for champ in unassigned[:]:
            for role in list(remaining_roles):
                if champ in ROLE_CHAMPIONS.get(role, []):
                    assigned[role] = champ
                    unassigned.remove(champ)
                    remaining_roles.remove(role)
                    break
        
        # 4. Total fallback for unknown or weird picks
        for champ in unassigned:
            if remaining_roles:
                role = list(remaining_roles)[0]
                assigned[role] = champ
                remaining_roles.remove(role)

        return assigned

    def get_viable_pick(self, role: str, team_picks: List[str], opponent_picks: List[str], is_ban: bool = False) -> str:
        """Determines a pick or ban."""
        all_picked = team_picks + opponent_picks + self.blue_bans + self.red_bans
        
        if is_ban:
            return random.choice([c for c in ROLE_CHAMPIONS[role] if c not in all_picked])

        # For bots, we still want them to pick something sensible for their role
        # even if the 'enemy' doesn't know what role they are.
        # Check if we can find an opponent likely in our lane
        predicted_opponents = self.predict_enemy_roles(opponent_picks)
        opponent_pick = predicted_opponents.get(role)
        
        if opponent_pick:
            counters = get_counters(opponent_pick, db_path=self.db_path, limit=10)
            if counters:
                role_viable = ROLE_CHAMPIONS[role]
                potential_counters = [c['name'] for c in counters if c['name'] in role_viable]
                available = [c for c in potential_counters if c not in all_picked]
                if available:
                    return random.choice(available[:3])

        available = [c for c in ROLE_CHAMPIONS[role] if c not in all_picked]
        # Occasionally pick a flex champion to make it interesting
        if not is_ban and random.random() < 0.3:
            flex_options = [c for c in FLEX_CHAMPIONS.keys() if c in available]
            if flex_options:
                return random.choice(flex_options)

        return random.choice(available) if available else "Unknown"

    async def run(self):
        print("=== League of Legends Draft Simulator (Role Ambiguity Mode) ===")
        
        # 0. Configuration
        ban_choice = input("Enable Ban Phase? (y/n): ").lower()
        self.enable_bans = ban_choice == 'y'

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
        self.user_team = random.choice(["Blue", "Red"])
        
        # Randomize lanes for bots (Internal knowledge)
        blue_lanes = ROLES.copy()
        random.shuffle(blue_lanes)
        red_lanes = ROLES.copy()
        random.shuffle(red_lanes)

        # Standard Tournament Draft Order
        draft_sequence = []
        if self.enable_bans:
            draft_sequence += [("Ban", "Blue", 0), ("Ban", "Red", 0), ("Ban", "Blue", 1), ("Ban", "Red", 1), ("Ban", "Blue", 2), ("Ban", "Red", 2)]
        draft_sequence += [("Pick", "Blue", 0), ("Pick", "Red", 0), ("Pick", "Red", 1), ("Pick", "Blue", 1), ("Pick", "Blue", 2), ("Pick", "Red", 2)]
        if self.enable_bans:
            draft_sequence += [("Ban", "Red", 3), ("Ban", "Blue", 3), ("Ban", "Red", 4), ("Ban", "Blue", 4)]
        draft_sequence += [("Pick", "Red", 3), ("Pick", "Blue", 3), ("Pick", "Blue", 4), ("Pick", "Red", 4)]

        total_actions = len(draft_sequence)
        for i, (action_type, team_side, slot_index) in enumerate(draft_sequence):
            is_our_side = (team_side == self.user_team)
            
            # Helper to get current lists
            our_picks = list(self.blue_team.values()) if self.user_team == "Blue" else list(self.red_team.values())
            enemy_picks = list(self.red_team.values()) if self.user_team == "Blue" else list(self.blue_team.values())
            
            ban_list = self.blue_bans if team_side == "Blue" else self.red_bans
            current_lane = blue_lanes[slot_index] if team_side == "Blue" else red_lanes[slot_index]

            print(f"\n[{i+1}/{total_actions}] {team_side} Team {action_type}...")

            is_user_turn = (is_our_side and current_lane == self.user_lane)
            
            if action_type == "Ban":
                if is_user_turn:
                    ban = input(f"--> YOUR TURN! Enter your BAN for {current_lane}: ").strip().title()
                    ban_list.append(ban)
                else:
                    ban = self.get_viable_pick(current_lane, our_picks, enemy_picks, is_ban=True)
                    ban_list.append(ban)
                    print(f"--> {team_side} Bot BANNED {ban}")
            else:
                # Pick logic
                if is_user_turn:
                    print(f"--> Generating recommendation for YOUR pick ({self.user_lane})...")
                    
                    # USER only knows their team's lanes, and predicts enemy lanes
                    predicted_enemy_team = self.predict_enemy_roles(enemy_picks)
                    
                    state = {
                        "our_team": {role: self.get_id(champ) for role, champ in (self.blue_team if self.user_team == "Blue" else self.red_team).items()},
                        "enemy_team": {role: self.get_id(champ) for role, champ in predicted_enemy_team.items()},
                        "last_enemy_pick": self.get_id(enemy_picks[-1]) if enemy_picks else None
                    }
                    await self.orchestrator.handle_enemy_pick(state, target_role=self.user_lane)
                    
                    while True:
                        pick = input(f"--> YOUR TURN! Enter your champion for {self.user_lane}: ").strip().title()
                        if pick == "Kaisa": pick = "Kai'Sa"
                        if pick == "Khazix": pick = "Kha'Zix"
                        
                        all_picked = list(self.blue_team.values()) + list(self.red_team.values()) + self.blue_bans + self.red_bans
                        if pick in all_picked:
                            print(f"{pick} is already picked/banned. Choose another.")
                        else:
                            if self.user_team == "Blue": self.blue_team[self.user_lane] = pick
                            else: self.red_team[self.user_lane] = pick
                            break
                else:
                    # Bot pick logic (using internal lane knowledge)
                    pick = self.get_viable_pick(current_lane, our_picks, enemy_picks)
                    if team_side == "Blue": self.blue_team[current_lane] = pick
                    else: self.red_team[current_lane] = pick
                    print(f"--> {team_side} Bot picked {pick}")

                    # If it was an enemy pick, trigger recommendation
                    if not is_our_side:
                        updated_enemy_picks = list(self.red_team.values()) if self.user_team == "Blue" else list(self.blue_team.values())
                        predicted_enemy_team = self.predict_enemy_roles(updated_enemy_picks)
                        
                        state_for_orch = {
                            "our_team": {role: self.get_id(champ) for role, champ in (self.blue_team if self.user_team == "Blue" else self.red_team).items()},
                            "enemy_team": {role: self.get_id(champ) for role, champ in predicted_enemy_team.items()},
                            "last_enemy_pick": self.get_id(pick)
                        }
                        await self.orchestrator.handle_enemy_pick(state_for_orch)
            
            await asyncio.sleep(1)

        print("\n=== Draft Summary ===")
        print(f"Blue Bans: {', '.join(self.blue_bans)}")
        print(f"Red Bans:  {', '.join(self.red_bans)}")
        blue_pick_str = ", ".join([f"{r}: {c}" for r, c in self.blue_team.items()])
        red_pick_str = ", ".join([f"{r}: {c}" for r, c in self.red_team.items()])
        print(f"Blue Team: {blue_pick_str}")
        print(f"Red Team:  {red_pick_str}")
        print("======================")

if __name__ == "__main__":
    sim = DraftSimulator()
    asyncio.run(sim.run())
