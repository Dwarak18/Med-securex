from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel, Field
import uvicorn
import os
import sys
import asyncio
import logging
import time
import pandas as pd
import json
import csv
import hashlib
from contextlib import asynccontextmanager
from typing import Dict, List, Optional, Any, Union, TYPE_CHECKING
from datetime import datetime
from difflib import SequenceMatcher

# Set up logging FIRST (before any imports that use logger)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import PostgreSQL functionality
try:
    # Add API-gateway path to import PostgreSQL module
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../API-gateway'))
    from postgres_db import (
        init_postgres, store_payload_analysis, store_malicious_pattern,
        find_similar_patterns, get_recent_payloads, get_attack_statistics, postgres_db
    )
    POSTGRES_AVAILABLE = True
    logger.info("PostgreSQL module imported successfully")
except ImportError as e:
    logger.warning(f"PostgreSQL not available: {e}")
    POSTGRES_AVAILABLE = False

# Add the rag_pipeline to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '../'))

# Create fallback classes first
class MockRAGPipelineOrchestrator:
    def __init__(self, config): 
        self.vector_db = None

class MockRAGPipelineConfig:
    def __init__(self): 
        self.vector_db_path = ""

class MockRAGSecurityAgent:
    def __init__(self, vector_db): 
        self.vector_db = vector_db
    def analyze_threat(self, indicators): 
        return None
    def analyze_payload(self, payload): 
        return None

# Try to import the real RAG pipeline
try:
    from rag_pipeline.main_pipeline import RAGPipelineOrchestrator, RAGPipelineConfig
    from rag_pipeline.rag_agent import RAGSecurityAgent
    RAG_PIPELINE_AVAILABLE = True
    logger.info("RAG Pipeline successfully imported and available")
except ImportError as e:
    logger.warning(f"RAG Pipeline not available, using fallback: {e}")
    RAG_PIPELINE_AVAILABLE = False
    RAGPipelineOrchestrator = MockRAGPipelineOrchestrator
    RAGPipelineConfig = MockRAGPipelineConfig  
    RAGSecurityAgent = MockRAGSecurityAgent

# Global variables - RAG pipeline and cyberagents orchestrator
rag_pipeline = None
payload_dataset = None
cyber_orchestrator = None

def init_rag_pipeline():
    """Initialize the RAG pipeline for threat analysis"""
    global rag_pipeline
    if RAG_PIPELINE_AVAILABLE:
        try:
            config = RAGPipelineConfig()
            rag_pipeline = RAGPipelineOrchestrator(config)  # type: ignore
            
            # Initialize pipeline for threat analysis (not model training)
            init_result = rag_pipeline.initialize_pipeline()
            
            if init_result['status'] == 'success':
                logger.info("RAG Pipeline initialized successfully for threat analysis")
            else:
                logger.warning(f"Pipeline initialization warning: {init_result.get('error_message', 'Unknown issue')}")
            
            return rag_pipeline
        except Exception as e:
            logger.warning(f"Failed to initialize RAG Pipeline: {e}")
            return None
    else:
        logger.info("RAG Pipeline not available for threat analysis")
        return None

def init_cyber_orchestrator():
    """Initialize the cyber agents orchestrator"""
    global cyber_orchestrator
    try:
        # Import the orchestrator from cyberagents
        sys.path.append(os.path.join(os.path.dirname(__file__), "cyberagents"))
        from agents.orchestrator import OrchestratorAgent
        
        cyber_orchestrator = OrchestratorAgent()
        logger.info("Cyber agents orchestrator initialized successfully")
        return cyber_orchestrator
    except Exception as e:
        logger.error(f"Failed to initialize cyber agents orchestrator: {e}")
        return None

