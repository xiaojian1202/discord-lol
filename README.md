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
1. Place your CSV files (`MatchStatsTbl.csv`, `ChampionTbl.csv`, `SummonerMatchTbl.csv`) into `data/raw/`.
2. Run the ingestion script:
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

## Project Structure
- `src/lcu/`: Riot Client interaction logic.
- `src/database/`: SQLite query module.
- `src/ai/`: Triton GPT integration.
- `src/discord/`: Webhook sender.
- `src/scripts/`: Database initialization tools.
- `tests/`: Comprehensive test suite.
