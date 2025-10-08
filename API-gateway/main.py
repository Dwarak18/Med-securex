import os
import sys
import json
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from collections import defaultdict, deque

import uvicorn
import httpx
from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware

from owasp_rules import OWASP_RULES
from regex_rules import check_regex_rules, detect_email

# --- Database-backed incident/request logger ---
from incident_logger import (
    setup_database,
    log_request,
    log_incident,
    get_incidents,
    mark_incident_handled,
    get_api_usage
)

# --- In-memory API usage stats (for React charts) ---
API_USAGE_STATS = {
    "total_requests": deque(maxlen=3600),
    "successful_requests": deque(maxlen=3600),
    "blocked_requests": deque(maxlen=3600),
    "timestamps": deque(maxlen=3600)
}

CLIENT_TIMEOUT = httpx.Timeout(10.0, connect=5.0)
ADMIN_KEY = "supersecretadminkey"

app = FastAPI(title="Merged API Gateway + Med-securex Backend")
logging.basicConfig(level=logging.INFO)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

# Startup / shutdown for database
@app.on_event("startup")
async def on_startup():
    setup_database()
    logging.info("✅ MongoDB logger initialized.")

@app.on_event("shutdown")
async def on_shutdown():
    logging.info("🔌 MongoDB logger shutdown.")

def admin_auth(key: str):
    if key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True

def log_api_usage(status: str):
    """In-memory API usage logging for charts."""
    now = datetime.utcnow()
    API_USAGE_STATS["timestamps"].append(now)
    API_USAGE_STATS["total_requests"].append(1)
    if status == "success":
        API_USAGE_STATS["successful_requests"].append(1)
        API_USAGE_STATS["blocked_requests"].append(0)
    elif status == "blocked":
        API_USAGE_STATS["successful_requests"].append(0)
        API_USAGE_STATS["blocked_requests"].append(1)
    else:
        API_USAGE_STATS["successful_requests"].append(0)
        API_USAGE_STATS["blocked_requests"].append(0)

# Multi-backend proxy map
APP_BACKEND_URL = os.getenv("APP_BACKEND_URL", "http://127.0.0.1:9001")
SECURITY_BACKEND_URL = os.getenv("SECURITY_BACKEND_URL", "http://127.0.0.1:9000")
ROUTE_MAP = {
    "/auth": APP_BACKEND_URL,
    "/users": APP_BACKEND_URL,
    "/orders": APP_BACKEND_URL,
    "/api": APP_BACKEND_URL,
}
DEFAULT_BACKEND = SECURITY_BACKEND_URL

def resolve_backend(path: str) -> str:
    prefixes = sorted(ROUTE_MAP.keys(), key=len, reverse=True)
    for p in prefixes:
        if path.startswith(p):
            return ROUTE_MAP[p]
    return DEFAULT_BACKEND

# --- Suricata eve.json tailing ---
SURICATA_PATHS = [
    "/opt/homebrew/var/log/suricata/eve.json",
    "/var/log/suricata/eve.json",
    "/var/log/suricata/eve/eve.json"
]
def find_eve_path():
    for p in SURICATA_PATHS:
        if os.path.exists(p):
            return p
    return None
EVE_PATH = find_eve_path()

def tail_lines(path: str, n: int = 1000):
    avg_line_size = 400
    to_read = n * avg_line_size
    try:
        with open(path, "rb") as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            start = max(0, size - to_read)
            f.seek(start)
            data = f.read().decode("utf-8", errors="ignore")
            lines = data.splitlines()
            if start > 0 and lines:
                lines = lines[1:]
            return lines[-n:]
    except Exception:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            all_lines = f.readlines()
            return [l.rstrip("\n") for l in all_lines[-n:]]

def compact_alert_from_eve(obj: dict):
    if obj.get("event_type") != "alert":
        return None
    alert = obj.get("alert", {})
    return {
        "timestamp": obj.get("timestamp"),
        "event_type": "alert",
        "src_ip": obj.get("src_ip") or obj.get("source_ip") or obj.get("src_addr"),
        "src_port": obj.get("src_port") or obj.get("source_port"),
        "dest_ip": obj.get("dest_ip") or obj.get("destination_ip") or obj.get("dst_addr"),
        "dest_port": obj.get("dest_port") or obj.get("destination_port"),
        "proto": obj.get("proto"),
        "alert": {
            "action": alert.get("action"),
            "signature": alert.get("signature"),
            "category": alert.get("category"),
            "severity": alert.get("severity"),
            "signature_id": alert.get("signature_id")
        }
    }

# --- Admin: Suricata alerts ---
@app.get("/admin/suricata-alerts")
def get_suricata_alerts(
    key: str,
    limit: int = Query(50, ge=1, le=500),
    since: str = Query(None)
):
    admin_auth(key)
    if EVE_PATH is None:
        raise HTTPException(500, "Suricata eve.json not found")
    since_dt = None
    if since:
        try:
            since_dt = datetime.fromisoformat(since).replace(tzinfo=timezone.utc)
        except:
            raise HTTPException(400, "Invalid 'since' timestamp")
    lines = tail_lines(EVE_PATH, max(limit*6, 500))
    alerts = []
    for line in reversed(lines):
        if not line.strip(): continue
        try:
            obj = json.loads(line)
        except:
            continue
        if obj.get("event_type") != "alert":
            continue
        if since_dt:
            ts = obj.get("timestamp")
            try:
                ts_dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except:
                continue
            if ts_dt <= since_dt:
                continue
        compact = compact_alert_from_eve(obj)
        if compact:
            alerts.append(compact)
            if len(alerts) >= limit:
                break
    return {"path": EVE_PATH, "count": len(alerts), "alerts": alerts}

