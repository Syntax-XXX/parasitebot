# ParasiteBot 🦠

> **AI-powered Personality Parasite Bot for Discord**  
> Clone, mimic, and interact with AI-generated versions of users — with explicit consent and style tuning!

---

## info

the bot will work only when he reached the message limit and then tried to clone the person. he more messages the more accurate it can get

the bot needs permission to:
Read Message Log in the channel
To Create Webhooks
And Send messages

## Overview

ParasiteBot is a Discord bot that uses advanced AI (via Groq/OpenAI APIs) to clone users' personalities based on their message history — but only after users explicitly consent. Users can customize the style of their AI clone’s responses, control consent, and explore an infection chain that traces who cloned whom.

This bot emphasizes **privacy** by storing all user data locally, deleting messages from non-consenting users, and providing full user control over their data and clone style.

---

## Features

- **User Consent Management**  
  Users must explicitly accept before their messages are recorded and used for AI cloning.

- **Clone Style Tuner**  
  Choose from different clone communication styles:  
  - `default`  
  - `formal`  
  - `meme`  
  - `toxic`  
  - `uwu`

- **AI-Generated Clone Replies**  
  The bot replies impersonating the user in their chosen style when mentioned.

- **Infection Chain Visualization**  
  Trace the chain of clones showing who cloned whom.

- **Server Status Command**  
  View system health stats (CPU, memory, disk usage, uptime).

- **Consent Revocation**  
  Users can revoke consent anytime to stop data collection.

---

## Commands

| Command             | Description                                                    |
|---------------------|----------------------------------------------------------------|
| `clone!help`        | Show this help menu with all available commands                |
| `clone!style [type]`| Change your clone’s speaking style (`default`, `formal`, `meme`, `toxic`, `uwu`) |
| `clone!consent`     | Give consent to use your messages for AI cloning               |
| `clone!revoke`      | Revoke your consent and stop data collection                   |
| `clone!infect-chain`| Show the infection chain of clones                              |
| `clone!serv-status` | Show current server and system statistics                       |
| `clone!status`      | Show your active clone style and consent status                |
| `clone!creator`     | Display info about the bot creator (Syntax-XXX)                |

---

## Installation

### Requirements

- Python 3.10+  
### Setup

1. Clone this repository:

```bash
git clone https://github.com/yourusername/ParasiteBot.git
cd ParasiteBot
Create and activate a Python virtual environment (recommended):
```
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```
2. Install dependencies:

```bash
pip install -r requirements.txt
Create a .env file in the project root and add your keys:
```

3. Run the bot:

```bash
python main.py
```

---

Usage
Invite the bot to your Discord server with permissions to read/send messages and manage webhooks.

Users must allow their messages to be logged for AI cloning.

Change your clone style with clone!style [style].

Mention the bot or interact to get AI-generated replies mimicking consenting users.

Use clone!infect-chain to view who cloned whom in your server.

Data & Privacy
All user message data is stored locally in a JSON file (clones.json).

No data is shared externally.

Messages from users without consent are deleted automatically.

Users can revoke consent anytime to stop data collection and AI cloning.

Contributing
Contributions, bug reports, and feature requests are welcome!
Please open issues or pull requests on GitHub.

License
MIT License

Contact
Created and maintained by Syntax-XXX
Find me on Discord or GitHub