def load_payload_dataset():
    """Load the payload dataset from multiple CSV files in datasets directory"""
    global payload_dataset
    
    if payload_dataset is not None:
        return payload_dataset
    
    try:
        # Use datasets directory instead of single CSV file
        datasets_dir = os.path.join(os.path.dirname(__file__), "..", "datasets")
        payload_dataset = []
        
        # List of CSV files to load
        csv_files = [
            'brute_force.csv', 'command_injection.csv', 'cross_site_scripting.csv',
            'deserialization.csv', 'directory_traversal.csv', 'file_inclusion.csv',
            'generic_payload.csv', 'healthcare_idor.csv', 'healthcare_path_traversal.csv',
            'healthcare_sql_injection.csv', 'healthcare_xss.csv', 'http_protocol_attack.csv',
            'idor.csv', 'open_redirect.csv', 'path_traversal.csv', 'race_condition.csv',
            'sql_injection.csv', 'ssrf.csv', 'ssti.csv', 'xss.csv', 'xxe.csv'
        ]
        
        total_loaded = 0
        for csv_file in csv_files:
            csv_path = os.path.join(datasets_dir, csv_file)
            if os.path.exists(csv_path):
                try:
                    with open(csv_path, 'r', encoding='utf-8') as csvfile:
                        reader = csv.DictReader(csvfile)
                        file_count = 0
                        for row in reader:
                            # Extract attack type from filename
                            attack_type = csv_file.replace('.csv', '').replace('_', ' ').title()
                            
                            payload_dataset.append({
                                'payload': row.get('Payload', row.get('payload', '')).strip(),
                                'signature': row.get('Signature', row.get('signature', '')).strip(),
                                'attack_type': attack_type,
                                'severity': row.get('Severity', row.get('severity', 'Medium')).strip(),
                                'mitre': row.get('MITRE', row.get('mitre', '')).strip(),
                                'label': row.get('Label', row.get('label', '1')).strip(),
                                'description': row.get('Description', row.get('description', f'{attack_type} attack payload')).strip()
                            })
                            file_count += 1
                        
                        total_loaded += file_count
                        logger.info(f"Loaded {file_count} payloads from {csv_file}")
                        
                except Exception as file_error:
                    logger.warning(f"Failed to load {csv_file}: {str(file_error)}")
            else:
                logger.warning(f"CSV file not found: {csv_path}")
        
        logger.info(f"Total loaded {total_loaded} payload signatures from {len(csv_files)} dataset files")
        return payload_dataset
        
    except Exception as e:
        logger.error(f"Failed to load payload dataset: {str(e)}")
        return []