# --- Payload inspection middleware ---
@app.middleware("http")
async def payload_inspect(request: Request, call_next):
    body = b""
    try:
        body = await request.body()
    except:
        pass
    try:
        text = body.decode("utf-8", errors="ignore")
    except:
        text = ""
    qs = request.url.query or ""
    full_payload = text + ("?"+qs if qs else "")
    client_ip = getattr(getattr(request, "client", None), "host", None) or "unknown"

    # OWASP
    for name, fn in OWASP_RULES.items():
        try:
            if fn(full_payload):
                await log_incident(client_ip, full_payload, name)
                log_api_usage("blocked")
            return JSONResponse(content={"detail": f"Blocked by OWASP rule: {name}"}, status_code=403)
        except:
            logging.exception("OWASP rule error")

    # Regex
    try:
        triggered = check_regex_rules(full_payload)
    except:
        triggered = []
    if triggered:
        for r in triggered:
            await log_incident(client_ip, full_payload, r)
        log_api_usage("blocked")
        return JSONResponse(content={"detail": f"Blocked by Regex rule(s): {', '.join(triggered)}"}, status_code=403)

    # RAG integration
    rag_url = f"{os.getenv('RAG_SERVICE_URL','http://localhost:8000')}/check_payload"
    try:
        async with httpx.AsyncClient(timeout=CLIENT_TIMEOUT) as rag_client:
            resp = await rag_client.post(rag_url, json={"payload": full_payload})
            if resp.status_code == 200 and resp.content:
                data = resp.json()
                verdict = data.get("verdict","unknown")
                score = data.get("confidence_score",0)
            else:
                verdict, score = "unknown", 0
    except:
        verdict, score = "unknown", 0

    if verdict == "malicious":
        await log_incident(client_ip, full_payload, "RAG-malicious")
        log_api_usage("blocked")
        raise HTTPException(403, "Blocked by RAG verdict: malicious")
    if verdict == "unknown":
        await log_incident(client_ip, full_payload, "RAG-unknown")
        log_api_usage("error")
        raise HTTPException(503, "RAG service unavailable")

    # Forward to backend
    backend_base = resolve_backend(request.url.path)
    target = backend_base.rstrip("/") + request.url.path
    if request.url.query:
        target += "?" + request.url.query
    headers = dict(request.headers)
    headers.pop("host", None)

    try:
        async with httpx.AsyncClient(timeout=CLIENT_TIMEOUT) as client:
            resp = await client.request(
                method=request.method,
                url=target,
                headers=headers,
                content=body
            )
    except:
        await log_request(status='error', client_ip=client_ip)
        log_api_usage("error")
        return JSONResponse(content={"detail":"Bad Gateway"}, status_code=502)
    # success
    await log_request(status='success', client_ip=client_ip)
    log_api_usage("success")

    ct = resp.headers.get("content-type","application/json")
    if "application/json" in ct:
        return JSONResponse(content=resp.json(), status_code=resp.status_code)
    return Response(resp.content, status_code=resp.status_code, media_type=ct)

# --- Admin incidents endpoints (DB) ---
@app.get("/admin/incidents")
async def admin_list(key: str):
    admin_auth(key)
    return await get_incidents()

@app.post("/admin/incidents/{incident_id}/handle")
async def admin_handle(incident_id: int, key: str):
    admin_auth(key)
    if await mark_incident_handled(incident_id):
        return {"message": f"Incident {incident_id} marked handled"}
    raise HTTPException(404, "Incident not found")

# --- API Usage & Blocked Requests endpoints ---
@app.get("/api/api-usage")
async def api_usage_endpoint():
    # Return DB-based usage for chart 1
    return await get_api_usage()

@app.get("/api/blocked-requests")
async def blocked_requests_endpoint():
    # Return in-memory usage buckets
    buckets = defaultdict(int)
    for ts, err in zip(API_USAGE_STATS["timestamps"], API_USAGE_STATS["blocked_requests"]):
        hour_min = ts.strftime("%H:%M")
        buckets[hour_min] += err
    return [{"time": t, "blocked": c} for t, c in sorted(buckets.items())]

# --- TTP endpoints ---
@app.get("/api/ttps")
async def get_ttps():
    # Proxy to RAG threat_statistics endpoint...
    try:
        async with httpx.AsyncClient(timeout=CLIENT_TIMEOUT) as client:
            resp = await client.get(f"{os.getenv('RAG_SERVICE_URL','http://localhost:8000')}/threat_statistics?hours=168")
            if resp.status_code != 200 or resp.json().get("status") != "success":
                return []
            # If transform_threats_to_ttps is not available, just return the data
            return resp.json().get("data", {})
    except:
        return []

@app.get("/api/ttps/bubbles")
async def get_ttps_bubbles():
    data = await get_ttps()
    # Group logic here...
    # (reuse bubble grouping from API-gateway code)

# --- Health ---
@app.get("/health")
async def health():
    return {"status":"healthy","service":"merged","version":"1.0.0"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)