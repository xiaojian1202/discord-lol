# Spec: Discord LoL Drafting Bot

## Objective
Build a Python-based coaching bot that monitors League of Legends drafting phases via the Riot LCU API. It will recommend counter-picks by combining historical matchup data (SQLite) with LLM-generated reasoning, delivering updates to a Discord channel via Webhooks.

## Tech Stack
- **Language:** Python 3.10+
- **APIs:** Riot LCU (via `lcu-driver`), Discord Webhooks
- **AI:** Triton GPT (OpenAI-compatible API)
- **Database:** SQLite (matchup statistics)
- **Data Source:** Kaggle LoL Match History dataset

## Commands
- **Initialize DB:** `python3 -m src.scripts.init_db --match-stats data/raw/MatchStatsTbl.csv --champions data/raw/ChampionTbl.csv --summoner-matches data/raw/SummonerMatchTbl.csv`
- **Run Bot:** `python3 -m src.main`
- **Test:** `python3 -m pytest`
- **Lint:** `ruff check .`

## Project Structure
```
discord-lol/
├── src/
│   ├── main.py              # Entry point & Orchestrator
│   ├── lcu/                 # LCU API polling & state management
│   ├── database/            # SQLite queries & schema
│   ├── ai/                  # LLM integration (OpenAI-compatible)
│   ├── discord/             # Webhook sender
│   ├── scripts/             # Data ingestion scripts
│   └── utils/               # Shared helpers (logging, config)
├── data/
│   ├── raw/                 # Landing spot for Kaggle CSV files
│   └── matchups.db          # SQLite DB file
├── tests/                   # Unit tests
├── .env                     # Secrets (Discord Webhook, AI API Key, Triton URL)
└── requirements.txt         # Dependencies
```

## Code Style
- **Type Hinting:** Required for all function signatures.
- **Asyncio:** Use `asyncio` for non-blocking LCU polling and AI requests.
- **Formatting:** Adhere to PEP 8 (via Ruff).

Example:
```python
async def get_counter_picks(champion_id: str) -> list[str]:
    """Retrieves top 3 counter picks from SQLite."""
    # ... logic here
```

## Testing Strategy
- **Framework:** Pytest
- **Mocks:** Mock LCU API responses and LLM calls to avoid external dependencies during testing.
- **Integration:** Test the end-to-end flow from a simulated draft state change to a Discord payload generation.

## Boundaries
- **Always:** Log LCU connection status, validate LLM responses before sending.
- **Ask first:** Adding new major dependencies, changing the SQLite schema.
- **Never:** Hardcode API keys or Webhook URLs (use `.env`).

## Success Criteria
1. Successfully detects entry into a LoL draft lobby.
2. Correctly identifies picked/banned champions for both teams.
3. Retrieves relevant counter-data from SQLite for the enemy's most recent pick.
4. Generates a readable recommendation via the LLM.
5. Sends the recommendation to Discord within 5 seconds of a state change.

## Implementation Details
1. **Database Ingestion:** A script `init_db.py` will parse the Kaggle CSV and calculate win rates/matchup stats to store in SQLite.
2. **AI Integration:** Use `openai` python library configured with Triton GPT's base URL.
3. **LCU Polling:** Use `riot-lcu` to listen for `ChampSelect` events.
4. **Counter Logic:** Calculate win rates of Champion A vs Champion B across the dataset, filtered by a minimum game threshold.
