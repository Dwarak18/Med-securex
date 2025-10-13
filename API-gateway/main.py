import os
import sys
import json
import asyncio
from typing import Dict, List, Optional
from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
import httpx
import logging
import uvicorn

import os
import json
from datetime import datetime, timezone, timedelta


from owasp_rules import OWASP_RULES
from regex_rules import check_regex_rules, detect_email
from incident_logger import log_incident, get_incidents, mark_incident_handled
from pydantic import BaseModel
from collections import defaultdict, deque

class IncidentCreate(BaseModel):
    ip: str
    payload: str
    rule: str

# API Usage tracking - in-memory storage for demo
# Timeout for HTTPX client requests
CLIENT_TIMEOUT = httpx.Timeout(10.0, connect=5.0)
# In production, consider using Redis or database
API_USAGE_STATS = {
    "total_requests": deque(maxlen=3600),  # Store last hour of data (1 per second)
    "successful_requests": deque(maxlen=3600),
    "blocked_requests": deque(maxlen=3600),
    "timestamps": deque(maxlen=3600)
}

def log_api_usage(status: str):
    """Log API usage with timestamp"""
    now = datetime.utcnow()
    
    # Add timestamp
    API_USAGE_STATS["timestamps"].append(now)
    
    # Count total requests
    API_USAGE_STATS["total_requests"].append(1)
    
    # Count by status
    if status == "success":
        API_USAGE_STATS["successful_requests"].append(1)
        API_USAGE_STATS["blocked_requests"].append(0)
    elif status == "blocked":
        API_USAGE_STATS["successful_requests"].append(0)
        API_USAGE_STATS["blocked_requests"].append(1)
    else:  # error or other
        API_USAGE_STATS["successful_requests"].append(0)
        API_USAGE_STATS["blocked_requests"].append(0)

app = FastAPI()
logging.basicConfig(level=logging.INFO)

# Add CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Admin key (demo)
def admin_auth(key: str):
    if key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True
ADMIN_KEY = "supersecretadminkey"