def enrich_threat_details_from_csv(payload, attack_type_hint=None):
    """Enrich threat details using CSV dataset for malicious payloads"""
    dataset = load_payload_dataset()
    
    if not dataset:
        return None
    
    best_match = None
    best_ratio = 0.0
    
    # Clean user payload for comparison
    user_payload_clean = payload.lower().strip()
    
    # First try exact matching by attack type if hint is provided
    if attack_type_hint:
        for entry in dataset:
            if entry['attack_type'].lower() == attack_type_hint.lower():
                payload_clean = entry['payload'].lower().strip()
                ratio = SequenceMatcher(None, user_payload_clean, payload_clean).ratio()
                
                if ratio > best_ratio and ratio > 0.2:  # Lower threshold for type-specific matches
                    best_ratio = ratio
                    best_match = entry
    
    # If no good type-specific match, try general matching
    if not best_match or best_ratio < 0.4:
        for entry in dataset:
            payload_clean = entry['payload'].lower().strip()
            
            # Calculate similarity ratio
            ratio = SequenceMatcher(None, user_payload_clean, payload_clean).ratio()
            
            # Also check if user payload contains key parts of the dataset payload
            if any(part in user_payload_clean for part in payload_clean.split() if len(part) > 3):
                ratio += 0.1  # Boost for partial matches
            
            if ratio > best_ratio and ratio > 0.3:  # Minimum threshold
                best_ratio = ratio
                best_match = entry
    
    return best_match if best_ratio > 0.3 else None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting RAG service with cyber agents integration...")
    
    global rag_pipeline, cyber_orchestrator
    try:
        # Initialize RAG pipeline for threat analysis
        rag_pipeline = init_rag_pipeline()
        
        if rag_pipeline:
            logger.info("RAG pipeline initialized successfully for threat analysis")
        else:
            logger.warning("RAG pipeline not initialized - threat analysis limited")
        
        # Initialize cyber agents orchestrator
        cyber_orchestrator = init_cyber_orchestrator()
        
        if cyber_orchestrator:
            logger.info("Cyber agents orchestrator initialized successfully")
        else:
            logger.warning("Cyber agents orchestrator not initialized - payload analysis limited")
        
        # Initialize PostgreSQL for malicious payload storage
        global POSTGRES_AVAILABLE
        if POSTGRES_AVAILABLE:
            try:
                await init_postgres()
                logger.info("PostgreSQL initialized successfully for payload storage")
            except Exception as pg_e:
                logger.warning(f"PostgreSQL initialization failed: {pg_e} - continuing without database")
                POSTGRES_AVAILABLE = False
        else:
            logger.warning("PostgreSQL not available - payload storage unavailable")
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        rag_pipeline = None
        cyber_orchestrator = None
    
    yield
    
    # Shutdown
    logger.info("RAG service shutting down")
    
    # Close PostgreSQL connection
    if POSTGRES_AVAILABLE:
        try:
            from postgres_db import close_postgres
            await close_postgres()
            logger.info("PostgreSQL connection closed")
        except Exception as e:
            logger.error(f"Error closing PostgreSQL connection: {e}")
    
    if rag_pipeline:
        try:
            # Add cleanup if needed
            pass
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

app = FastAPI(lifespan=lifespan, title="Enhanced RAG Security Service (ChromaDB)", version="2.0.0")

