import os
import json
import logging
from datetime import datetime, timezone, timedelta
from pymongo import MongoClient

logging.basicConfig(level=logging.INFO)


MONGO_URL = os.getenv("MONGO_URL")

mongo_client = MongoClient(MONGO_URL)
mongo_db = mongo_client["incident_logs"]

# --- Table Definitions ---
incidents_collection = mongo_db["incidents"]
requests_collection = mongo_db["requests"]

# --- Database Functions ---
def setup_database():
    # MongoDB creates collections automatically on first insert
    logging.info("[MongoDB] Collections will be created on first insert.")

async def log_request(status: str, client_ip: str):
    try:
        req = {
            "status": status,
            "client_ip": client_ip,
            "timestamp": datetime.now(timezone.utc)
        }
        requests_collection.insert_one(req)
        logging.info(f"✅ Request logged: {status}")
    except Exception as e:
        logging.error(f"❌ log_request error: {e}", exc_info=True)

async def log_incident(ip: str, payload: str, rule: str):
    try:
        inc = {
            "ip": ip,
            "payload": payload,
            "rule_triggered": rule,
            "status": "open",
            "timestamp": datetime.now(timezone.utc)
        }
        incidents_collection.insert_one(inc)
        logging.info("🚨 Incident recorded.")
        await log_request(status='error', client_ip=ip)
    except Exception as e:
        logging.error(f"❌ log_incident error: {e}", exc_info=True)

async def get_api_usage():
    try:
        # Aggregate requests in the last hour, grouped by 5-minute intervals
        now = datetime.now(timezone.utc)
        one_hour_ago = now - timedelta(hours=1)
        pipeline = [
            {"$match": {"timestamp": {"$gte": one_hour_ago}}},
            {"$group": {
                "_id": {
                    "interval": {
                        "$dateToString": {
                            "format": "%H:%M",
                            "date": {
                                "$subtract": [
                                    "$timestamp",
                                    {"$mod": [{"$minute": "$timestamp"}, 5]}
                                ]
                            }
                        }
                    }
                },
                "success": {"$sum": {"$cond": [{"$eq": ["$status", "success"]}, 1, 0]}},
                "errors": {"$sum": {"$cond": [{"$eq": ["$status", "error"]}, 1, 0]}}
            }},
            {"$sort": {"_id.interval": 1}}
        ]
        rows = list(requests_collection.aggregate(pipeline))
        data = []
        for row in rows:
            s = int(row.get('success', 0))
            e = int(row.get('errors', 0))
            data.append({"time": row['_id']['interval'], "rps": s+e, "success": s, "errors": e})
        return data
    except Exception as e:
        logging.error(f"❌ get_api_usage error: {e}", exc_info=True)
        return []

async def get_incidents():
    try:
        rows = incidents_collection.find().sort("timestamp", -1).limit(500)
        incs = []
        for r in rows:
            inc = dict(r)
            if isinstance(inc.get('timestamp'), datetime):
                inc['timestamp'] = inc['timestamp'].isoformat()
            incs.append(inc)
        return incs
    except Exception as e:
        logging.error(f"❌ get_incidents error: {e}", exc_info=True)
        return []

async def mark_incident_handled(incident_id: int):
    try:
        result = incidents_collection.update_one({"_id": incident_id}, {"$set": {"status": "handled"}})
        return result.modified_count > 0
    except Exception as e:
        logging.error(f"❌ mark_incident_handled error: {e}", exc_info=True)
        return False