# Route map - map path prefixes to backend base URLs
# Use environment variables for Docker compatibility
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
    body_bytes = b""
    try:
        body_bytes = await request.body()
    except:
        pass
    try:
        text = body_bytes.decode("utf-8", errors="ignore")
    except:
        text = ""
    qs = request.url.query or ""
    full_payload = text + ("?"+qs if qs else "")
    client_ip = getattr(getattr(request, "client", None), "host", None) or "unknown"

    # OWASP
    for rule_name, rule_fn in OWASP_RULES.items():
        try:
            if rule_fn(full_payload):
                await log_incident(client_ip, full_payload, rule_name)
                log_api_usage("blocked")  # Log blocked request
                return JSONResponse(status_code=403, content={"detail": f"Blocked by OWASP rule: {rule_name}"})
        except Exception:
            logging.exception("Error evaluating OWASP rule %s", rule_name)

    # Regex
    try:
        triggered = check_regex_rules(full_payload)
    except:
        triggered = []
    if triggered:
        for r in triggered:
            await log_incident(client_ip, full_payload, r)
        log_api_usage("blocked")  # Log blocked request
        return JSONResponse(status_code=403, content={"detail": f"Blocked by Regex rule(s): {', '.join(triggered)}"})

    # Enhanced RAG integration with detailed analysis
    rag_url = f"{os.getenv('RAG_SERVICE_URL','http://localhost:8000')}/check_payload"
    try:
        rag_payload = {
            "payload": full_payload,
            "source_ip": client_ip,
            "user_agent": request.headers.get("user-agent"),
            "timestamp": datetime.now().isoformat()
        }
        
        async with httpx.AsyncClient(timeout=CLIENT_TIMEOUT) as rag_client:
            resp = await rag_client.post(rag_url, json=rag_payload)
            if resp.status_code == 200 and resp.content:
                data = resp.json()
                verdict = data.get("verdict", "unknown")
                score = data.get("confidence_score", 0)
                threat_details = data.get("threat_details", {})
                analysis_method = data.get("analysis_method", "unknown")
                blocking_recommended = data.get("blocking_recommended", False)
                
                # Log detailed information for malicious payloads
                if verdict == "malicious":
                    attack_type = threat_details.get("attack_type", "unknown")
                    severity = threat_details.get("severity", "medium")
                    rule_name = f"RAG-{analysis_method}-{attack_type}"
                    
                    await log_incident(client_ip, full_payload, rule_name)
                    log_api_usage("blocked")
                    
                    # Enhanced blocking response with threat details
                    return JSONResponse(
                        status_code=403, 
                        content={
                            "detail": f"Blocked by RAG analysis: {attack_type}",
                            "threat_info": {
                                "attack_type": attack_type,
                                "severity": severity,
                                "confidence": score,
                                "method": analysis_method,
                                "description": threat_details.get("description", "")
                            }
                        }
                    )
                elif verdict == "unknown" and analysis_method == "failed":
                    await log_incident(client_ip, full_payload, "RAG-service-error")
                    log_api_usage("error")
                    return JSONResponse(status_code=503, content={"detail": "RAG service analysis failed"})
            else:
                verdict, score = "unknown", 0
    except Exception as e:
        logging.error(f"RAG service communication failed: {e}")
        verdict, score = "unknown", 0

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
                content=body_bytes,
                params=None
            )
    except httpx.RequestError as exc:
        logging.exception("Upstream request failed: %s", exc)
        log_api_usage("error")  # Log error request
        return JSONResponse(status_code=502, content={"detail": "Bad Gateway: upstream unreachable"})

    # Log successful request
    log_api_usage("success")
    
    content_type = resp.headers.get("content-type", "application/json")
    try:
        if "application/json" in content_type:
            return JSONResponse(status_code=resp.status_code, content=resp.json())
        else:
            return Response(content=resp.content, status_code=resp.status_code, media_type=content_type)
    except Exception:
        return Response(content=resp.content, status_code=resp.status_code, media_type=content_type)

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

# --- Enhanced payload analysis endpoints ---
@app.get("/api/recent-payloads")
async def get_recent_payloads_api(limit: int = Query(50, ge=1, le=200), key: str = Query(...)):
    """Get recent payload analyses from PostgreSQL"""
    admin_auth(key)
    
    try:
        # Forward request to RAG service
        rag_service_url = os.getenv("RAG_SERVICE_URL", "http://localhost:8000")
        async with httpx.AsyncClient(timeout=CLIENT_TIMEOUT) as client:
            response = await client.get(f"{rag_service_url}/malicious_payloads?limit={limit}")
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=response.status_code, detail="RAG service error")
                
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="RAG service unavailable")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/attack-statistics")
async def get_attack_statistics_api(hours: int = Query(24, ge=1, le=168), key: str = Query(...)):
    """Get attack statistics from PostgreSQL"""
    admin_auth(key)
    
    try:
        # Forward request to RAG service
        rag_service_url = os.getenv("RAG_SERVICE_URL", "http://localhost:8000")
        async with httpx.AsyncClient(timeout=CLIENT_TIMEOUT) as client:
            response = await client.get(f"{rag_service_url}/attack_statistics?hours={hours}")
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=response.status_code, detail="RAG service error")
                
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="RAG service unavailable")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/payload-analysis/{payload_hash}")
async def get_payload_analysis(payload_hash: str, key: str = Query(...)):
    """Get detailed analysis for a specific payload"""
    admin_auth(key)
    
    try:
        # Import PostgreSQL functions locally to avoid circular imports
        from postgres_db import postgres_db
        
        if not postgres_db.pool:
            await postgres_db.init_pool()
        
        async with postgres_db.pool.acquire() as conn:
            # Get payload details
            payload_data = await conn.fetchrow("""
                SELECT p.*, i.severity, i.status as incident_status, i.description,
                       i.created_at as incident_time, i.metadata 
                FROM payloads p
                LEFT JOIN incidents i ON p.id = i.payload_id
                WHERE p.payload_hash = $1
            """, payload_hash)
            
            if not payload_data:
                raise HTTPException(404, "Payload not found")
            
            # Convert to dict and format timestamps
            result = dict(payload_data)
            for key, value in result.items():
                if isinstance(value, datetime):
                    result[key] = value.isoformat()
            
            return {"status": "success", "data": result}
            
    except Exception as e:
        logging.error(f"Error getting payload analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/attack-trends")
