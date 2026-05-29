# Demo Instructions

## Prerequisites

- **Python 3.10+**
- **League of Legends Client** (Optional, only for real-time LCU listener)
- **Discord Webhook URL** (For receiving recommendations)

## Setup

1.  **Clone the Repository:**
    ```bash
    git clone <your-repo-url>
    cd discord-lol
    ```

2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure Environment:**
    Create a `.env` file in the root directory:
    ```env
    DATABASE_PATH=data/matchups.db
    DISCORD_WEBHOOK_URL=your_discord_webhook_url_here
    GEMINI_API_KEY=your_google_gemini_api_key_here
    ```

    ### How to get a Discord Webhook URL:
    1.  Open your Discord server and navigate to the channel where you want to receive recommendations.
    2.  Click on the **Edit Channel** (gear icon) next to the channel name.
    3.  Select **Integrations** from the left sidebar.
    4.  Click on **Webhooks** and then **New Webhook**.
    5.  (Optional) Customize the name and avatar of the bot.
    6.  Click **Copy Webhook URL** and paste it into your `.env` file as `DISCORD_WEBHOOK_URL`.

4.  **Data Setup:**
    The project includes pre-processed champion and matchup data (`data/matchups.db` and `src/scripts/role_data.json`). **You can run the tool immediately using these files.**

    If you wish to re-run the analysis or expand the database, you must download the raw dataset:
    - **Dataset Source:** [Kaggle - 80k LoL Matches](https://www.kaggle.com/datasets/nathansmallcalder/lol-match-history-and-summoner-data-80k-matches)
    - **Instructions:** Download and extract the CSV files into the `data/raw/` directory.

    Once the raw data is in place, you can initialize the database or refresh role trends:
    ```bash
    python3 src/scripts/init_db.py
    python3 src/scripts/analyze_roles.py
    ```

## Running the Tool

### 1. Draft Simulator (Recommended for Testing)
Test the recommendation engine without needing the League Client open. This mode simulates a full tournament draft with role ambiguity and bans.
```bash
python3 -m src.scripts.sim_draft
```

### 2. Live LCU Listener
Automatically detect champion select sessions in an active League of Legends client.
```bash
python3 -m src.main
```

### 3. Role Analysis
Update the simulator's knowledge of champion roles based on the raw dataset.
```bash
python3 src/scripts/analyze_roles.py
```

## Troubleshooting
- If you encounter "no current event loop" errors, ensure you are running the scripts as modules (using `-m`) or using the latest Python version.
- Ensure your `DISCORD_WEBHOOK_URL` is valid to see the AI recommendations.
