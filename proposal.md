# Project Proposal - Discord LoL Bot

A League of Legends coaching bot on Discord (Embed in another tool) using Python scripts to read champion selection and drafting states from Riot API libraries.

### Past Project Reference

Completely new project with no relevant reference. Have heard and seen some of the API libraries.

[Github URL](https://github.com/xiaojian1202/discord-lol)

### Planned Technologies

- Riot API (most likely Riot League Client Update) to pull live states locally.
- api-gpt-oss-120b for reasoning suggestion generation.
- Discord's built in webhook functions to allow messages and data updates sent to a text channel in a Discord server.
- SQLite database to store matchup statistics from a public [Kaggle datatset](https://www.kaggle.com/datasets/nathansmallcalder/lol-match-history-and-summoner-data-80k-matches).

### First Deliverable

The first deliverable to build is a python script that can run and pull draft states live when I am in the drafting/selection phase of the lobby. The minimum is to keep track of both team's selections and send messages into a desired Discord channel to recommend counter picks based on current board state to account for drafting orders.

### Rough Architecture

- Poll script: python script that checks champion selection states through the Riot Library APIs. Refreshes every 10 seconds (selection time per player is 30 seconds)
- State tracker: Using the polled data, compare against the last update. If different, update it.
- Database query: Extract the enemy champion's name as a string (if applicable because you might be the first pick) and query the SQLite database and retrieve top counters sorted by win rates against the the champion with a minimum game threshold.
- AI Draft: Uses LLM to combine draft state and database query to prompt the LLM to generate a concise a recommendation.
- Discord sender: Convert the LLM response in a structured format (JSON or md) and sends a HTTPS POST request to the Discord text channel via webhook.

### After Deliverables

- Expand into a background app or minialistic UI tool that becomes an overlay during a live game without having a different window open. 
- Expand the pipeline to become dynamic, accounting for damage type balance, win conditions, crowd control, champion archetypes, etc.

