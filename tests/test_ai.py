import pytest
from unittest.mock import patch, MagicMock
from src.ai.client import get_ai_recommendation

@patch('src.ai.client.OpenAI')
def test_get_ai_recommendation(mock_openai):
    # Setup mock
    mock_client = MagicMock()
    mock_openai.return_value = mock_client
    
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content="Pick Zed because he counters Annie's low mobility."))
    ]
    mock_client.chat.completions.create.return_value = mock_response
    
    # Test data
    our_team = {"Top": "Malphite"}
    enemy_team = {"Mid": "Annie"}
    counters = [
        {"name": "Zed", "win_rate": 0.6, "total_games": 100},
        {"name": "Olaf", "win_rate": 0.55, "total_games": 150}
    ]
    
    recommendation = get_ai_recommendation(our_team, enemy_team, counters, target_role="Mid")
    
    assert "Zed" in recommendation
    assert "Annie" in recommendation
    mock_client.chat.completions.create.assert_called_once()
    
    # Check if prompt contains the data
    args, kwargs = mock_client.chat.completions.create.call_args
    prompt = kwargs['messages'][1]['content']
    assert "Zed" in prompt
    assert "Annie" in prompt
    assert "Malphite" in prompt
    assert "specifically for the Mid role" in prompt
