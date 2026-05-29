import os
import logging
import random
from openai import OpenAI
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
load_dotenv()

def diagnostic_test():
    api_key = os.getenv("TRITON_API_KEY")
    base_url = os.getenv("TRITON_BASE_URL")
    model_name = os.getenv("TRITON_MODEL", "api-gpt-oss-120b")
    
    print(f"Testing Model: {model_name}")
    print(f"Base URL: {base_url}")
    
    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )

    # Test 1: Standard Pick Recommendation Prompt
    print("\n--- Test 1: Standard Pick Recommendation Prompt ---")
    try:
        prompt = """You are a professional League of Legends drafting coach. Provide a concise (1-2 sentences) recommendation for our next pick for Mid.

Current LoL Draft State:
Our Team: {'Top': 'Garen', 'Jng': 'Lee Sin'}
Enemy Team: {'Top': 'Darius', 'Jng': 'Elise'}
Available Roles on Our Team: Mid, ADC, Sup

Statistically strong counters for the enemy picks:
- Zed counters Darius
- Ahri counters Elise

CRITICAL INSTRUCTIONS:
1. Do NOT recommend a champion for a role that is already filled on our team.
2. Focus on why the pick is strong against their composition or how it synergizes with ours.
3. DO NOT THINK OUT LOUD. Provide ONLY the recommendation itself.
"""
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000
        )
        msg = response.choices[0].message
        content = getattr(msg, 'content', None)
        reasoning = getattr(msg, 'reasoning_content', None)
        print(f"Content: '{content}'")
        print(f"Reasoning Excerpt: '{str(reasoning)[:100]}...'" if reasoning else "Reasoning: None")
        print(f"Usage: {response.usage}")
        print(f"Finish Reason: {response.choices[0].finish_reason}")
    except Exception as e:
        print(f"Error: {e}")

    # Test 2: Fallback Prompt
    print("\n--- Test 2: Fallback Prompt ---")
    try:
        simple_prompt = "Give one sentence of LoL draft advice for Mid against Darius and Elise. Provide ONLY the advice, no reasoning."
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": simple_prompt}],
            max_tokens=500
        )
        msg = response.choices[0].message
        content = getattr(msg, 'content', None)
        print(f"Content: '{content}'")
        print(f"Usage: {response.usage}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    diagnostic_test()
