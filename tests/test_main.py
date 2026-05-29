import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from src.main import Orchestrator

@pytest.mark.asyncio
@patch('src.main.os.path.exists')
@patch('src.lcu.listener.Connector')
@patch('src.main.get_counters')
@patch('src.main.get_ai_recommendation')
@patch('src.main.send_discord_message')
@patch('src.main.sqlite3.connect')
async def test_orchestrator_handle_enemy_pick(mock_sqlite, mock_send, mock_ai, mock_counters, mock_connector, mock_exists):
    # Setup mocks
    mock_exists.return_value = True
    mock_conn = MagicMock()
    mock_sqlite.return_value = mock_conn
    mock_cursor = mock_conn.cursor.return_value
    # sqlite3 fetchone returns a tuple/row, so [0] access works
    mock_cursor.fetchone.return_value = ("Annie",)
    
    mock_counters.return_value = [{"name": "Zed", "win_rate": 0.6, "total_games": 100}]
    mock_ai.return_value = "Pick Zed!"
    mock_send.return_value = True
    
    orchestrator = Orchestrator()
    
    state = {
        "our_team": {"Top": 1},
        "enemy_team": {"Mid": 2},
        "last_enemy_pick": 2
    }
    
    await orchestrator.handle_enemy_pick(state)
    
    # Verify the flow
    mock_counters.assert_called_once_with("Annie", db_path='data/matchups.db', limit=3)
    mock_ai.assert_called_once()
    mock_send.assert_called_once_with("Pick Zed!")
