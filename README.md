# League of Legends Draft Coach

Draft recommendations powered by AI and historical match data.

## Features

- **Live LCU Integration:** Automatically detects champion select events in your League of Legends client.
- **AI Recommendations:** Uses LLM to provide nuanced advice based on team comps, counters, and synergy.
- **Discord Integration:** Sends suggestions directly to your Discord server via webhooks.
- **Draft Simulator:** Test your strategies and the AI logic without opening the game client.
- **Data-Driven Role Analysis:** Predicts enemy lanes using empirical trends from an 80k match dataset.

## Technical Pipelines

### 1. Data Ingestion Pipeline

The project processes large-scale match history data to build a local knowledge base.

- **Raw Data Source:** [Kaggle - 80k LoL Matches](https://www.kaggle.com/datasets/nathansmallcalder/lol-match-history-and-summoner-data-80k-matches) | Save the datasets under /data/raw
- **Ingestion Flow:** 
  1. Consumes `data/raw/*.csv` files.
  2. `analyze_roles.py` identifies flex-picks and lane distributions.
  3. `init_db.py` populates the SQLite `matchups.db`.

### 2. Recommendation Pipeline

The real-time decision-making flow:

1. **LCU Event:** `listener.py` detects a state change via WebSocket.
2. **State Enrichment:** `Orchestrator` resolves IDs and predicts ambiguous enemy roles based on analyzed flex-pick data.
3. **Context Construction:** Combines team comps, bans, and top 3 historical counters for each enemy pick.
4. **AI Analysis:** LLM analyzes the context to provide strategic reasoning (e.g., "Pick Jax because they lack hard CC and you have an AP-heavy mid").

## Testing & Validation

The system is verified through a comprehensive test suite targeting core logic:


| Component       | Test Case         | Status | Result                                                 |
| --------------- | ----------------- | ------ | ------------------------------------------------------ |
| **Database**    | `test_query.py`   | ✅ PASS | Successfully retrieves top counters by winrate         |
| **Data Ingest** | `test_init_db.py` | ✅ PASS | Correctly migrates CSV data to SQLite                  |
| **LCU Parser**  | `test_lcu.py`     | ✅ PASS | Accurately identifies user turn and enemy picks        |
| **Logic**       | `test_ai.py`      | ✅ PASS | Validates prompt construction and AI response handling |


## Documentation

- **[DEMO.md](DEMO.md):** Installation and run instructions.
- **[DESIGN.md](DESIGN.md):** System architecture and design decisions.
- **[Proposal/](proposal/):** Original and marked-up project proposals.
- **[Transcripts/](transcripts/):** Records of the development process.

## Demo Video

[Watch the Project Demo on YouTube](https://youtu.be/2HyEu-uHsyA)

## Setup & Installation

### Environment Setup

Create a `.env` file in the root directory. You can use the provided template:

```bash
cp .env.example .env
```

Ensure you provide your **API Key** and **Discord Webhook URL**.

### Quick Start

1. `pip install -r requirements.txt`
2. Launch the simulator immediately using the included pre-processed data:
  ```bash
   python3 -m src.scripts.sim_draft
  ```
3. (Optional) To refresh data from the raw datasets (requires downloading from Kaggle):
  ```bash
   python3 src/scripts/init_db.py
   python3 src/scripts/analyze_roles.py
  ```

