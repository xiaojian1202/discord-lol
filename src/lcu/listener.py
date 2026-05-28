import asyncio
import logging
from lcu_driver import Connector
from typing import Dict, List, Optional, Callable

class LCUListener:
    def __init__(self, on_enemy_pick: Optional[Callable[[Dict], None]] = None):
        self.connector: Optional[Connector] = None
        self.on_enemy_pick = on_enemy_pick
        self.last_enemy_pick: Optional[int] = None
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
        self.current_session = {}

    async def _on_session_update(self, connection, event):
        # If event type is DELETE, the lobby was closed
        if hasattr(event, 'type') and event.type == 'Delete':
            logging.info("Champion Select session ended.")
            self.last_enemy_pick = None
            self.current_session = {}
            return

        data = event.data
        if not data:
            # If data is empty, it might mean the lobby was dodged or ended
            if self.current_session:
                logging.info("Champion Select session cleared.")
                self.last_enemy_pick = None
                self.current_session = {}
            return
            
        self.current_session = data
        
        try:
            if self.is_new_enemy_pick(data):
                logging.info(f"New enemy pick detected: {self.last_enemy_pick}")
                if self.on_enemy_pick:
                    state = self.parse_session(data)
                    if asyncio.iscoroutinefunction(self.on_enemy_pick):
                        await self.on_enemy_pick(state)
                    else:
                        self.on_enemy_pick(state)
        except Exception as e:
            logging.error(f"Error processing session update: {e}")

    def is_new_enemy_pick(self, data: Dict) -> bool:
        """
        Detects if a new enemy champion has been locked in.
        """
        # Look through actions for completed enemy picks
        enemy_picks = []
        for action_group in data.get('actions', []):
            for action in action_group:
                if action['type'] == 'pick' and action['completed'] and not action['isAllyAction']:
                    enemy_picks.append(action['championId'])
        
        if not enemy_picks:
            return False
            
        latest_pick = enemy_picks[-1]
        if latest_pick != self.last_enemy_pick and latest_pick != 0:
            self.last_enemy_pick = latest_pick
            return True
            
        return False

    def parse_session(self, data: Dict) -> Dict:
        """
        Extracts relevant draft state from the LCU session data.
        """
        our_team = [p['championId'] for p in data.get('myTeam', []) if p['championId'] != 0]
        enemy_team = [p['championId'] for p in data.get('theirTeam', []) if p['championId'] != 0]
        
        return {
            "our_team": our_team,
            "enemy_team": enemy_team,
            "last_enemy_pick": self.last_enemy_pick
        }

    def start(self):
        logging.info("Starting LCU Listener...")
        self._setup_connector()
        self.connector.start()
