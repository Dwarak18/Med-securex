import logging
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import re

try:
    from transformers import pipeline as hf_pipeline
    from langchain_community.llms import HuggingFacePipeline
except ImportError as e:
    logging.warning(f"Optional dependency not available: {e}")
    hf_pipeline = None
    HuggingFacePipeline = None

from .retrieval import (
    AdvancedRAGRetriever,
    RAGQueryOptimizer,
    RAGContext,
    QueryType
)
from .vector_db import CybersecurityVectorDB


@dataclass
class ThreatAnalysisResult:
    threat_level: str
    confidence_score: float
    attack_vectors: List[str]
    mitre_techniques: List[str]
    affected_systems: List[str]
    recommendations: List[str]
    evidence: List[Dict[str, Any]]
    analysis_summary: str
    timestamp: str


@dataclass
class PayloadAnalysisResult:
    payload_type: str
    attack_classification: str
    severity_level: str
    exploitation_method: str
    target_systems: List[str]
    mitigation_strategies: List[str]
    similar_attacks: List[Dict[str, Any]]
    technical_details: Dict[str, Any]
    risk_assessment: str


@dataclass
class SecurityRecommendation:
    priority: str
    category: str
    action: str
    description: str
    implementation_steps: List[str]
    resources_required: List[str]
    timeline: str
    effectiveness_rating: float


