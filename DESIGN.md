# Design Decisions: League of Legends Draft Architect

This document tracks three pivotal design decisions made during the development of the Draft Architect, detailing the rationale and impact of each choice.

## 1. Discord Webhook Integration vs. Local UI Overlay

**Context:** Initially, the plan was to build a minimalistic UI overlay that would appear directly over the League of Legends client during Champion Select.

**Decision:** Pivoted to a **Discord Webhook** notification system. 

- **Rationale:** 
  - **Anti-Cheat Safety:** Modern anti-cheat systems (like Vanguard) are highly sensitive to external overlays and memory hooks. Using an external communication channel (Discord) completely bypasses the risk of triggering false positives or bans. Overlays would likely require an official API key from Riot Games for developers.
  - **Cross-Device Accessibility:** Recommendations sent to Discord can be viewed on a second monitor, a tablet, or a mobile phone, providing more screen real estate than a crowded game client overlay.
  - **Ease of Development:** Leveraging Discord's built-in webhook functionality allowed us to focus on the AI recommendation engine rather than UI/UX rendering logic.

## 2. Tournament Draft Simulator for Development & Testing

**Context:** Testing the app in real-time was difficult because League's "Custom Game" bots pick champions instantly, making it impossible to test the app's response to individual pick events without going into an actual game which would be time consuming.

**Decision:** We implemented a comprehensive **Draft Simulator** (`src/scripts/sim_draft.py`) that mimics the LCU's WebSocket events.

- **Rationale:** 
  - **Controlled Testing:** The simulator follows the exact B1-R1-B2 pick sequence, allowing us to verify the AI's recommendations at every phase.
  - **Offline Development:** Developers can iterate on the AI prompt and recommendation logic without having the League client open or being in a game.
  - **Role Ambiguity Simulation:** We added a mode to simulate unknown enemy roles, which is critical for testing the robustness of our pick suggestions.

## 3. Data-Driven Role Ambiguity Prediction

**Context:** Identifying which lane an enemy champion is going to is critical for counter-picking. Initially, we used a static dictionary of champions and their primary roles.

**Decision:** We transitioned to an **Empirical Role Analysis** system (`src/scripts/analyze_roles.py`).

- **Rationale:** 
  - **Accuracy:** By analyzing 80k matches from the Kaggle dataset, we identified "flex-picks" (champions played in multiple roles) based on real player behavior rather than static definitions.
  - **Threshold-Based Logic:** We only classify a champion as a flex-pick if their secondary role meets a 15% frequency threshold in the data, reducing noise from rare picks.
  - **Dynamic Adaptation:** If the meta shifts (e.g., a champion moves from Support to Mid), re-running the analysis script automatically updates the simulator's logic without manual code changes.

