from agents.attack_agent import AttackAgent
from agents.network_agent import NetworkAgent
from agents.investigation_agent import InvestigationAgent
from utils.logger import logger
import json
from typing import Dict, List, Optional, Any

class OrchestratorAgent:
    """
    Orchestrator to manage all three agents: attack detection, network monitoring, and investigation.
    Coordinates payload analysis, threat intelligence, and response recommendations.
    """
    def __init__(self):
        logger.info("Initializing enhanced OrchestratorAgent...")
        try:
            self.attack_agent = AttackAgent()
            self.network_agent = NetworkAgent()
            self.investigation_agent = InvestigationAgent()
            
            # Orchestrator state and configuration
            self.analysis_cache = {}
            self.threat_score_weights = {
                'attack_confidence': 0.4,
                'network_reputation': 0.3,
                'investigation_severity': 0.3
            }
            
            logger.info("Enhanced OrchestratorAgent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OrchestratorAgent: {e}")
            raise

    def process(self, api_logs: list, network_logs: list, source_ip: Optional[str] = None) -> str:
        """
        Enhanced processing: coordinates payload analysis, network monitoring, and threat investigation.
        Returns comprehensive security analysis with threat scoring and recommendations.
        """
        try:
            findings = []
            threat_indicators = []

            # Input validation
            if not api_logs and not network_logs:
                logger.warning("No logs provided for analysis")
                return "ERROR: No logs provided for analysis"

            # Phase 1: Attack Detection (Payload Analysis)
            if api_logs:
                if not isinstance(api_logs, list):
                    logger.error("API logs must be a list")
                    return "ERROR: API logs must be provided as a list"
                
                valid_api_logs = [log for log in api_logs if log and str(log).strip()]
                if valid_api_logs:
                    combined_api_logs = "\n".join(valid_api_logs)
                    logger.info(f"Phase 1: Processing {len(valid_api_logs)} payloads for attack detection...")
                    attack_result = self.attack_agent.detect_attack(combined_api_logs)
                    findings.append(f"PAYLOAD_ANALYSIS: {attack_result}")
                    
                    # Extract threat indicators
                    if "MALICIOUS" in attack_result:
                        threat_indicators.append("malicious_payload_detected")
                    if "confidence=" in attack_result and "0.8" in attack_result:
                        threat_indicators.append("high_confidence_threat")
                else:
                    logger.warning("All API logs are empty")

            # Phase 2: Network Analysis with IP intelligence
            network_data = []
            if network_logs and isinstance(network_logs, list):
                network_data.extend([log for log in network_logs if log and str(log).strip()])
            if source_ip:
                network_data.append(f"Source IP: {source_ip}")
            
            if network_data:
                combined_network_data = "\n".join(network_data)
                logger.info(f"Phase 2: Processing network data with IP intelligence...")
                network_result = self.network_agent.analyze_traffic(combined_network_data)
                findings.append(f"NETWORK_INTELLIGENCE: {network_result}")
                
                # Extract network threat indicators
                if "BLOCKED" in network_result:
                    threat_indicators.append("blocked_ip_detected")
                if "TOR_EXIT_NODE" in network_result:
                    threat_indicators.append("tor_network_detected")
                if "MALICIOUS" in network_result:
                    threat_indicators.append("malicious_ip_detected")

            # Phase 3: Investigation & Correlation
            if findings:
                logger.info("Phase 3: Correlating findings and generating threat intelligence...")
                investigation_result = self.investigation_agent.investigate(findings)
                
                # Calculate threat score
                threat_score = self._calculate_threat_score(threat_indicators, investigation_result)
                threat_level = "CRITICAL" if threat_score > 0.8 else "HIGH" if threat_score > 0.6 else "MEDIUM" if threat_score > 0.3 else "LOW"
                
                # Generate comprehensive report
                report = f"""=== COMPREHENSIVE SECURITY ANALYSIS ===

THREAT ASSESSMENT:
- Overall Threat Score: {threat_score:.2f}/1.0
- Threat Level: {threat_level}
- Source IP: {source_ip or 'Not provided'}

ANALYSIS RESULTS:
{chr(10).join(findings)}

THREAT INVESTIGATION:
{investigation_result}

THREAT INDICATORS DETECTED:
{chr(10).join([f"- {indicator.replace('_', ' ').title()}" for indicator in set(threat_indicators)]) if threat_indicators else "- No specific threat indicators"}

IMMEDIATE RECOMMENDATIONS:
{"* IMMEDIATE ACTION REQUIRED - Block malicious traffic" if threat_score > 0.7 else "* Continue monitoring for similar patterns"}
* Update threat intelligence with new indicators
* Review and enhance security controls
"""
                return report
            else:
                return "No valid logs found for analysis"
            
        except Exception as e:
            logger.error(f"Error in OrchestratorAgent.process: {e}")
            return f"ERROR: Processing failed - {str(e)}"
    
    def _calculate_threat_score(self, threat_indicators: List[str], investigation_result: str) -> float:
        """Calculate overall threat score based on findings"""
        try:
            score = 0.0
            
            # Payload analysis indicators
            if 'malicious_payload_detected' in threat_indicators:
                score += 0.4
            if 'high_confidence_threat' in threat_indicators:
                score += 0.2
            
            # Network intelligence indicators
            if 'blocked_ip_detected' in threat_indicators:
                score += 0.3
            if 'malicious_ip_detected' in threat_indicators:
                score += 0.2
            if 'tor_network_detected' in threat_indicators:
                score += 0.1
            
            # Investigation severity
            if 'CRITICAL' in investigation_result or 'HIGH' in investigation_result:
                score += 0.3
            elif 'MEDIUM' in investigation_result:
                score += 0.2
            
            return min(score, 1.0)  # Cap at 1.0
            
        except Exception as e:
            logger.error(f"Error calculating threat score: {e}")
            return 0.5