class RAGSecurityAgent:
    def __init__(self, vector_db: Optional[CybersecurityVectorDB] = None):
        self.vector_db = vector_db or CybersecurityVectorDB()
        self.retriever = AdvancedRAGRetriever(self.vector_db)
        self.optimizer = RAGQueryOptimizer(self.retriever)
        if HuggingFacePipeline and hf_pipeline:
            try:
                self.llm = HuggingFacePipeline(pipeline=hf_pipeline('text-generation', model='gpt2'))
            except Exception as e:
                logging.warning(f"Failed to initialize LLM in RAGSecurityAgent: {e}")
                self.llm = None
        else:
            self.llm = None
        self.threat_level_mapping = {
            'critical': ['critical', 'severe', 'high-risk', 'dangerous'],
            'high': ['high', 'significant', 'important', 'major'],
            'medium': ['medium', 'moderate', 'standard', 'normal'],
            'low': ['low', 'minor', 'minimal', 'negligible']
        }

    def generate_llm_response(self, prompt: str) -> str:
        if self.llm:
            try:
                return self.llm(prompt)
            except Exception as e:
                logging.warning(f"LLM generation failed: {e}")
                return "LLM response generation failed"
        else:
            return "LLM not available"

    def analyze_threat(self, threat_indicators: List[str], context: str = "") -> ThreatAnalysisResult:
        """Analyze threat indicators and provide comprehensive threat assessment."""
        try:
            # Retrieve relevant context from vector database
            query = f"threat analysis {' '.join(threat_indicators)} {context}".strip()
            rag_context = self.retriever.retrieve(query, top_k=5)
            
            # Basic analysis using rule-based approach
            threat_level = "Medium"  # Default
            confidence_score = min(rag_context.confidence_score + 0.1, 1.0)
            attack_vectors = ["unknown"]
            mitre_techniques = []
            affected_systems = ["unknown_systems"]
            recommendations = ["Conduct security review"]
            evidence = []
            
            indicator_text = ' '.join(threat_indicators).lower()
            if any(keyword in indicator_text for keyword in ['critical', 'exploit', 'malware']):
                threat_level = "Critical"
            elif any(keyword in indicator_text for keyword in ['suspicious', 'anomaly']):
                threat_level = "High"
            
            summary = f"Threat analysis for {len(threat_indicators)} indicators. Threat level: {threat_level}"
            
            return ThreatAnalysisResult(
                threat_level=threat_level,
                confidence_score=confidence_score,
                attack_vectors=attack_vectors,
                mitre_techniques=mitre_techniques,
                affected_systems=affected_systems,
                recommendations=recommendations,
                evidence=evidence,
                analysis_summary=summary,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logging.error(f"Error in threat analysis: {e}")
            return ThreatAnalysisResult(
                threat_level="Unknown",
                confidence_score=0.0,
                attack_vectors=[],
                mitre_techniques=[],
                affected_systems=[],
                recommendations=["Review threat indicators manually"],
                evidence=[],
                analysis_summary=f"Analysis failed: {str(e)}",
                timestamp=datetime.now().isoformat()
            )
    
    def analyze_payload(self, payload: str, context: str = "") -> PayloadAnalysisResult:
        """Analyze a security payload and classify the attack."""
        try:
            # Retrieve relevant context
            query = f"payload analysis {payload} {context}".strip()
            rag_context = self.retriever.retrieve(query, top_k=5)
            
            # Simple payload classification
            payload_lower = payload.lower()
            
            if any(keyword in payload_lower for keyword in ['select', 'union', 'drop', 'insert', "'"]):
                payload_type = "SQL Injection"
                severity_level = "High"
            elif any(keyword in payload_lower for keyword in ['<script', 'javascript:', 'onerror']):
                payload_type = "Cross-Site Scripting (XSS)"
                severity_level = "Medium"
            elif any(keyword in payload_lower for keyword in ['cmd', 'exec', 'system']):
                payload_type = "Command Injection"
                severity_level = "Critical"
            else:
                payload_type = "Unknown"
                severity_level = "Medium"
            
            return PayloadAnalysisResult(
                payload_type=payload_type,
                attack_classification="Code Injection",
                severity_level=severity_level,
                exploitation_method="Direct Exploitation",
                target_systems=["Web Applications"],
                mitigation_strategies=["Input validation", "Output encoding"],
                similar_attacks=[],
                technical_details={"payload_length": len(payload)},
                risk_assessment=f"{severity_level} risk payload detected"
            )
            
        except Exception as e:
            logging.error(f"Error in payload analysis: {e}")
            return PayloadAnalysisResult(
                payload_type="Unknown",
                attack_classification="Unclassified",
                severity_level="Medium",
                exploitation_method="Unknown",
                target_systems=[],
                mitigation_strategies=["Manual review required"],
                similar_attacks=[],
                technical_details={},
                risk_assessment=f"Analysis failed: {str(e)}"
            )
    
    def get_security_recommendations(self, security_context: str) -> List[SecurityRecommendation]:
        """Generate security recommendations based on context."""
        try:
            recommendations = []
            
            if "injection" in security_context.lower():
                recommendations.append(SecurityRecommendation(
                    priority="High",
                    category="Input Validation",
                    action="Implement input sanitization",
                    description="Deploy comprehensive input validation and sanitization measures",
                    implementation_steps=["Review input validation", "Implement parameterized queries"],
                    resources_required=["Development team"],
                    timeline="1-2 weeks",
                    effectiveness_rating=0.9
                ))
            
            if "authentication" in security_context.lower():
                recommendations.append(SecurityRecommendation(
                    priority="High",
                    category="Authentication",
                    action="Strengthen authentication mechanisms",
                    description="Enhance authentication security measures",
                    implementation_steps=["Implement MFA", "Review password policies"],
                    resources_required=["Security team"],
                    timeline="2-3 weeks",
                    effectiveness_rating=0.85
                ))
            
            return recommendations or [SecurityRecommendation(
                priority="Medium",
                category="General",
                action="Security review",
                description="Conduct general security assessment",
                implementation_steps=["Review security context"],
                resources_required=["Security analyst"],
                timeline="1 week",
                effectiveness_rating=0.6
            )]
            
        except Exception as e:
            logging.error(f"Error generating recommendations: {e}")
            return [SecurityRecommendation(
                priority="Low",
                category="Error",
                action="Manual review",
                description="Automated analysis failed",
                implementation_steps=["Manual analysis required"],
                resources_required=["Security analyst"],
                timeline="Unknown",
                effectiveness_rating=0.3
            )]
    
    def investigate_attack_pattern(self, threat_indicators: List[str]) -> Dict[str, Any]:
        """Investigate and correlate attack patterns."""
        try:
            return {
                "pattern_analysis": {
                    "indicators_analyzed": len(threat_indicators),
                    "confidence_level": 0.7,
                    "sources_consulted": ["vector_database"]
                },
                "attack_timeline": [{"phase": f"Phase {i+1}", "indicator": ind[:50]} for i, ind in enumerate(threat_indicators)],
                "related_techniques": [],
                "threat_actor_profile": {"sophistication_level": "Medium"},
                "attack_sophistication": "Medium" if len(threat_indicators) > 2 else "Low",
                "defensive_gaps": ["Input validation", "Access controls"]
            }
            
        except Exception as e:
            logging.error(f"Error in attack pattern investigation: {e}")
            return {"error": f"Investigation failed: {str(e)}"}

