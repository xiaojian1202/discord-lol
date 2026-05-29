# Transcript 2: Solving the Testing Bottleneck with the Draft Simulator

**User:** i have a problem right now. i want to test the app locally on the game client with a custom game but the bots choose champions before starting the game. are there any alternatives to testing the app in the game client without starting a real game?

**Agent:** Custom game bots are indeed too fast for testing pick-by-pick logic. The best alternative is to build a Draft Simulator that mimics the LCU's behavior. We can write a script that follows the standard tournament draft order and "feeds" the Orchestrator fake session data.

**User:** lets refine the sim_draft.py to add an optional mode to include bans for users who want to experience bans. what are some other scenarios that you suggest?

**Agent:** I've added the ban phase (B1-R1-B2-R2-B3-R3 sequence). For other scenarios, I suggest adding "Role Ambiguity." In a real draft, you don't always know where the enemy is going. We could make the simulator hide enemy lanes to see if our AI can still give good advice.

**User:** that sounds perfect. lets make the simulator more realistic by hiding the enemy paths.
