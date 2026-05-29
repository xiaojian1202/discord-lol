# Transcript 1: Researching and Implementing the LCU Listener

**User:** i want to build a tool that can see what's happening in my League of Legends champion select in real-time. is that even possible?

**Agent:** Yes, it is. The League of Legends client has a local API called the LCU (League Client Update). We can use a library called `lcu-driver` to connect to it via WebSockets and listen for session updates.

**User:** okay, lets do that. how do we know which event to listen for?

**Agent:** We'll target the `/lol-champ-select/v1/session` endpoint. This gives us a JSON object every time a player picks, bans, or hovers a champion. I'll start by researching the data structure of that session object.

**User:** great. once we have the data, i want to send it to discord so i can see it on my phone while i'm playing.

**Agent:** That's a smart design choice. It avoids having to build an overlay that might trigger anti-cheat software. I'll implement a `LCUListener` class that parses the session data and passes it to an orchestrator to handle the Discord notification.
