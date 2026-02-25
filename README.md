# Torn Investment Tracker

Real-time investment dashboard for Torn using the official API.

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Set your API key (NEVER hardcode it)
```bash
# Linux / macOS
export TORN_API_KEY=your_16char_key_here

# Windows (PowerShell)
$env:TORN_API_KEY="your_16char_key_here"

# Windows (cmd)
set TORN_API_KEY=your_16char_key_here
```

### 3. Run the server
```bash
python app.py
```

### 4. Open the dashboard
Visit: http://localhost:5000

---

## How it works
- The **API key lives only on the server** — it's never sent to the browser
- The backend fetches investment data and caches it for 60 seconds to respect Torn's rate limits (max 100 req/min)
- The frontend polls `/api/investments` (the local server), not Torn directly
- Auto-refreshes every 60 seconds with a live countdown timer
- Displays maturity countdown per investment

## API ToS Disclosure
| | |
|---|---|
| **Data Storage** | Not stored / temporary in-memory cache only |
| **Data Sharing** | Nobody |
| **Purpose** | Personal portfolio tracking |
| **Key Storage** | Stored as environment variable / not shared |
| **Access Level** | Limited — `investments` selection only |

## Optional: Keep running with a process manager
```bash
# Install pm2 (node) or use screen/tmux
screen -S torn python app.py
```

## Optional: .env file support
Install `python-dotenv`, create a `.env` file:
```
TORN_API_KEY=your_key_here
```
Then add to the top of `app.py`:
```python
from dotenv import load_dotenv
load_dotenv()
```
