# Stock Ticker Backend

Modular Python backend for an online Stock Ticker game with a React browser client.

## Features

- FastAPI backend (HTTP/HTTPS)
- DuckDB persistence
- Auto-reset persistence on backend startup (all prior games are cleared)
- Multiple concurrent games via generated `game_code`
- Lobby flow with owner-controlled game start
- Round-based progression with per-round roll count
- Player done-tracking before ticker rolls execute
- Board-game aligned ticker dice logic (stock/action/amount via 3d6 mapping)
- BUY orders fixed to 500 shares and all stocks start at $1
- Standings + winner calculation at game end

## Run Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -e .
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

HTTPS backend (TLS cert + key):

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --ssl-certfile path\to\cert.pem --ssl-keyfile path\to\key.pem
```

## CORS Origin Whitelist

Backend CORS is restricted to an origin whitelist.

- Environment variable: `CORS_ALLOWED_ORIGINS`
- Format: comma-separated origins
- Example:

```bash
set CORS_ALLOWED_ORIGINS=http://localhost:5173,http://192.168.1.50:5173
```

If not set, defaults are:

- `http://localhost:5173`
- `https://localhost:5173`
- `http://127.0.0.1:5173`
- `https://127.0.0.1:5173`

## API

- `POST /games` create game (owner name, rounds, rolls)
- `POST /games/join` join game by code + player name
- `GET /games/{game_id}` fetch full game view
- `GET /games/code/{game_code}` fetch game by code
- `POST /games/{game_id}/start` owner starts game
- `POST /games/{game_id}/trades` submit BUY/SELL trade
- `POST /games/{game_id}/done` player marks "All Done"
- `POST /games/{game_id}/close` owner closes game

## Frontend

```bash
cd frontend
copy .env.example .env
npm install
npm run dev
```

Default frontend API target: current browser origin (or `VITE_API_BASE` if set).
