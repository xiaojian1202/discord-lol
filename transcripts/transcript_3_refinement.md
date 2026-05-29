# Transcript 3: Implementing Data-Driven Role Ambiguity Logic

**User:** add the logic for deciding role ambiguity (figure out what lane a potential selection from the opposing team might be). This means you wont know what lanes the opposing picks will be representing and you only know about your team's lanes.

**Agent:** To do this accurately, I'll need to implement a prediction algorithm. I can use the 80k match dataset to see where champions are most commonly played. For example, if we see a Nautilus, he could be Support, Jungle, or Mid.

**User:** for flex champions, restrict the dictionary to the two most common lanes. and how do you determine flex champions for what lanes? if you use the csv files, only include secondary roles if it meets a minimum threshold of matches.

**Agent:** Understood. I'll write an analysis script that calculates the pick-rate percentage for every role per champion. I'll set a 15% threshold; if a secondary role appears less than that, we'll ignore it to avoid "troll" picks.

**User:** i realize users might not have the dataset locally, so make sure the tool can still run if the raw csv files are missing.

**Agent:** I'll have the analysis script output a `role_data.json` file. We'll include this pre-processed file in the repo so users get the benefit of the data analysis without needing to download 1GB of raw CSVs.
