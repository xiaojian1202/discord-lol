import os
import logging
from openai import OpenAI
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional


load_dotenv()

def get_ai_recommendation(
    our_team: Dict[str, str], 
    enemy_team: Dict[str, str], 
    counters: List[Dict[str, Any]],
    target_role: Optional[str] = None
) -> str:
    """
    Generates a concise drafting recommendation using Triton GPT.
    our_team/enemy_team: Dict mapping role -> champion_name
    """
    api_key = os.getenv("TRITON_API_KEY", "dummy")
    base_url = os.getenv("TRITON_BASE_URL", "https://api.openai.com/v1")
    
    client = OpenAI(api_key=api_key, base_url=base_url)
    
    our_team_str = ", ".join([f"{r}: {c}" for r, c in our_team.items()]) if our_team else "None"
    enemy_team_str = ", ".join([f"{r}: {c}" for r, c in enemy_team.items()]) if enemy_team else "None"
    
    counter_info = "\n".join([
        f"- {c['name']} (Win rate vs enemy: {c['win_rate']:.1%}, games: {c['total_games']})"
        for c in counters
    ])
    
    target_clause = f" specifically for the {target_role} role" if target_role else ""
    roles_list = ["Top", "Jng", "Mid", "ADC", "Sup"]
    available_roles = [r for r in roles_list if r not in our_team]
    
    # Combined prompt for instructional models
    prompt = f"""You are a professional League of Legends drafting coach. Provide a concise (1-2 sentences) recommendation for our next pick{target_clause}.

Current LoL Draft State:
Our Team: {our_team_str}
Enemy Team: {enemy_team_str}
Available Roles on Our Team: {available_roles}

Statistically strong counters for the enemy picks:
{counter_info}

CRITICAL INSTRUCTIONS:
1. Do NOT recommend a champion for a role that is already filled on our team.
2. Focus on why the pick is strong against their composition or how it synergizes with ours.
3. If no specific counters are provided above, suggest a strong general pick for the role.
"""

    model_name = os.getenv("TRITON_MODEL", "AWS Instructional")
    logging.debug(f"AI Prompt: {prompt}")

    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=150
    )
    
    content = response.choices[0].message.content
    if not content:
        logging.warning("AI returned empty content. Retrying with simpler prompt...")
        # Fallback to even simpler prompt if empty
        simple_prompt = f"Give me a 1-sentence LoL pick recommendation for {target_role or 'any role'} against {enemy_team_str}."
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": simple_prompt}],
            temperature=0.7,
            max_tokens=50
        )
        content = response.choices[0].message.content

    return content.strip() if content else "AI provided an empty recommendation."