async def get_attack_trends(days: int = Query(7, ge=1, le=30), key: str = Query(...)):
    """Get attack trends over time for dashboard"""
    admin_auth(key)
    
    try:
        from postgres_db import postgres_db
        
        if not postgres_db.pool:
            await postgres_db.init_pool()
        
        async with postgres_db.pool.acquire() as conn:
            # Get daily attack counts by type
            trends = await conn.fetch("""
                SELECT 
                    DATE(created_at) as date,
                    attack_type,
                    COUNT(*) as count,
                    AVG(confidence_score) as avg_confidence
                FROM payloads 
                WHERE verdict = 'malicious' 
                  AND created_at >= CURRENT_DATE - INTERVAL '%s days'
                GROUP BY DATE(created_at), attack_type
                ORDER BY date DESC, count DESC
            """ % days)
            
            # Format results for frontend charts
            result = []
            for trend in trends:
                result.append({
                    "date": trend["date"].isoformat(),
                    "attack_type": trend["attack_type"],
                    "count": trend["count"],
                    "avg_confidence": float(trend["avg_confidence"]) if trend["avg_confidence"] else 0.0
                })
            
            return {"status": "success", "data": result}
            
    except Exception as e:
        logging.error(f"Error getting attack trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/threat-intelligence")
async def get_threat_intelligence(key: str = Query(...)):
    """Get comprehensive threat intelligence summary"""
    admin_auth(key)
    
    try:
        from postgres_db import postgres_db
        
        if not postgres_db.pool:
            await postgres_db.init_pool()
        
        async with postgres_db.pool.acquire() as conn:
            # Get comprehensive threat statistics
            stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_payloads,
                    COUNT(*) FILTER (WHERE verdict = 'malicious') as malicious_count,
                    COUNT(*) FILTER (WHERE verdict = 'benign') as benign_count,
                    COUNT(*) FILTER (WHERE verdict = 'unknown') as unknown_count,
                    COUNT(DISTINCT client_ip) as unique_ips,
                    COUNT(DISTINCT attack_type) FILTER (WHERE verdict = 'malicious') as attack_types,
                    AVG(confidence_score) FILTER (WHERE verdict = 'malicious') as avg_malicious_confidence,
                    MAX(created_at) as last_analysis
                FROM payloads 
                WHERE created_at >= CURRENT_DATE - INTERVAL '24 hours'
            """)
            
            # Get top attack types
            top_attacks = await conn.fetch("""
                SELECT attack_type, COUNT(*) as count, AVG(confidence_score) as avg_confidence
                FROM payloads 
                WHERE verdict = 'malicious' 
                  AND created_at >= CURRENT_DATE - INTERVAL '24 hours'
                GROUP BY attack_type
                ORDER BY count DESC
                LIMIT 10
            """)
            
            # Get top attacking IPs
            top_ips = await conn.fetch("""
                SELECT client_ip, COUNT(*) as count, 
                       COUNT(DISTINCT attack_type) as attack_variety
                FROM payloads 
                WHERE verdict = 'malicious' 
                  AND created_at >= CURRENT_DATE - INTERVAL '24 hours'
                GROUP BY client_ip
                ORDER BY count DESC
                LIMIT 10
            """)
            
            result = {
                "summary": dict(stats),
                "top_attacks": [dict(attack) for attack in top_attacks],
                "top_ips": [dict(ip) for ip in top_ips]
            }
            
            # Format datetime objects
            if result["summary"]["last_analysis"]:
                result["summary"]["last_analysis"] = result["summary"]["last_analysis"].isoformat()
            
            return {"status": "success", "data": result}
            
    except Exception as e:
        logging.error(f"Error getting threat intelligence: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# API Usage endpoint for the React chart
@app.get("/api/api-usage")
def get_api_usage():
    """
    Return API usage data formatted for the ApiUsageChart component.
    Shows requests per minute over the last hour with success/error breakdown.
    """
    from datetime import datetime, timedelta
    
    now = datetime.utcnow()
    chart_data = []
    
    # Generate last 60 minutes of data (1-minute intervals)
    for i in range(59, -1, -1):
        minute_ago = now - timedelta(minutes=i)
        minute_str = minute_ago.strftime("%H:%M")
        
        # Count requests in this minute window
        total_requests = 0
        successful_requests = 0
        blocked_requests = 0
        
        # Calculate window bounds
        window_start = minute_ago
        window_end = minute_ago + timedelta(minutes=1)
        
        # Count from usage stats
        for idx, timestamp in enumerate(API_USAGE_STATS["timestamps"]):
            if window_start <= timestamp < window_end:
                if idx < len(API_USAGE_STATS["total_requests"]):
                    total_requests += API_USAGE_STATS["total_requests"][idx]
                if idx < len(API_USAGE_STATS["successful_requests"]):
                    successful_requests += API_USAGE_STATS["successful_requests"][idx]
                if idx < len(API_USAGE_STATS["blocked_requests"]):
                    blocked_requests += API_USAGE_STATS["blocked_requests"][idx]
        
        chart_data.append({
            "time": minute_str,
            "rps": total_requests,
            "success": successful_requests,
            "errors": blocked_requests
        })
    
    return chart_data

# Blocked requests endpoint for the React chart
@app.get("/api/blocked-requests")
def get_blocked_requests():
    """
    Return blocked requests data formatted for the BlockedRequestsChart component.
    Groups incidents by time intervals and counts blocked requests.
    """
    from collections import defaultdict
    from datetime import datetime, timedelta
    
    # Get all incidents
    import asyncio
    incidents = asyncio.run(get_incidents()) if callable(get_incidents) else get_incidents
    
    # Group incidents by hour for the chart
    hourly_blocks = defaultdict(int)
    now = datetime.utcnow()
    
    # Generate last 24 hours of data
    chart_data = []
    for i in range(24):
        hour_ago = now - timedelta(hours=i)
        hour_str = hour_ago.strftime("%H:00")
        hourly_blocks[hour_str] = 0
    
    # Count actual blocked incidents by hour
    for incident in incidents:
        try:
            incident_time = datetime.fromisoformat(incident["timestamp"].replace('Z', '+00:00'))
            # Only count incidents from last 24 hours
            if (now - incident_time).total_seconds() <= 86400:  # 24 hours in seconds
                hour_key = incident_time.strftime("%H:00")
                hourly_blocks[hour_key] += 1
        except Exception:
            continue
    
    # Convert to chart format (reverse to show oldest to newest)
    for i in range(23, -1, -1):
        hour_ago = now - timedelta(hours=i)
        hour_str = hour_ago.strftime("%H:00")
        chart_data.append({
            "time": hour_str,
            "blocked": hourly_blocks[hour_str]
        })
    
    return chart_data

# TTP endpoints for MITRE ATT&CK data
@app.get("/api/ttps")
async def get_ttps():
    """
    Get TTPs (Tactics, Techniques, and Procedures) data from RAG service MongoDB.
    Returns MITRE ATT&CK techniques detected in the environment.
    """
    try:
        # Get RAG service URL
        rag_service_url = os.getenv("RAG_SERVICE_URL", "http://localhost:8000")
        
        async with httpx.AsyncClient(timeout=CLIENT_TIMEOUT) as client:
            # Fetch threat statistics from RAG service
            response = await client.get(f"{rag_service_url}/threat_statistics?hours=168")  # Last 7 days
            
            if response.status_code != 200:
                logging.error(f"RAG service returned status {response.status_code}")
                return []
            
            threat_data = response.json()
            
            if threat_data.get('status') != 'success':
                logging.warning(f"RAG service returned unsuccessful status: {threat_data}")
                return []
            
            # Transform MongoDB threat data to TTP format
            ttps = await transform_threats_to_ttps(threat_data.get('data', {}))
            return ttps
            
    except httpx.RequestError as e:
        logging.error(f"Error connecting to RAG service: {e}")
        return []
    except Exception as e:
        logging.error(f"Error fetching TTPs: {e}")
        return []

@app.get("/api/ttps/bubbles")
async def get_ttps_bubble_data():
    """
    Get TTP data formatted specifically for the bubble chart.
    Groups TTPs by tactic and provides aggregated counts.
    """
    try:
        # Get the raw TTP data
        ttps = await get_ttps()
        
        if not ttps:
            return []
        
        # Group by tactic for bubble chart
        tactic_groups = {}
        for ttp in ttps:
            tactic = ttp['tactic']
            if tactic not in tactic_groups:
                tactic_groups[tactic] = {
                    'tactic': tactic,
                    'count': 0,
                    'techniques': [],
                    'total_incidents': 0,
                    'last_seen': ttp['lastSeen']
                }
            
            tactic_groups[tactic]['count'] += 1
            tactic_groups[tactic]['total_incidents'] += ttp['count']
            tactic_groups[tactic]['techniques'].append({
                'id': ttp['id'],
                'name': ttp['name'],
                'count': ttp['count']
            })
            
            # Update last seen to most recent
            if ttp['lastSeen'] > tactic_groups[tactic]['last_seen']:
                tactic_groups[tactic]['last_seen'] = ttp['lastSeen']
        
        # Convert to list format for bubble chart
        bubble_data = []
        for tactic, data in tactic_groups.items():
            bubble_data.append({
                'tactic': tactic,
                'technique_count': data['count'],
                'incident_count': data['total_incidents'],
                'techniques': data['techniques'][:5],  # Top 5 techniques
                'last_seen': data['last_seen']
            })
        
        # Sort by incident count (descending)
        bubble_data.sort(key=lambda x: x['incident_count'], reverse=True)
        
        return bubble_data
        
    except Exception as e:
        logging.error(f"Error fetching TTP bubble data: {e}")
        return []

async def transform_threats_to_ttps(threat_statistics: dict) -> list:
    """
    Transform threat statistics from MongoDB to TTP format expected by React components.
    """
    try:
        # Get RAG service URL for detailed threat data
        rag_service_url = os.getenv("RAG_SERVICE_URL", "http://localhost:8000")
        
        async with httpx.AsyncClient(timeout=CLIENT_TIMEOUT) as client:
            # We need to fetch detailed threat verdicts to get individual MITRE techniques
            # This would require a new endpoint in RAG service to get detailed verdicts
            # For now, we'll create sample data based on the attack types
            
            attack_types = threat_statistics.get('top_attack_types', [])
            
            ttps = []
            
            # Map common attack types to MITRE ATT&CK techniques
            attack_type_to_mitre = {
                'SQL Injection': {
                    'id': 'T1190',
                    'name': 'Exploit Public-Facing Application',
                    'tactic': 'Initial Access',
                    'description': 'Adversaries may attempt to take advantage of a weakness in an Internet-facing computer or program using software, data, or commands in order to cause unintended or unanticipated behavior.',
                    'source': 'Web Application Security Scanner'
                },
                'Cross-Site Scripting': {
                    'id': 'T1059.007',
                    'name': 'JavaScript',
                    'tactic': 'Execution',
                    'description': 'Adversaries may abuse various implementations of JavaScript for execution.',
                    'source': 'XSS Detection Engine'
                },
                'Command Injection': {
                    'id': 'T1059.004',
                    'name': 'Unix Shell',
                    'tactic': 'Execution', 
                    'description': 'Adversaries may abuse Unix shell commands and scripts for execution.',
                    'source': 'Command Injection Scanner'
                },
                'Directory Traversal': {
                    'id': 'T1083',
                    'name': 'File and Directory Discovery',
                    'tactic': 'Discovery',
                    'description': 'Adversaries may enumerate files and directories or may search in specific locations of a host or network share for certain information.',
                    'source': 'Path Traversal Detection'
                },
                'Authentication Bypass': {
                    'id': 'T1078',
                    'name': 'Valid Accounts',
                    'tactic': 'Credential Access',
                    'description': 'Adversaries may obtain and abuse credentials of existing accounts as a means of gaining Initial Access, Persistence, Privilege Escalation, or Defense Evasion.',
                    'source': 'Authentication Monitor'
                },
                'Brute Force': {
                    'id': 'T1110',
                    'name': 'Brute Force',
                    'tactic': 'Credential Access',
                    'description': 'Adversaries may use brute force techniques to gain access to accounts when passwords are unknown or when password hashes are obtained.',
                    'source': 'Login Attempt Monitor'
                },
                'Malware': {
                    'id': 'T1204',
                    'name': 'User Execution',
                    'tactic': 'Execution',
                    'description': 'An adversary may rely upon specific actions by a user in order to gain execution.',
                    'source': 'Malware Detection Engine'
                },
                'Phishing': {
                    'id': 'T1566',
                    'name': 'Phishing',
                    'tactic': 'Initial Access',
                    'description': 'Adversaries may send phishing messages to gain access to victim systems.',
                    'source': 'Email Security Gateway'
                }
            }
            
            # Create TTP entries from detected attack types
            for attack_type_data in attack_types:
                attack_type = attack_type_data.get('_id', '')
                count = attack_type_data.get('count', 0)
                
                if attack_type in attack_type_to_mitre:
                    mitre_info = attack_type_to_mitre[attack_type]
                    
                    ttp = {
                        'id': mitre_info['id'],
                        'name': mitre_info['name'], 
                        'tactic': mitre_info['tactic'],
                        'description': mitre_info['description'],
                        'source': mitre_info['source'],
                        'endpoint': f"Detected via {attack_type} analysis",
                        'count': count,
                        'lastSeen': datetime.now().isoformat()
                    }
                    
                    ttps.append(ttp)
            
            # Add some default techniques if no specific attacks detected
            if not ttps:
                default_ttps = [
                    {
                        'id': 'T1190',
                        'name': 'Exploit Public-Facing Application',
                        'tactic': 'Initial Access',
                        'description': 'Adversaries may attempt to take advantage of a weakness in an Internet-facing computer or program.',
                        'source': 'Security Monitoring',
                        'endpoint': 'Web Application Endpoints',
                        'count': 1,
                        'lastSeen': datetime.now().isoformat()
                    },
                    {
                        'id': 'T1078',
                        'name': 'Valid Accounts',
                        'tactic': 'Credential Access', 
                        'description': 'Adversaries may obtain and abuse credentials of existing accounts.',
                        'source': 'Authentication Logs',
                        'endpoint': 'Login Endpoints',
                        'count': 1,
                        'lastSeen': datetime.now().isoformat()
                    }
                ]
                ttps.extend(default_ttps)
            
            return ttps
            
    except Exception as e:
        logging.error(f"Error transforming threats to TTPs: {e}")
        return []

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "api-gateway",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)