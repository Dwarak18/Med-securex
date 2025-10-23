import os
import sys
import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import GEMINI_API_KEY, MODEL_NAME, USE_GEMINI
import logging
logger = logging.getLogger("CyberAgents.InvestigationAgent")

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    logger.warning("Google Generative AI not available")
    GEMINI_AVAILABLE = False

class InvestigationAgent:
    """
    Agent to collect payload details including TTP ID, name, description, and response recommendations.
    """
    def __init__(self):
        try:
            # Load MITRE ATT&CK mapping and payload database
            self.mitre_mapping = self._load_mitre_mapping()
            self.payload_database = self._load_payload_database()
            
            # Initialize Gemini for enhanced analysis
            self.model = None
            if USE_GEMINI and GEMINI_AVAILABLE:
                try:
                    from google.generativeai.generative_models import GenerativeModel
                    self.model = GenerativeModel(MODEL_NAME)
                except (AttributeError, ImportError):
                    logger.warning("GenerativeModel not available in current genai version")
                
            logger.info("InvestigationAgent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize InvestigationAgent: {e}")
            raise
    
    def _load_mitre_mapping(self) -> Dict:
        """Load MITRE ATT&CK technique mappings"""
        try:
            # Common MITRE ATT&CK techniques for web application attacks
            mitre_mapping = {
                'sql_injection': {
                    'technique_id': 'T1190',
                    'technique_name': 'Exploit Public-Facing Application',
                    'description': 'SQL injection attacks exploit vulnerabilities in web applications',
                    'tactics': ['Initial Access'],
                    'response': [
                        'Block malicious payloads immediately',
                        'Apply input validation and parameterized queries',
                        'Monitor database logs for suspicious activity',
                        'Update and patch web applications'
                    ]
                },
                'xss': {
                    'technique_id': 'T1059.007',
                    'technique_name': 'Command and Scripting Interpreter: JavaScript',
                    'description': 'Cross-site scripting attacks inject malicious scripts',
                    'tactics': ['Execution'],
                    'response': [
                        'Implement Content Security Policy (CSP)',
                        'Sanitize user input and output encoding',
                        'Block malicious script execution',
                        'Monitor for unauthorized script activity'
                    ]
                },
                'command_injection': {
                    'technique_id': 'T1059',
                    'technique_name': 'Command and Scripting Interpreter',
                    'description': 'Command injection executes arbitrary commands on the host',
                    'tactics': ['Execution'],
                    'response': [
                        'Block command execution immediately',
                        'Implement input validation and sanitization',
                        'Use allowlists for permitted commands',
                        'Monitor system command execution logs'
                    ]
                },
                'directory_traversal': {
                    'technique_id': 'T1083',
                    'technique_name': 'File and Directory Discovery',
                    'description': 'Directory traversal attacks access unauthorized files',
                    'tactics': ['Discovery'],
                    'response': [
                        'Block path traversal attempts',
                        'Implement proper access controls',
                        'Validate and sanitize file paths',
                        'Monitor file system access logs'
                    ]
                },
                'xxe': {
                    'technique_id': 'T1190',
                    'technique_name': 'Exploit Public-Facing Application',
                    'description': 'XML External Entity attacks exploit XML parsers',
                    'tactics': ['Initial Access'],
                    'response': [
                        'Disable XML external entity processing',
                        'Implement secure XML parsing',
                        'Block malicious XML payloads',
                        'Monitor XML processing logs'
                    ]
                }
            }
            
            logger.info(f"Loaded {len(mitre_mapping)} MITRE ATT&CK technique mappings")
            return mitre_mapping
            
        except Exception as e:
            logger.error(f"Error loading MITRE mapping: {e}")
            return {}
    
    def _load_payload_database(self) -> Dict:
        """Load payload database with detailed information"""
        try:
            datasets_dir = Path(__file__).resolve().parents[2] / "datasets"
            payload_db = {}
            
            # Load payloads from different attack type CSV files
            attack_files = {
                'sql_injection.csv': 'sql_injection',
                'xss.csv': 'xss',
                'command_injection.csv': 'command_injection',
                'directory_traversal.csv': 'directory_traversal',
                'xxe.csv': 'xxe',
                'ssrf.csv': 'ssrf'
            }
            
            for file_name, attack_type in attack_files.items():
                file_path = datasets_dir / file_name
                if file_path.exists():
                    df = pd.read_csv(file_path)
                    if 'Payload' in df.columns:
                        for _, row in df.iterrows():
                            payload = str(row.get('Payload', '')).strip()
                            if payload:
                                payload_db[payload] = {
                                    'attack_type': attack_type,
                                    'severity': row.get('Severity', 'Medium'),
                                    'description': row.get('Description', f'{attack_type.replace("_", " ").title()} attack payload'),
                                    'signature': row.get('Signature', payload[:50] + '...' if len(payload) > 50 else payload)
                                }
            
            logger.info(f"Loaded {len(payload_db)} payloads into database")
            return payload_db
            
        except Exception as e:
            logger.error(f"Error loading payload database: {e}")
            return {}

    def investigate(self, findings: list) -> str:
        """
        Investigate findings and provide detailed payload information including TTP ID, name, description, and response.
        """
        try:
            # Input validation
            if not findings or not isinstance(findings, list):
                logger.warning("Invalid or empty findings list provided")
                return "ERROR: Invalid input - Findings list is empty or invalid"
            
            valid_findings = [f for f in findings if f and str(f).strip()]
            if not valid_findings:
                logger.warning("All findings are empty or invalid")
                return "ERROR: All findings are empty or invalid"
            
            logger.info(f"Investigating {len(valid_findings)} findings for TTP mapping")
            
            investigation_results = []
            
            for finding in valid_findings:
                # Extract payload information from finding
                payload_info = self._analyze_payload(finding)
                if payload_info:
                    investigation_results.append(payload_info)
            
            # Generate comprehensive investigation report
            report = self._generate_investigation_report(investigation_results, valid_findings)
            
            logger.info("Investigation completed with TTP mapping")
            return report
                
        except Exception as e:
            logger.error(f"Unexpected error in InvestigationAgent: {e}")
            return f"ERROR: Investigation failed - {str(e)}"
    
    def _analyze_payload(self, finding: str) -> Optional[Dict]:
        """Analyze a single finding to extract payload information and map to TTPs"""
        try:
            # Extract potential payload from finding
            payload = self._extract_payload_from_finding(finding)
            if not payload:
                return None
            
            # Check against known payload database
            payload_match = None
            best_similarity = 0
            
            for known_payload, info in self.payload_database.items():
                similarity = self._calculate_similarity(payload.lower(), known_payload.lower())
                if similarity > best_similarity and similarity > 0.3:
                    best_similarity = similarity
                    payload_match = info
            
            # Determine attack type from finding content
            attack_type = self._identify_attack_type(payload, finding)
            
            # Get MITRE mapping for attack type
            mitre_info = self.mitre_mapping.get(attack_type, {})
            
            result = {
                'payload': payload,
                'attack_type': attack_type,
                'ttp_id': mitre_info.get('technique_id', 'Unknown'),
                'ttp_name': mitre_info.get('technique_name', 'Unknown Technique'),
                'description': mitre_info.get('description', 'No description available'),
                'tactics': mitre_info.get('tactics', []),
                'severity': payload_match.get('severity', 'Medium') if payload_match else 'Medium',
                'response_recommendations': mitre_info.get('response', ['Monitor and analyze further']),
                'confidence': best_similarity,
                'signature': payload_match.get('signature', payload[:50]) if payload_match else payload[:50]
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing payload: {e}")
            return None
    
    def _extract_payload_from_finding(self, finding: str) -> Optional[str]:
        """Extract payload from finding text"""
        try:
            # Look for common payload indicators
            if "Analyzing API request:" in finding:
                parts = finding.split("Analyzing API request:")
                if len(parts) > 1:
                    return parts[1].split("...")[0].strip()
            
            # Look for MALICIOUS/ATTACK indicators with payload
            if "MALICIOUS" in finding or "ATTACK" in finding:
                # Try to extract the actual payload
                lines = finding.split('\n')
                for line in lines:
                    if any(indicator in line.lower() for indicator in ['select', 'script', 'union', '../', 'cmd']):
                        return line.strip()
            
            # Fallback: return the entire finding if it looks like a payload
            if any(pattern in finding.lower() for pattern in ['select', '<script', 'union', '../', '&&', '|']):
                return finding.strip()
                
            return None
            
        except Exception as e:
            logger.error(f"Error extracting payload: {e}")
            return None
    
    def _identify_attack_type(self, payload: str, finding: str) -> str:
        """Identify attack type based on payload and finding content"""
        try:
            payload_lower = payload.lower()
            finding_lower = finding.lower()
            
            # SQL Injection patterns
            if any(pattern in payload_lower for pattern in ['select', 'union', 'insert', 'delete', 'drop', "' or ", '" or ']):
                return 'sql_injection'
            
            # XSS patterns
            if any(pattern in payload_lower for pattern in ['<script', 'javascript:', 'onerror=', 'onload=', 'alert(']):
                return 'xss'
            
            # Command injection patterns
            if any(pattern in payload_lower for pattern in ['&&', '||', ';', '|', '`', 'cmd', 'exec', 'system']):
                return 'command_injection'
            
            # Directory traversal patterns
            if any(pattern in payload_lower for pattern in ['../', '..\\', 'etc/passwd', 'windows/system32']):
                return 'directory_traversal'
            
            # XXE patterns
            if any(pattern in payload_lower for pattern in ['<!entity', '<!doctype', 'system "', 'file://']):
                return 'xxe'
            
            # SSRF patterns
            if any(pattern in payload_lower for pattern in ['http://', 'https://', 'file://', 'localhost', '127.0.0.1']):
                return 'ssrf'
            
            return 'unknown'
            
        except Exception as e:
            logger.error(f"Error identifying attack type: {e}")
            return 'unknown'
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text strings"""
        try:
            from difflib import SequenceMatcher
            return SequenceMatcher(None, text1, text2).ratio()
        except Exception:
            return 0.0
    
    def _generate_investigation_report(self, investigation_results: List[Dict], findings: List[str]) -> str:
        """Generate comprehensive investigation report"""
        try:
            if not investigation_results:
                return "No specific threats identified in findings. General monitoring recommended."
            
            report_lines = ["=== THREAT INVESTIGATION REPORT ===\n"]
            
            # Summary
            total_threats = len(investigation_results)
            attack_types = list(set([result['attack_type'] for result in investigation_results]))
            severities = [result['severity'] for result in investigation_results]
            high_severity_count = sum(1 for s in severities if s.upper() in ['HIGH', 'CRITICAL'])
            
            report_lines.append(f"SUMMARY:")
            report_lines.append(f"- Total threats identified: {total_threats}")
            report_lines.append(f"- Attack types: {', '.join(attack_types)}")
            report_lines.append(f"- High/Critical severity threats: {high_severity_count}")
            report_lines.append("")
            
            # Detailed analysis for each threat
            for i, result in enumerate(investigation_results, 1):
                report_lines.append(f"THREAT {i}:")
                report_lines.append(f"- TTP ID: {result['ttp_id']}")
                report_lines.append(f"- TTP Name: {result['ttp_name']}")
                report_lines.append(f"- Attack Type: {result['attack_type'].replace('_', ' ').title()}")
                report_lines.append(f"- Severity: {result['severity']}")
                report_lines.append(f"- Description: {result['description']}")
                report_lines.append(f"- Tactics: {', '.join(result['tactics'])}")
                report_lines.append(f"- Payload Signature: {result['signature']}")
                report_lines.append("")
                
                report_lines.append("RESPONSE RECOMMENDATIONS:")
                for rec in result['response_recommendations']:
                    report_lines.append(f"  * {rec}")
                report_lines.append("")
            
            # Overall recommendations
            report_lines.append("OVERALL RECOMMENDATIONS:")
            if high_severity_count > 0:
                report_lines.append("* IMMEDIATE ACTION REQUIRED - High severity threats detected")
                report_lines.append("* Block malicious traffic immediately")
                report_lines.append("* Investigate potential data compromise")
            else:
                report_lines.append("* Continue monitoring for similar patterns")
                report_lines.append("* Review and update security controls")
            
            report_lines.append("* Update threat intelligence with new indicators")
            report_lines.append("* Consider implementing additional detection rules")
            
            return "\n".join(report_lines)
            
        except Exception as e:
            logger.error(f"Error generating investigation report: {e}")
            return f"Investigation completed but report generation failed: {str(e)}"
