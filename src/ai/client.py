import os
from openai import OpenAI
from dotenv import load_dotenv
from typing import List, Dict, Any

load_dotenv()

def get_ai_recommendation(draft_state: Dict[str, List[str]], counters: List[Dict[str, Any]]) -> str:
    """
    Generates a concise drafting recommendation using Triton GPT.
    """
    api_key = os.getenv("TRITON_API_KEY", "dummy")
    base_url = os.getenv("TRITON_BASE_URL", "https://api.openai.com/v1")
    
    client = OpenAI(api_key=api_key, base_url=base_url)
    
    our_team = ", ".join(draft_state.get("our_team", []))
    enemy_team = ", ".join(draft_state.get("enemy_team", []))
    
    counter_info = "\n".join([
        f"- {c['name']} (Win rate vs enemy: {c['win_rate']:.1%}, games: {c['total_games']})"
        for c in counters
    ])
    
    prompt = f"""
Current LoL Draft State:
Our Team: {our_team if our_team else "None yet"}
Enemy Team: {enemy_team if enemy_team else "None yet"}

Statistically strong counters for the enemy picks:
{counter_info}

Based on this, provide a concise (1-2 sentences) recommendation for our next pick. Focus on why the counter is strong or how it fits our current team composition.
"""

    response = client.chat.completions.create(
        model="gpt-4o", # Model name might need adjustment for Triton
        messages=[
            {"role": "system", "content": "You are a professional League of Legends drafting coach."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=150
    )
    
    return response.choices[0].message.content.strip()