# Health check endpoint - SINGLE ENDPOINT ONLY
@app.get("/health")
async def rag_service_health():
    """Comprehensive health check endpoint"""
    try:
        # Determine the analysis mode
        analysis_mode = "cyber_agents_analysis"
        if cyber_orchestrator is None:
            analysis_mode = "degraded_no_orchestrator"
        
        health_status = {
            "status": "healthy",
            "service": "rag-service",
            "version": "3.0.0",
            "rag_pipeline_available": RAG_PIPELINE_AVAILABLE,
            "rag_pipeline_initialized": rag_pipeline is not None,
            "cyber_orchestrator_initialized": cyber_orchestrator is not None,
            "postgres_available": POSTGRES_AVAILABLE,
            "timestamp": datetime.now().isoformat(),
            "analysis_mode": analysis_mode,
            "agents": {
                "attack_agent": cyber_orchestrator is not None,
                "network_agent": cyber_orchestrator is not None,
                "investigation_agent": cyber_orchestrator is not None
            }
        }
        
        if cyber_orchestrator is None:
            health_status["status"] = "degraded"
            health_status["message"] = "Cyber agents orchestrator failed to initialize"
            
        return health_status
    except Exception as e:
        return {
            "status": "error",
            "service": "rag-service", 
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

class PayloadRequest(BaseModel):
    payload: str
    source_ip: Optional[str] = Field(None, description="Source IP address")
    user_agent: Optional[str] = Field(None, description="User agent string")
    timestamp: Optional[str] = Field(None, description="Request timestamp")

class ThreatDetails(BaseModel):
    signature: str = ""
    attack_type: str = ""
    severity: str = ""
    mitre_techniques: List[str] = []
    description: str = ""
    confidence_score: float = 0.0
    risk_level: str = ""
    affected_systems: List[str] = []
    recommendations: List[str] = []

class PayloadAnalysisResponse(BaseModel):
    verdict: str  # 'malicious', 'legit', 'unknown'
    confidence_score: float
    threat_details: ThreatDetails
    payload: str
    analysis_timestamp: str
    processing_time_ms: int
    analysis_method: str  # 'rag_pipeline', 'pattern_matching', 'failed'
    similar_threats: List[Dict[str, Any]] = []
    blocking_recommended: bool = False

@app.get('/stats')
async def stats():
    try:
        stats_info = {
            'status': 'ok',
            'rag_pipeline': 'available' if rag_pipeline else 'unavailable',
            'cyber_orchestrator': 'available' if cyber_orchestrator else 'unavailable',
            'postgres': 'connected' if POSTGRES_AVAILABLE else 'unavailable',
            'mode': 'cyber_agents_analysis'
        }
        
        return stats_info
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return {'status': 'error', 'message': str(e)}

@app.get('/malicious_payloads')
async def get_malicious_payloads(limit: int = 100):
    """
    Get recent malicious payloads for frontend display.
    This endpoint is exposed to the frontend to show detected threats.
    """
    try:
        if not POSTGRES_AVAILABLE:
            return {
                'status': 'error',
                'message': 'PostgreSQL not available',
                'payloads': []
            }
        
        # Get recent malicious payloads from PostgreSQL
        recent_payloads = await get_recent_payloads(limit=limit, verdict_filter='malicious')
        
        # Format for frontend display
        formatted_payloads = []
        for payload_data in recent_payloads:
            formatted_payloads.append({
                'id': payload_data.get('id'),
                'payload': payload_data.get('payload', '')[:200] + '...' if len(payload_data.get('payload', '')) > 200 else payload_data.get('payload', ''),
                'attack_type': payload_data.get('attack_type', 'Unknown'),
                'confidence_score': payload_data.get('confidence_score', 0.0),
                'client_ip': payload_data.get('client_ip', 'Unknown'),
                'timestamp': payload_data.get('timestamp', ''),
                'rule_triggered': payload_data.get('rule_triggered', 'Unknown'),
                'severity': 'High' if payload_data.get('confidence_score', 0) > 0.8 else 'Medium'
            })
        
        return {
            'status': 'success',
            'total_count': len(formatted_payloads),
            'payloads': formatted_payloads
        }
        
    except Exception as e:
        logger.error(f"Error getting malicious payloads: {e}")
        return {
            'status': 'error',
            'message': str(e),
            'payloads': []
        }

@app.get('/attack_statistics')
async def get_attack_statistics():
    """
    Get attack statistics for frontend dashboard.
    """
    try:
        if not POSTGRES_AVAILABLE:
            return {
                'status': 'error',
                'message': 'PostgreSQL not available',
                'statistics': {}
            }
        
        # Get attack statistics from PostgreSQL
        stats = await get_attack_statistics()
        
        return {
            'status': 'success',
            'statistics': stats
        }
        
    except Exception as e:
        logger.error(f"Error getting attack statistics: {e}")
        return {
            'status': 'error',
            'message': str(e),
            'statistics': {}
        }

# MongoDB threat statistics endpoint removed - using PostgreSQL statistics instead

@app.post('/check_payload')
async def check_payload(req: PayloadRequest) -> PayloadAnalysisResponse:
    """
    Check payload endpoint - converts payload to vector and analyzes for malicious/benign classification.
    This endpoint is only exposed to the backend, not the frontend.
    """
    start_time = time.time()
    analysis_timestamp = datetime.now().isoformat()
    
    try:
        # Initialize default response
        threat_details = ThreatDetails()
        verdict = 'unknown'
        confidence_score = 0.0
        similar_threats = []
        blocking_recommended = False
        analysis_method_used = "cyberagents"
        
        # Use cyber agents orchestrator for payload analysis
        if cyber_orchestrator:
            try:
                logger.info("🤖 Using cyber agents orchestrator for payload analysis")
                
                # Process payload through orchestrator (attack detection + investigation)
                api_logs = [req.payload]
                network_logs = []  # Can be extended later with network context
                
                orchestrator_result = cyber_orchestrator.process(api_logs, network_logs)
                
                # Parse orchestrator result to determine verdict
                if "ATTACK" in orchestrator_result.upper() or "MALICIOUS" in orchestrator_result.upper():
                    verdict = 'malicious'
                    confidence_score = 0.8  # Default confidence for detected attacks
                    blocking_recommended = True
                elif "SAFE" in orchestrator_result.upper() or "BENIGN" in orchestrator_result.upper():
                    verdict = 'benign'
                    confidence_score = 0.7
                    blocking_recommended = False
                else:
                    verdict = 'unknown'
                    confidence_score = 0.5
                    blocking_recommended = False
                
                # Extract threat details from orchestrator result
                threat_details = ThreatDetails(
                    description=orchestrator_result,
                    confidence_score=confidence_score,
                    recommendations=["Monitor for similar patterns"] if verdict == 'malicious' else ["Continue monitoring"]
                )
                
                logger.info(f"✅ Cyber agents analysis completed: {verdict} (confidence: {confidence_score:.2f})")
                
            except Exception as e:
                logger.error(f"❌ Cyber agents analysis failed: {e}")
                # Fallback to pattern matching
                verdict = 'unknown'
                analysis_method_used = "failed"
        else:
            logger.warning("⚠️ Cyber orchestrator not available")
            verdict = 'unknown'
            analysis_method_used = "failed"
        
        processing_time = int((time.time() - start_time) * 1000)
        
        # Store analysis results in PostgreSQL
        if POSTGRES_AVAILABLE and verdict in ['malicious', 'benign']:
            try:
                payload_hash = hashlib.sha256(req.payload.encode('utf-8')).hexdigest()
                
                await store_payload_analysis(
                    payload=req.payload,
                    payload_hash=payload_hash,
                    client_ip=req.source_ip or "unknown",
                    verdict=verdict,
                    confidence_score=confidence_score,
                    analysis_method=analysis_method_used,
                    attack_type=threat_details.attack_type,
                    rule_triggered=f"RAG-{analysis_method_used}"
                )
                
                # Store malicious patterns for future use
                if verdict == 'malicious' and confidence_score > 0.8:
                    await store_malicious_pattern(
                        pattern_signature=req.payload,
                        pattern_hash=payload_hash,
                        attack_type=threat_details.attack_type,
                        confidence_score=confidence_score
                    )
                    
                logger.info(f"✅ Analysis results stored in PostgreSQL")
            except Exception as e:
                logger.error(f"Failed to store analysis results in PostgreSQL: {e}")
        
        # Log malicious verdicts
        if verdict == 'malicious':
            await log_malicious_detailed(
                req.payload, confidence_score, threat_details, req.source_ip,
                processing_time, similar_threats, blocking_recommended
            )
        
        return PayloadAnalysisResponse(
            verdict=verdict,
            confidence_score=confidence_score,
            threat_details=threat_details,
            payload=req.payload,
            analysis_timestamp=analysis_timestamp,
            processing_time_ms=processing_time,
            analysis_method=analysis_method_used,
            similar_threats=similar_threats,
            blocking_recommended=blocking_recommended
        )
    
    except Exception as e:
        logger.error(f"Error in check_payload: {e}")
        processing_time = int((time.time() - start_time) * 1000)
        
        return PayloadAnalysisResponse(
            verdict='unknown',
            confidence_score=0.0,
            threat_details=ThreatDetails(
                description=f"Analysis failed: {str(e)}",
                recommendations=["Manual review required"]
            ),
            payload=req.payload,
            analysis_timestamp=analysis_timestamp,
            processing_time_ms=processing_time,
            analysis_method="failed",
            blocking_recommended=False
        )

async def analyze_with_rag_pipeline(payload: str) -> Optional[Dict[str, Any]]:
    """Analyze payload using the RAG pipeline"""
    try:
        if not rag_pipeline or not RAG_PIPELINE_AVAILABLE:
            logger.info("RAG pipeline not available for analysis")
            return None
        
        # Use the RAG pipeline for comprehensive analysis
        try:
            security_agent = RAGSecurityAgent(rag_pipeline.vector_db)  # type: ignore
        except Exception as e:
            logger.error(f"Failed to create RAGSecurityAgent: {e}")
            return None
        
        # Analyze the payload - convert string to list format expected by RAG
        threat_indicators = [payload]  # Convert single payload to list
        
        try:
            threat_analysis = security_agent.analyze_threat(threat_indicators)
            payload_analysis = security_agent.analyze_payload(payload)
        except Exception as e:
            logger.error(f"RAG analysis failed: {e}")
            return None
        
        # Determine verdict based on analysis
        verdict = 'unknown'
        confidence_score = 0.5
        
        if threat_analysis and hasattr(threat_analysis, 'threat_level'):
            threat_level = str(threat_analysis.threat_level).lower()
            if threat_level in ['high', 'critical']:
                verdict = 'malicious'
                confidence_score = getattr(threat_analysis, 'confidence_score', 0.8)
            elif threat_level in ['low', 'none']:
                verdict = 'legit'
                confidence_score = getattr(threat_analysis, 'confidence_score', 0.7)
        
        # Build base threat details from ChromaDB analysis
        base_threat_details = {
            'signature': getattr(payload_analysis, 'attack_classification', '') if payload_analysis else '',
            'attack_type': getattr(payload_analysis, 'payload_type', '') if payload_analysis else '',
            'severity': getattr(payload_analysis, 'severity_level', '') if payload_analysis else '',
            'mitre_techniques': getattr(threat_analysis, 'mitre_techniques', []) if threat_analysis else [],
            'description': getattr(threat_analysis, 'analysis_summary', '') if threat_analysis else '',
            'confidence_score': confidence_score,
            'risk_level': getattr(threat_analysis, 'threat_level', '') if threat_analysis else '',
            'affected_systems': getattr(threat_analysis, 'affected_systems', []) if threat_analysis else [],
            'recommendations': getattr(threat_analysis, 'recommendations', []) if threat_analysis else []
        }
        
        # If payload is identified as malicious, enrich with CSV dataset details
        if verdict == 'malicious':
            attack_type_hint = base_threat_details.get('attack_type', '')
            csv_match = enrich_threat_details_from_csv(payload, attack_type_hint)
            
            if csv_match:
                # Enrich with CSV data while keeping ChromaDB analysis
                threat_details = {
                    'signature': csv_match['signature'] or base_threat_details['signature'],
                    'attack_type': csv_match['attack_type'] or base_threat_details['attack_type'],
                    'severity': csv_match['severity'] or base_threat_details['severity'],
                    'mitre_techniques': [csv_match['mitre']] if csv_match['mitre'] else base_threat_details['mitre_techniques'],
                    'description': csv_match['description'] or base_threat_details['description'],
                    'confidence_score': confidence_score,
                    'risk_level': csv_match['severity'] or base_threat_details['risk_level'],
                    'affected_systems': base_threat_details['affected_systems'],
                    'recommendations': base_threat_details['recommendations']
                }
                logger.info(f"Enriched malicious payload with CSV data: {csv_match['attack_type']} - {csv_match['severity']}")
            else:
                threat_details = base_threat_details
        else:
            threat_details = base_threat_details
        
        similar_threats = []
        if threat_analysis and hasattr(threat_analysis, 'evidence'):
            similar_threats = getattr(threat_analysis, 'evidence', [])[:3]  # Top 3 similar threats
        
        return {
            'verdict': verdict,
            'confidence_score': confidence_score,
            'threat_details': threat_details,
            'similar_threats': similar_threats,
            'blocking_recommended': verdict == 'malicious' and confidence_score > 0.7
        }
        
    except Exception as e:
        logger.error(f"Unexpected error in RAG Pipeline analysis: {e}")
        return None

# Logging functions
def log_malicious(payload, score):
    try:
        log_dir = os.path.join(os.path.dirname(__file__), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        with open(os.path.join(log_dir, 'malicious_verdicts.log'), 'a', encoding='utf-8') as f:
            f.write(f"{datetime.now().isoformat()}\t{payload}\t{score}\n")
    except Exception as e:
        logger.error(f"Error logging malicious payload: {e}")

async def log_malicious_detailed(payload: str, score: float, threat_details: ThreatDetails, 
                               source_ip: Optional[str] = None, processing_time_ms: int = 0,
                               similar_threats: Optional[List[Dict]] = None, blocking_recommended: bool = False):
    """Enhanced logging for malicious payloads with detailed threat information"""
    try:
        # MongoDB logging (primary)
        if MONGODB_AVAILABLE and mongo_logger.connected:
            threat_details_dict = {
                'signature': threat_details.signature,
                'attack_type': threat_details.attack_type,
                'severity': threat_details.severity,
                'mitre_techniques': threat_details.mitre_techniques,
                'description': threat_details.description,
                'risk_level': threat_details.risk_level,
                'affected_systems': threat_details.affected_systems,
                'recommendations': threat_details.recommendations
            }
            
            await mongo_logger.log_threat_verdict(
                payload=payload,
                verdict='malicious',
                confidence_score=score,
                threat_details=threat_details_dict,
                source_ip=source_ip,
                processing_time_ms=processing_time_ms,
                similar_threats=similar_threats or [],
                blocking_recommended=blocking_recommended
            )
        
        # File logging (backup/legacy)
        log_dir = os.path.join(os.path.dirname(__file__), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'payload': payload,
            'confidence_score': score,
            'threat_details': {
                'signature': threat_details.signature,
                'attack_type': threat_details.attack_type,
                'severity': threat_details.severity,
                'mitre_techniques': threat_details.mitre_techniques,
                'description': threat_details.description,
                'risk_level': threat_details.risk_level
            },
            'source_ip': source_ip,
            'blocking_recommended': blocking_recommended
        }
        
        # Write to detailed log file
        with open(os.path.join(log_dir, 'detailed_malicious_verdicts.log'), 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry) + '\n')
            
        # Also write to simple log for backward compatibility
        log_malicious(payload, score)
        
    except Exception as e:
        logger.error(f"Error logging detailed malicious payload: {e}")

async def call_pattern_matching(payload: str) -> Dict[str, Any]:
    """Pattern matching fallback with CSV enrichment for malicious payloads"""
    try:
        
        # Fallback to pattern matching if no CSV match
        # SQL Injection patterns
        sql_patterns = ['union', 'select', 'drop', 'delete', 'insert', 'update', 'exec', 'execute', '--', ';--']
        
        # XSS patterns
        xss_patterns = ['<script', 'javascript:', 'alert(', 'document.cookie', 'eval(', 'onload=', 'onerror=']
        
        # Command injection patterns
        cmd_patterns = ['&&', '||', '|', ';', '`', '$(' ]
        
        # Directory traversal patterns
        path_patterns = ['../', '..\\', '/etc/passwd', '/etc/shadow', 'c:\\windows']
        
        # Authentication bypass patterns
        auth_patterns = ['admin', 'root', 'password', "'or'1'='1", '"or"1"="1']
        
        all_patterns = sql_patterns + xss_patterns + cmd_patterns + path_patterns + auth_patterns
        payload_lower = payload.lower()
        
        threat_count = 0
        detected_types = []
        
        for pattern in all_patterns:
            if pattern.lower() in payload_lower:
                threat_count += 1
                if pattern in sql_patterns:
                    detected_types.append("SQL Injection")
                elif pattern in xss_patterns:
                    detected_types.append("Cross-Site Scripting")
                elif pattern in cmd_patterns:
                    detected_types.append("Command Injection")
                elif pattern in path_patterns:
                    detected_types.append("Directory Traversal")
                elif pattern in auth_patterns:
                    detected_types.append("Authentication Bypass")
        
        # More sophisticated scoring
        if threat_count >= 2:
            verdict = 'malicious'
            confidence = 0.7
        elif threat_count == 1 and len(payload) > 50:  # Single pattern in long payload
            verdict = 'malicious'
            confidence = 0.6
        else:
            verdict = 'legit'
            confidence = 0.3
        
        # Build base threat details for pattern matching
        attack_types = list(set(detected_types)) if detected_types else ["Unknown"]
        severity = "High" if threat_count >= 2 else "Medium" if threat_count == 1 else "Low"
        
        base_threat_details = {
            'signature': f"Pattern-based detection: {', '.join(attack_types)}",
            'attack_type': ', '.join(attack_types),
            'severity': severity,
            'mitre_techniques': [],
            'description': f"Detected {threat_count} suspicious pattern(s) in payload",
            'confidence_score': confidence,
            'risk_level': severity,
            'affected_systems': [],
            'recommendations': ["Monitor payload", "Consider blocking if confirmed malicious"]
        }
        
        # If malicious, try to enrich with CSV data
        if verdict == 'malicious' and attack_types and attack_types[0] != "Unknown":
            csv_match = enrich_threat_details_from_csv(payload, attack_types[0])
            
            if csv_match:
                # Enrich with CSV data
                threat_details = {
                    'signature': csv_match['signature'] or base_threat_details['signature'],
                    'attack_type': csv_match['attack_type'] or base_threat_details['attack_type'],
                    'severity': csv_match['severity'] or base_threat_details['severity'],
                    'mitre_techniques': [csv_match['mitre']] if csv_match['mitre'] else base_threat_details['mitre_techniques'],
                    'description': csv_match['description'] or base_threat_details['description'],
                    'confidence_score': confidence,
                    'risk_level': csv_match['severity'] or base_threat_details['risk_level'],
                    'affected_systems': base_threat_details['affected_systems'],
                    'recommendations': base_threat_details['recommendations']
                }
                logger.info(f"Pattern matching enriched with CSV data: {csv_match['attack_type']} - {csv_match['severity']}")
            else:
                threat_details = base_threat_details
        else:
            threat_details = base_threat_details
        
        return {
            'verdict': verdict,
            'confidence_score': confidence,
            'threat_details': threat_details,
            'similar_threats': [],
            'blocking_recommended': verdict == 'malicious' and confidence > 0.6
        }
            
    except Exception as e:
        logger.error(f"Error in pattern matching: {e}")
        return {
            'verdict': 'unknown',
            'confidence_score': 0.0,
            'threat_details': {
                'signature': '',
                'attack_type': '',
                'severity': '',
                'mitre_techniques': [],
                'description': f"Pattern matching failed: {str(e)}",
                'confidence_score': 0.0,
                'risk_level': '',
                'affected_systems': [],
                'recommendations': ["Manual review required"]
            },
            'similar_threats': [],
            'blocking_recommended': False
        }

@app.get("/recent_payloads")
async def get_recent_payloads_endpoint(limit: int = 50):
    """Get recent payload analyses from PostgreSQL"""
    if not POSTGRES_AVAILABLE:
        raise HTTPException(status_code=503, detail="PostgreSQL not available")
    
    try:
        payloads = await get_recent_payloads(limit)
        return {"status": "success", "data": payloads}
    except Exception as e:
        logger.error(f"Error getting recent payloads: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/attack_statistics")
async def get_attack_statistics_endpoint(hours: int = 24):
    """Get attack statistics from PostgreSQL"""
    if not POSTGRES_AVAILABLE:
        raise HTTPException(status_code=503, detail="PostgreSQL not available")
    
    try:
        stats = await get_attack_statistics(hours)
        return {"status": "success", "data": stats}
    except Exception as e:
        logger.error(f"Error getting attack statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")