import pytest
from unittest.mock import MagicMock, patch
from src.lcu.listener import LCUListener

@pytest.fixture
def mock_connector():
    with patch('src.lcu.listener.Connector') as mock:
        # Mock the connector instance to avoid event loop issues
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        yield mock_instance

def test_lcu_listener_parse_session(mock_connector):
    listener = LCUListener()
    
    # Mock session data
    session_data = {
        "myTeam": [
            {"championId": 1, "cellId": 0, "assignedPosition": "top"},
            {"championId": 0, "cellId": 1, "assignedPosition": "jungle"}
        ],
        "theirTeam": [
            {"championId": 2, "cellId": 5, "assignedPosition": "middle"},
            {"championId": 0, "cellId": 6, "assignedPosition": "bottom"}
        ],
        "actions": [
            [
                {"championId": 2, "completed": True, "type": "pick", "actorCellId": 5, "isAllyAction": False}
            ]
        ]
    }
    
    # We must call check_for_updates to update last_enemy_pick
    listener.check_for_updates(session_data)
    state = listener.parse_session(session_data)
    
    assert state['our_team'] == {"Top": 1}
    assert state['enemy_team'] == {"Mid": 2}
    assert listener.last_enemy_pick == 2

def test_lcu_listener_detect_new_pick(mock_connector):
    listener = LCUListener()
    listener.last_enemy_pick = 1
    
    # New pick is 2
    session_data = {
        "theirTeam": [{"championId": 2, "cellId": 5}],
        "actions": [[{"championId": 2, "completed": True, "type": "pick", "actorCellId": 5, "isAllyAction": False}]]
    }
    
    assert listener.check_for_updates(session_data) == "enemy_pick"
    assert listener.last_enemy_pick == 2
    
def test_lcu_listener_detect_our_turn(mock_connector):
    listener = LCUListener()
    
    # User is cellId 0
    session_data = {
        "localPlayerCellId": 0,
        "actions": [
            [
                {"id": 10, "actorCellId": 0, "completed": False, "type": "pick", "isAllyAction": True}
            ]
        ]
    }
    
    assert listener.check_for_updates(session_data) == "our_turn"
    assert listener.last_action_id == 10
    
    # Same action again
    assert listener.check_for_updates(session_data) is None
    
    # Different action ID
    session_data["actions"][0][0]["id"] = 11
    assert listener.check_for_updates(session_data) == "our_turn"
    assert listener.last_action_id == 11
