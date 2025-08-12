from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import os
from db import init_db, list_profiles, get_profile, create_profile, update_profile, delete_profile, list_listings, get_listing
from job_runner import run_once

app = FastAPI(title="DealAI — Marketplace Monitor")
static_dir = Path(__file__).parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=static_dir, html=True), name="static")

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/", response_class=HTMLResponse)
def index():
    return FileResponse(static_dir / "index.html")

# Profiles API
@app.get("/api/profiles")
def api_list_profiles():
    return list_profiles()

@app.post("/api/profiles")
async def api_create_profile(request: Request):
    data = await request.json()
    print("--- RECEIVED DATA ---")
    import json
    print(json.dumps(data, indent=2))
    print("---------------------")
    if not data.get("name"):
        raise HTTPException(400, "name is required")
    pid = create_profile(data)
    return {"id": pid}

@app.put("/api/profiles/{pid}")
async def api_update_profile(pid: int, request: Request):
    data = await request.json()
    if not data.get("name"):
        raise HTTPException(400, "name is required")
    if not get_profile(pid):
        raise HTTPException(404, "profile not found")
    update_profile(pid, data)
    return {"ok": True}

@app.delete("/api/profiles/{pid}")
def api_delete_profile(pid: int):
    if not get_profile(pid):
        raise HTTPException(404, "profile not found")
    delete_profile(pid)
    return {"ok": True}

# Listings API
@app.get("/api/listings")
def api_list_listings(
    min_score: float = Query(0.0, ge=0.0, le=1.0),
    profile: str | None = None,
    status: str | None = None,
    security_min: int | None = None
):
    return list_listings(min_score=min_score, profile=profile, status=status, security_min=security_min)

# Per-item page
DETAIL_TEMPLATE = """<!doctype html>
<html><head><meta charset='utf-8'/><meta name='viewport' content='width=device-width, initial-scale=1'/>
<title>{title}</title></head>
<body style='font-family:system-ui,Arial;margin:20px'>
<h1 style='margin:0 0 8px 0'>{title}</h1>
<div style='color:#475569;margin-bottom:10px;'>£{price} • {profile} • score {score:.2f}</div>
<div style='margin-bottom:10px;'>Security: {sec}/100 — {tag}</div>
<p style='color:#334155'>{reason}</p>
<p><a href='{url}' target='_blank' rel='noopener'>Open on Facebook</a></p>
<p><a href='/'>← Back to results</a></p>
</body></html>"""

def _tag_for(sec:int):
    if sec >= 96: return "Safe"
    if sec >= 86: return "Low risk"
    if sec >= 70: return "Scam alert"
    return "Rejected"

@app.get("/item/{item_id}", response_class=HTMLResponse)
def item_page(item_id: int):
    row = get_listing(item_id)
    if not row:
        raise HTTPException(404, "Not found")
    html = DETAIL_TEMPLATE.format(
        title=row.get("title","Item"),
        price=(row.get("price_cents") or 0)/100,
        profile=row.get("profile",""),
        score=float(row.get("score") or 0.0),
        sec=int(row.get("security_score") or 0),
        url=row.get("url","#"),
        reason=row.get("ai_reasons") or row.get("reason") or "",
        tag=_tag_for(int(row.get("security_score") or 0))
    )
    return HTMLResponse(content=html)

# ---- HTTP trigger for worker ----
@app.post("/run-worker")
def run_worker(token: str):
    if token != os.getenv("TRIGGER_SECRET"):
        raise HTTPException(401, "invalid token")
    result = run_once()
    return JSONResponse(result)
