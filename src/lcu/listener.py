import asyncio
import logging
from lcu_driver import Connector
from typing import Dict, List, Optional, Callable

class LCUListener:
    def __init__(self, on_enemy_pick: Optional[Callable[[Dict], None]] = None):
        self.connector: Optional[Connector] = None
        self.on_enemy_pick = on_enemy_pick
        self.last_enemy_pick: Optional[int] = None
        self.last_action_id: Optional[int] = None
        self.current_session: Dict = {}

    def _setup_connector(self):
        if self.connector:
            return
            
        self.connector = Connector()
        # Register events
        self.connector.ready(self._on_ready)
        self.connector.close(self._on_close)
        
        # Using the register method as a decorator to register the callback
        @self.connector.ws.register('/lol-champ-select/v1/session', event_types=('UPDATE', 'CREATE', 'DELETE'))
        async def session_update_wrapper(connection, event):
            await self._on_session_update(connection, event)

    async def _on_ready(self, connection):
        logging.info("LCU API is ready. Connected to League Client.")
        # Initial check
        res = await connection.request('get', '/lol-champ-select/v1/session')
        if res.status == 200:
            data = await res.json()
            class MockEvent:
                def __init__(self, data):
                    self.data = data
            await self._on_session_update(connection, MockEvent(data))

    async def _on_close(self, connection):
        logging.info("League Client closed. Waiting for reconnect...")
        self.last_enemy_pick = None
        self.last_action_id = None
        self.current_session = {}

    async def _on_session_update(self, connection, event):
        # If event type is DELETE, the lobby was closed
        if hasattr(event, 'type') and event.type == 'Delete':
            logging.info("Champion Select session ended.")
            self.last_enemy_pick = None
            self.last_action_id = None
            self.current_session = {}
            return

        data = event.data
        if not data:
            if self.current_session:
                logging.info("Champion Select session cleared.")
                self.last_enemy_pick = None
                self.last_action_id = None
                self.current_session = {}
            return
            
        self.current_session = data
        
        try:
            update_reason = self.check_for_updates(data)
            if update_reason:
                logging.info(f"Draft update detected: {update_reason}")
                if self.on_enemy_pick:
                    state = self.parse_session(data)
                    # Pass target_role if it's our turn
                    if update_reason == "our_turn":
                        target_role = state.get("target_role")
                        if asyncio.iscoroutinefunction(self.on_enemy_pick):
                            await self.on_enemy_pick(state, target_role=target_role)
                        else:
                            self.on_enemy_pick(state, target_role=target_role)
                    else:
                        if asyncio.iscoroutinefunction(self.on_enemy_pick):
                            await self.on_enemy_pick(state)
                        else:
                            self.on_enemy_pick(state)
        except Exception as e:
            logging.error(f"Error processing session update: {e}")

    def check_for_updates(self, data: Dict) -> Optional[str]:
        """
        Detects if a new enemy pick or if it's the user's turn.
        Returns the reason for update, or None.
        """
        local_cell_id = data.get('localPlayerCellId')
        actions = data.get('actions', [])
        
        # 1. Check for new enemy picks
        enemy_picks = []
        for action_group in actions:
            for action in action_group:
                if action['type'] == 'pick' and action['completed'] and not action['isAllyAction']:
                    enemy_picks.append(action['championId'])
        
        if enemy_picks:
            latest_pick = enemy_picks[-1]
            if latest_pick != self.last_enemy_pick and latest_pick != 0:
                self.last_enemy_pick = latest_pick
                return "enemy_pick"

        # 2. Check if it's our turn to pick
        for action_group in actions:
            for action in action_group:
                # If it's a pick action for us, and it's active (not completed)
                # In LCU, isInProgress might not be reliable, but actorCellId matches 
                # and it's the first non-completed pick action in the sequence.
                if action['actorCellId'] == local_cell_id and action['type'] == 'pick' and not action['completed']:
                    # We need to make sure this is the *current* active action
                    # LCU session has 'timer' which can help, but usually 
                    # there's only one active action group.
                    if action['id'] != self.last_action_id:
                        self.last_action_id = action['id']
                        return "our_turn"
        
        return None

    def parse_session(self, data: Dict) -> Dict:
        """
        Extracts relevant draft state from the LCU session data, including roles.
        """
        role_map = {
            "top": "Top",
            "jungle": "Jng",
            "middle": "Mid",
            "bottom": "ADC",
            "utility": "Sup"
        }

        local_cell_id = data.get('localPlayerCellId')
        target_role = None

        def get_team_roles(team_data, is_our_team=False):
            nonlocal target_role
            team_dict = {}
            for p in team_data:
                cid = p.get('championId', 0)
                pos = p.get('assignedPosition', '').lower()
                role_name = role_map.get(pos, f"Pick_{p.get('cellId')}")
                
                if cid != 0:
                    team_dict[role_name] = cid
                
                if is_our_team and p.get('cellId') == local_cell_id:
                    target_role = role_map.get(pos)
                    
            return team_dict

        our_team = get_team_roles(data.get('myTeam', []), is_our_team=True)
        enemy_team = get_team_roles(data.get('theirTeam', []))
        
        return {
            "our_team": our_team,
            "enemy_team": enemy_team,
            "last_enemy_pick": self.last_enemy_pick,
            "target_role": target_role
        }

    def start(self):
        logging.info("Starting LCU Listener...")
        self._setup_connector()
        self.connector.start()
