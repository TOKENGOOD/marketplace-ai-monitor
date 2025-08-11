# FB Marketplace Monitor — Web Admin (Profiles on a Website)

This version adds a **web UI** to create/edit/delete filters ("profiles") without touching files.

- Backend: FastAPI + SQLite
- Frontend: simple HTML/JS served by FastAPI
- Notifications: Telegram (per profile or global)
- Data: still mock listings for now (so you can test everything safely)

## Quick Start
1) Install Python 3.10+
2) In Command Prompt:
```
cd fb-marketplace-starter-web
python -m venv .venv
.venv\Scripts\activate
pip install -r backend\requirements.txt
copy backend\.env.example backend\.env
```
3) Edit `backend\.env` → set `TELEGRAM_BOT_TOKEN` (and optional global `TELEGRAM_CHAT_ID`).
4) Run the server:
```
cd backend
uvicorn app:app --reload --port 8000
```
5) Open http://127.0.0.1:8000/ — use **Profiles** tab to add your filters.
6) In a new terminal (with venv activated), run the worker to send mock alerts:
```
cd backend
python worker.py
```
You’ll see notifications per the profiles you created in the web UI.

## Next steps later
- Replace the mock scraper with Playwright
- Add AI filtering
- Deploy to a host (Render/Railway) and keep the same web admin
