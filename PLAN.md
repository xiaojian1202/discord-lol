# Implementation Plan: Discord LoL Drafting Bot

## Phase 1: Foundation & Data
- [x] **Task 1: Setup Environment**
  - Create `requirements.txt` with `riot-lcu`, `openai`, `python-dotenv`, `pandas`, `requests`, `pytest`.
  - Create `.env.example` with placeholders for Triton URL, AI Key, and Discord Webhook.
- [x] **Task 2: Data Ingestion Script**
  - Script: `src/scripts/init_db.py`.
  - Input: CSV files in `data/raw/`.
  - Logic: Group by champion matchups, calculate win rates, store in SQLite `data/matchups.db`.
  - Verification: Run script and verify table contents via SQLite CLI.

## Phase 2: Core Modules
- [x] **Task 3: Database Query Interface**
  - Module: `src/database/query.py`.
  - Function: `get_counters(champion_name: str, limit: int = 5)`.
  - Verification: Unit test with sample data.
- [x] **Task 4: AI Integration (Triton)**
  - Module: `src/ai/client.py`.
  - Logic: Prompt template for "Given [Draft State] and [Counter Data], suggest a pick".
  - Verification: Mock the Triton API response.
- [x] **Task 5: Discord Webhook Sender**
  - Module: `src/discord/webhook.py`.
  - Logic: Simple POST request to Discord webhook URL.
  - Verification: Send a test message to a private channel.

## Phase 3: LCU & Orchestration
- [x] **Task 6: LCU Event Listener**
  - Module: `src/lcu/listener.py`.
  - Logic: Connect to Riot Client, subscribe to `ChampSelect` events.
  - State Management: Track current bans/picks for both teams.
  - Verification: Log state changes while the client is in a custom/practice lobby.
- [x] **Task 7: Main Orchestrator**
  - File: `src/main.py`.
  - Logic: Link LCU events -> DB query -> AI suggestion -> Discord message.
  - Verification: End-to-end test in a live lobby.

## Risks & Mitigations
- **LCU Connection:** Riot Client must be running. Mitigation: Robust retry logic and status logging.
- **Data Quality:** Kaggle dataset might be outdated or missing champions. Mitigation: Allow the AI to "know" if data is missing and provide general advice.
- **Triton Latency:** AI generation might be slow. Mitigation: Async processing to not block the LCU listener.
