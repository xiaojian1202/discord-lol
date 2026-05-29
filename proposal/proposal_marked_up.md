# Marked Up Proposal: League of Legends Draft Architect

## Planned Technologies

- **Python**: (a) Implemented. Core language for all modules.
- **lcu-driver**: (a) Implemented. Used in `src/lcu/listener.py`.
- **SQLite**: (a) Implemented. Used for storing matchup data in `data/matchups.db`.
- **gpt-oss-120b**: (a) Implemented. Used in `src/ai/client.py` for recommendations.
- **Discord Webhooks**: (a) Implemented. Used in `src/discord/webhook.py`.
- **Pandas**: (a) Implemented. Used for data analysis in `src/scripts/analyze_roles.py`.

## First Deliverable

- **LCU Integration**: (a) Implemented. The app successfully detects champion select sessions.
- **Basic Counter Suggestions**: (a) Implemented. The app queries SQLite for counters and sends them to Discord.

## Rough Architecture for First Deliverable

- **Listener -> Orchestrator -> Database -> Discord**: (a) Implemented. This pipeline is the backbone of the application in `src/main.py`.

## After First Deliverable Goals

- **AI Recommendation Engine**: (a) Implemented to provide nuanced strategic advice.
- **Draft Simulator**: (a) Implemented. Created `src/scripts/sim_draft.py` for local testing.
- **Role Ambiguity Logic**: (a) Implemented. Added data-driven role prediction in `src/scripts/sim_draft.py`.
- **Visual Overlay**: (c) No longer planned. Decided to focus on the Discord/Mobile integration as it is less intrusive and doesn't risk anti-cheat triggers.
- **Ban Recommendations**: (b) Planned. The architecture supports this, but the AI prompt needs refinement to prioritize bans specifically.

