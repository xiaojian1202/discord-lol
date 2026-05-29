import os
import logging
import time
import random
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
    Includes retry logic and backoff to handle rate limits and empty responses.
    """
    api_key = os.getenv("TRITON_API_KEY", "dummy")
    base_url = os.getenv("TRITON_BASE_URL", "https://api.openai.com/v1")
    model_name = os.getenv("TRITON_MODEL", "AWS Instructional")
    
    client = OpenAI(api_key=api_key, base_url=base_url)
    
    our_team_str = ", ".join([f"{r}: {c}" for r, c in our_team.items()]) if our_team else "None"
    enemy_team_str = ", ".join([f"{r}: {c}" for r, c in enemy_team.items()]) if enemy_team else "None"
    
    counter_info = "\n".join([
        f"- {c['name']} (Win rate vs {c.get('counters_who', 'enemy')}: {c['win_rate']:.1%}, games: {c['total_games']})"
        for c in counters
    ])
    
    target_clause = f" specifically for the {target_role} role" if target_role else ""
    roles_list = ["Top", "Jng", "Mid", "ADC", "Sup"]
    available_roles = [r for r in roles_list if r not in our_team]
    
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
4. DO NOT THINK OUT LOUD. Provide ONLY the recommendation itself.
"""

    max_retries = 3
    base_delay = 2.0 # Seconds to wait before retrying

    for attempt in range(max_retries):
        try:
            logging.debug(f"AI Attempt {attempt + 1}/{max_retries}...")
            
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1000 # Increased to allow for reasoning models
            )
            
            choice = response.choices[0]
            content = getattr(choice.message, 'content', None)
            
            if content and content.strip():
                return content.strip()
            
            finish_reason = getattr(choice, 'finish_reason', 'unknown')
            usage = getattr(response, 'usage', 'unknown')
            logging.warning(f"Empty content received on attempt {attempt + 1}. Finish reason: {finish_reason}. Usage: {usage}")
            
        except Exception as e:
            logging.error(f"AI request failed on attempt {attempt + 1}: {e}")
        
        # Backoff before next attempt
        if attempt < max_retries - 1:
            delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
            logging.info(f"Retrying in {delay:.2f} seconds...")
            time.sleep(delay)

    # Final fallback attempt with simplified prompt
    try:
        logging.info("Attempting final fallback with simplified prompt...")
        simple_prompt = f"Give one sentence of LoL draft advice for {target_role or 'this pick'} against {enemy_team_str}. Provide ONLY the advice, no reasoning."
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": simple_prompt}],
            temperature=0.1,
            max_tokens=500 # Increased to allow for reasoning models
        )
        content = getattr(response.choices[0].message, 'content', None)
        if content and content.strip():
            return content.strip()
    except Exception as e:
        logging.error(f"Final fallback failed: {e}")

    return "AI provided an empty recommendation. Stick to high-winrate counters listed above."
