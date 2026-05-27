import pytest
import requests
from unittest.mock import patch, MagicMock
from src.discord.webhook import send_discord_message

@patch('src.discord.webhook.requests.post')
def test_send_discord_message(mock_post):
    # Setup mock
    mock_response = MagicMock()
    mock_response.status_code = 204
    mock_post.return_value = mock_response
    
    webhook_url = "https://discord.com/api/webhooks/test"
    content = "Pick Zed!"
    
    success = send_discord_message(content, webhook_url=webhook_url)
    
    assert success is True
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert kwargs['json']['content'] == content
    assert "Zed" in kwargs['json']['content']

@patch('src.discord.webhook.requests.post')
def test_send_discord_message_failure(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("Bad Request")
    mock_post.return_value = mock_response
    
    success = send_discord_message("test", webhook_url="http://fail")
    assert success is False
