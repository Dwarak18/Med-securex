import os
import asyncio
import asyncpg  # type: ignore
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# PostgreSQL connection settings
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "cybersecurity")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

class PostgresDB:
    def __init__(self):
        self.pool: Optional[Any] = None
    
    async def init_pool(self):
        """Initialize connection pool"""
        try:
            self.pool = await asyncpg.create_pool(DATABASE_URL)
            logger.info("PostgreSQL connection pool created successfully")
        except Exception as e:
            logger.error(f"Failed to create PostgreSQL connection pool: {e}")
            raise
    
    async def close_pool(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("PostgreSQL connection pool closed")
    
    async def setup_database(self):
        """Create database tables if they don't exist"""
        if not self.pool:
            await self.init_pool()
        
        async with self.pool.acquire() as conn:  # type: ignore
            # Create payloads table for storing analyzed payloads
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS payloads (
                    id SERIAL PRIMARY KEY,
                    payload_hash VARCHAR(64) UNIQUE NOT NULL,
                    original_payload TEXT NOT NULL,
                    client_ip INET,
                    verdict VARCHAR(20) NOT NULL,
                    confidence_score FLOAT,
                    analysis_method VARCHAR(50),
                    attack_type VARCHAR(100),
                    rule_triggered VARCHAR(200),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """)
            
            # Create payload_patterns table for storing known malicious patterns
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS payload_patterns (
                    id SERIAL PRIMARY KEY,
                    pattern_hash VARCHAR(64) UNIQUE NOT NULL,
                    pattern_signature TEXT NOT NULL,
                    attack_type VARCHAR(100) NOT NULL,
                    confidence_score FLOAT NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    last_matched TIMESTAMP WITH TIME ZONE,
                    match_count INTEGER DEFAULT 0
                );
            """)
            
            # Create incidents table for detailed incident logging
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS incidents (
                    id SERIAL PRIMARY KEY,
                    client_ip INET NOT NULL,
                    payload_id INTEGER REFERENCES payloads(id),
                    severity VARCHAR(20) DEFAULT 'medium',
                    status VARCHAR(20) DEFAULT 'open',
                    description TEXT,
                    metadata JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    resolved_at TIMESTAMP WITH TIME ZONE
                );
            """)
            
            # Create indexes for better performance
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_payloads_hash ON payloads(payload_hash);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_payloads_verdict ON payloads(verdict);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_payloads_created_at ON payloads(created_at);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_patterns_hash ON payload_patterns(pattern_hash);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_incidents_ip ON incidents(client_ip);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_incidents_created_at ON incidents(created_at);")
            
            logger.info("Database tables created successfully")
    
    async def store_payload_analysis(self, 
                                   payload: str, 
                                   payload_hash: str,
                                   client_ip: str,
                                   verdict: str,
                                   confidence_score: float,
                                   analysis_method: str,
                                   attack_type: Optional[str] = None,
                                   rule_triggered: Optional[str] = None) -> int:
        """Store payload analysis results"""
        if not self.pool:
            await self.init_pool()
        
        async with self.pool.acquire() as conn:  # type: ignore
            # Insert or update payload
            payload_id = await conn.fetchval("""
                INSERT INTO payloads 
                (payload_hash, original_payload, client_ip, verdict, confidence_score, 
                 analysis_method, attack_type, rule_triggered)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (payload_hash) DO UPDATE SET
                    confidence_score = GREATEST(payloads.confidence_score, EXCLUDED.confidence_score),
                    updated_at = NOW()
                RETURNING id;
            """, payload_hash, payload, client_ip, verdict, confidence_score, 
                analysis_method, attack_type, rule_triggered)
            
            logger.info(f"Stored payload analysis with ID: {payload_id}")
            return payload_id
    
    async def store_malicious_pattern(self, 
                                    pattern_signature: str,
                                    pattern_hash: str,
                                    attack_type: str,
                                    confidence_score: float) -> int:
        """Store a malicious pattern for future matching"""
        if not self.pool:
            await self.init_pool()
        
        async with self.pool.acquire() as conn:  # type: ignore
            pattern_id = await conn.fetchval("""
                INSERT INTO payload_patterns 
                (pattern_hash, pattern_signature, attack_type, confidence_score)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (pattern_hash) DO UPDATE SET
                    confidence_score = GREATEST(payload_patterns.confidence_score, EXCLUDED.confidence_score),
                    match_count = payload_patterns.match_count + 1,
                    last_matched = NOW()
                RETURNING id;
            """, pattern_hash, pattern_signature, attack_type, confidence_score)
            
            logger.info(f"Stored malicious pattern with ID: {pattern_id}")
            return pattern_id
    
    async def find_similar_patterns(self, payload: str, similarity_threshold: float = 0.8) -> List[Dict]:
        """Find similar malicious patterns for fallback matching"""
        if not self.pool:
            await self.init_pool()
        
        async with self.pool.acquire() as conn:  # type: ignore
            # For now, we'll use simple text similarity
            # In production, you might want to use more sophisticated similarity functions
            patterns = await conn.fetch("""
                SELECT id, pattern_signature, attack_type, confidence_score, match_count
                FROM payload_patterns
                WHERE similarity(pattern_signature, $1) > $2
                ORDER BY similarity(pattern_signature, $1) DESC
                LIMIT 10;
            """, payload, similarity_threshold)
            
            return [dict(p) for p in patterns]
    
    async def log_incident(self, 
                          client_ip: str,
                          payload_id: int,
                          severity: str = "medium",
                          description: Optional[str] = None,
                          metadata: Optional[Dict] = None) -> int:
        """Log a security incident"""
        if not self.pool:
            await self.init_pool()
        
        async with self.pool.acquire() as conn:  # type: ignore
            incident_id = await conn.fetchval("""
                INSERT INTO incidents (client_ip, payload_id, severity, description, metadata)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id;
            """, client_ip, payload_id, severity, description, 
                json.dumps(metadata) if metadata else None)
            
            logger.info(f"Logged incident with ID: {incident_id}")
            return incident_id
    
    async def get_recent_payloads(self, limit: int = 100) -> List[Dict]:
        """Get recent payload analyses"""
        if not self.pool:
            await self.init_pool()
        
        async with self.pool.acquire() as conn:  # type: ignore
            rows = await conn.fetch("""
                SELECT p.*, i.severity, i.status as incident_status
                FROM payloads p
                LEFT JOIN incidents i ON p.id = i.payload_id
                ORDER BY p.created_at DESC
                LIMIT $1;
            """, limit)
            
            return [dict(r) for r in rows]
    
    async def get_attack_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get attack statistics for the specified time period"""
        if not self.pool:
            await self.init_pool()
        
        async with self.pool.acquire() as conn:  # type: ignore
            # Get attack counts by type
            attack_counts = await conn.fetch("""
                SELECT attack_type, COUNT(*) as count
                FROM payloads
                WHERE created_at >= NOW() - INTERVAL '%s hours'
                  AND verdict = 'malicious'
                GROUP BY attack_type
                ORDER BY count DESC;
            """ % hours)
            
            # Get total stats
            total_stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_payloads,
                    COUNT(*) FILTER (WHERE verdict = 'malicious') as malicious_count,
                    COUNT(*) FILTER (WHERE verdict = 'benign') as benign_count,
                    COUNT(*) FILTER (WHERE verdict = 'unknown') as unknown_count
                FROM payloads
                WHERE created_at >= NOW() - INTERVAL '%s hours';
            """ % hours)
            
            return {
                "attack_counts": [dict(r) for r in attack_counts],
                "total_stats": dict(total_stats)
            }

# Global instance
postgres_db = PostgresDB()

# Convenience functions
async def init_postgres():
    """Initialize PostgreSQL connection and tables"""
    await postgres_db.init_pool()
    await postgres_db.setup_database()

async def close_postgres():
    """Close PostgreSQL connections"""
    await postgres_db.close_pool()

async def store_payload_analysis(*args, **kwargs):
    """Store payload analysis - convenience function"""
    return await postgres_db.store_payload_analysis(*args, **kwargs)

async def store_malicious_pattern(*args, **kwargs):
    """Store malicious pattern - convenience function"""
    return await postgres_db.store_malicious_pattern(*args, **kwargs)

async def find_similar_patterns(*args, **kwargs):
    """Find similar patterns - convenience function"""
    return await postgres_db.find_similar_patterns(*args, **kwargs)

async def log_incident(*args, **kwargs):
    """Log incident - convenience function"""
    return await postgres_db.log_incident(*args, **kwargs)

async def get_recent_payloads(*args, **kwargs):
    """Get recent payloads - convenience function"""
    return await postgres_db.get_recent_payloads(*args, **kwargs)

async def get_attack_statistics(*args, **kwargs):
    """Get attack statistics - convenience function"""
    return await postgres_db.get_attack_statistics(*args, **kwargs)