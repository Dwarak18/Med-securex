import os
import json
import logging
from datetime import datetime, timezone, timedelta

# Import PostgreSQL functionality
try:
    from postgres_db import postgres_db, store_payload_analysis, log_incident as pg_log_incident
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    logging.warning("PostgreSQL not available")

logging.basicConfig(level=logging.INFO)

# --- Database Functions ---
async def setup_database():
    """Setup PostgreSQL database tables"""
    if POSTGRES_AVAILABLE:
        try:
            await postgres_db.setup_database()
            logging.info("✅ PostgreSQL database setup completed")
        except Exception as e:
            logging.error(f"❌ PostgreSQL setup error: {e}")
    else:
        logging.warning("PostgreSQL not available - database setup skipped")

async def log_request(status: str, client_ip: str):
    """Log API request - logging to PostgreSQL"""
    try:
        logging.info(f"✅ Request logged: {status} from {client_ip}")
    except Exception as e:
        logging.error(f"❌ log_request error: {e}", exc_info=True)

async def log_incident(ip: str, payload: str, rule: str):
    try:
        # PostgreSQL logging only
        if POSTGRES_AVAILABLE:
            try:
                import hashlib
                payload_hash = hashlib.sha256(payload.encode('utf-8')).hexdigest()
                
                # Determine attack type and severity from rule
                attack_type = "unknown"
                severity = "medium"
                
                if "XSS" in rule.upper() or "SCRIPT" in rule.upper():
                    attack_type = "XSS"
                    severity = "high"
                elif "SQL" in rule.upper():
                    attack_type = "SQLi"
                    severity = "critical"
                elif "TRAVERSAL" in rule.upper() or "PATH" in rule.upper():
                    attack_type = "Path Traversal"
                    severity = "high"
                elif "COMMAND" in rule.upper():
                    attack_type = "Command Injection"
                    severity = "critical"
                elif "RAG" in rule.upper():
                    # Extract attack type from RAG rule if available
                    parts = rule.split("-")
                    if len(parts) > 2:
                        attack_type = parts[2]
                        severity = "high"
                
                # Store payload analysis
                payload_id = await store_payload_analysis(
                    payload=payload,
                    payload_hash=payload_hash,
                    client_ip=ip,
                    verdict="malicious",
                    confidence_score=0.8,  # Default confidence for rule-based detection
                    analysis_method="rule_based",
                    attack_type=attack_type,
                    rule_triggered=rule
                )
                
                # Log incident in PostgreSQL
                await pg_log_incident(
                    client_ip=ip,
                    payload_id=payload_id,
                    severity=severity,
                    description=f"Malicious payload detected by rule: {rule}",
                    metadata={"rule": rule, "detection_method": "gateway_rules"}
                )
                
                logging.info(f"🚨 Incident recorded in PostgreSQL (payload_id: {payload_id})")
            except Exception as pg_e:
                logging.error(f"PostgreSQL logging failed: {pg_e}")
        else:
            logging.warning("🚨 Incident detected but PostgreSQL not available for logging")
            
        await log_request(status='error', client_ip=ip)
    except Exception as e:
        logging.error(f"❌ log_incident error: {e}", exc_info=True)

async def get_api_usage():
    """Get API usage statistics from PostgreSQL"""
    if not POSTGRES_AVAILABLE:
        return []
    
    try:
        async with postgres_db.pool.acquire() as conn:
            # Get recent payload analysis grouped by time intervals
            rows = await conn.fetch("""
                SELECT 
                    DATE_TRUNC('minute', created_at) as interval,
                    COUNT(*) FILTER (WHERE verdict = 'benign') as success,
                    COUNT(*) FILTER (WHERE verdict = 'malicious') as errors
                FROM payloads 
                WHERE created_at >= NOW() - INTERVAL '1 hour'
                GROUP BY DATE_TRUNC('minute', created_at)
                ORDER BY interval
            """)
            
            data = []
            for row in rows:
                data.append({
                    "time": row['interval'].strftime("%H:%M"),
                    "rps": row['success'] + row['errors'],
                    "success": row['success'],
                    "errors": row['errors']
                })
            return data
    except Exception as e:
        logging.error(f"❌ get_api_usage error: {e}", exc_info=True)
        return []

async def get_incidents():
    """Get incidents from PostgreSQL"""
    if not POSTGRES_AVAILABLE:
        return []
    
    try:
        async with postgres_db.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT i.*, p.original_payload, p.attack_type, p.client_ip
                FROM incidents i
                JOIN payloads p ON i.payload_id = p.id
                ORDER BY i.created_at DESC
                LIMIT 500
            """)
            
            incs = []
            for r in rows:
                inc = dict(r)
                # Convert datetime objects to ISO format
                for key, value in inc.items():
                    if isinstance(value, datetime):
                        inc[key] = value.isoformat()
                incs.append(inc)
            return incs
    except Exception as e:
        logging.error(f"❌ get_incidents error: {e}", exc_info=True)
        return []

async def mark_incident_handled(incident_id: int):
    """Mark incident as handled in PostgreSQL"""
    if not POSTGRES_AVAILABLE:
        return False
        
    try:
        async with postgres_db.pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE incidents 
                SET status = 'resolved', resolved_at = NOW()
                WHERE id = $1
            """, incident_id)
            updated = int(result.split()[-1]) > 0
            
            if updated:
                logging.info(f"✅ Incident {incident_id} marked as resolved")
            return updated
    except Exception as e:
        logging.error(f"❌ mark_incident_handled error: {e}", exc_info=True)
        return False