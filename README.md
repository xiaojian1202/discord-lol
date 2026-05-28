# Discord LoL Drafting Bot

A Python-based drafting coach that monitors League of Legends champion select and sends counter-pick recommendations to Discord.

## Features
- **Real-time Monitoring:** Uses Riot LCU API to detect enemy picks as they happen.
- **Data-Driven:** Queries a local SQLite database (populated from Kaggle datasets) for win rate statistics.
- **AI-Powered:** Uses Triton GPT (OpenAI-compatible) to generate tactical reasoning for counter-picks.
- **Discord Integration:** Sends structured recommendations via Webhooks.

## Prerequisites
- Python 3.10+
- League of Legends Client (must be running for the bot to work)
- Triton GPT API access
- Discord Webhook URL
- **Dataset:** [League of Legends Relational Database (Kaggle)](https://www.kaggle.com/datasets/nathansmallcalder/lol-match-history-and-summoner-data-80k-matches)

## Setup

### 1. Clone & Install
```bash
git clone https://github.com/xiaojian1202/discord-lol.git
cd discord-lol
pip install -r requirements.txt
```

### 2. Configuration
Copy `.env.example` to `.env` and fill in your keys:
```bash
cp .env.example .env
```
*Note: Do not share your `.env` file.*

### 3. Data Ingestion
The bot requires a local SQLite database built from the Kaggle dataset.
1. Download the dataset from [Kaggle](https://www.kaggle.com/datasets/nathansmallcalder/lol-match-history-and-summoner-data-80k-matches).
2. Extract the files and place `MatchStatsTbl.csv`, `ChampionTbl.csv`, and `SummonerMatchTbl.csv` into the `data/raw/` directory.
3. Run the ingestion script:
```bash
python3 -m src.scripts.init_db --match-stats data/raw/MatchStatsTbl.csv --champions data/raw/ChampionTbl.csv --summoner-matches data/raw/SummonerMatchTbl.csv
```

## Usage

### Run the Bot
Ensure the League Client is open and logged in, then run:
```bash
python3 -m src.main
```

### Run Tests
```bash
python3 -m pytest
```

### Draft Simulator (Mock Lobby)
To test the bot's AI logic and Discord integration without opening League of Legends:
```bash
python3 -m src.scripts.sim_draft
```
Follow the terminal prompts to select your lane and pick champions. The simulator will automatically trigger the bot's reasoning whenever a "bot" enemy locks in.

## Project Structure
- `src/lcu/`: Riot Client interaction logic.
- `src/database/`: SQLite query module.
- `src/ai/`: Triton GPT integration.
- `src/discord/`: Webhook sender.
- `src/scripts/`: Database initialization tools.
- `tests/`: Comprehensive test suite.
