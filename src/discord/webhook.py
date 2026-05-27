import requests
import os
import logging
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

def send_discord_message(content: str, webhook_url: Optional[str] = None) -> bool:
    """
    Sends a message to a Discord channel via a Webhook.
    """
    url = webhook_url or os.getenv("DISCORD_WEBHOOK_URL")
    
    if not url:
        logging.error("Discord Webhook URL not provided.")
        return False
        
    payload = {
        "content": content,
        "username": "LoL Draft Coach",
        "avatar_url": "https://ddragon.leagueoflegends.com/cdn/14.1.1/img/profileicon/1.png" # Placeholder
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to send Discord message: {e}")
        return False
