import os
import sys
import requests
import json
import ipaddress
from typing import Dict, List, Optional
import joblib
from pathlib import Path
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import GEMINI_API_KEY, MODEL_NAME, USE_GEMINI
from utils.logger import logger

try:
    import google.generativeai as genai
    from google.api_core import exceptions
    GEMINI_AVAILABLE = True
except ImportError:
    logger.warning("Google Generative AI not available")
    GEMINI_AVAILABLE = False

class NetworkAgent:
    """
    Network monitoring agent with SecurityTrail, VirusTotal APIs for IP monitoring,
    blocklist, blacklist, and Tor list checking.
    """
    def __init__(self):
        try:
            # API Configuration (load from environment or config)
            self.virustotal_api_key = os.getenv('VIRUSTOTAL_API_KEY', '')
            self.securitytrail_api_key = os.getenv('SECURITYTRAIL_API_KEY', '')
            
            # Load pre-trained network model
            self.local_model = None
            model_path = Path("/app/models/network_model.joblib")
            if model_path.exists():
                self.local_model = joblib.load(str(model_path))
                logger.info("Loaded local Network classifier")
            else:
                logger.warning(f"Network model not found at {model_path}")

            # Initialize Gemini as backup
            self.model = None
            if USE_GEMINI and GEMINI_AVAILABLE:
                genai.configure(api_key=GEMINI_API_KEY)
                self.model = genai.GenerativeModel(MODEL_NAME)
            
            # Load threat intelligence lists
            self.blocklist = self._load_blocklist()
            self.tor_exit_nodes = self._load_tor_exit_nodes()
            
            # Rate limiting for API calls
            self.last_vt_call = 0
            self.last_st_call = 0
            self.vt_rate_limit = 15  # seconds between calls for free tier
            self.st_rate_limit = 1   # seconds between calls
            
            logger.info("NetworkAgent initialized successfully with threat intelligence")
        except Exception as e:
            logger.error(f"Failed to initialize NetworkAgent: {e}")
            raise
    
    def _load_blocklist(self) -> set:
        """Load IP blocklist from various sources"""
        try:
            blocklist = set()
            
            # Common malicious IP ranges and known bad IPs
            known_bad_ips = [
                '0.0.0.0/8',        # Invalid source
                '10.0.0.0/8',       # Private range
                '127.0.0.0/8',      # Loopback
                '169.254.0.0/16',   # Link-local
                '172.16.0.0/12',    # Private range
                '192.168.0.0/16',   # Private range
                '224.0.0.0/4',      # Multicast
                '240.0.0.0/4'       # Reserved
            ]
            
            for ip_range in known_bad_ips:
                try:
                    network = ipaddress.ip_network(ip_range, strict=False)
                    blocklist.add(str(network))
                except ValueError:
                    continue
            
            logger.info(f"Loaded {len(blocklist)} IP ranges to blocklist")
            return blocklist
            
        except Exception as e:
            logger.error(f"Error loading blocklist: {e}")
            return set()
    
    def _load_tor_exit_nodes(self) -> set:
        """Load current Tor exit node list"""
        try:
            # In production, this would fetch from Tor Project's official list
            # For demo, using a small sample of known Tor exit nodes
            tor_nodes = {
                '185.220.101.1',
                '185.220.101.11',
                '185.220.101.19',
                '185.220.101.20',
                '185.220.101.21'
            }
            
            logger.info(f"Loaded {len(tor_nodes)} Tor exit nodes")
            return tor_nodes
            
        except Exception as e:
            logger.error(f"Error loading Tor exit nodes: {e}")
            return set()
    
    def _is_rate_limited(self, service: str) -> bool:
        """Check if rate limited for API service"""
        current_time = time.time()
        
        if service == 'virustotal':
            if current_time - self.last_vt_call < self.vt_rate_limit:
                return True
            self.last_vt_call = current_time
        elif service == 'securitytrail':
            if current_time - self.last_st_call < self.st_rate_limit:
                return True
            self.last_st_call = current_time
        
        return False

    def analyze_traffic(self, network_log: str) -> str:
        """
        Analyze network traffic with IP monitoring using SecurityTrail, VirusTotal APIs,
        blocklist, blacklist, and Tor list checking.
        """
        try:
            # Input validation
            if not network_log or not isinstance(network_log, str):
                logger.warning("Invalid or empty network log provided")
                return "ERROR: Invalid input - Network log is empty or invalid"
            
            if len(network_log.strip()) == 0:
                logger.warning("Empty network log after stripping whitespace")
                return "ERROR: Empty network log provided"
            
            logger.info(f"Analyzing network traffic with IP intelligence: {network_log[:100]}...")
            
            # Extract IP addresses from network log
            ip_addresses = self._extract_ip_addresses(network_log)
            
            results = []
            
            # Local model analysis
            if self.local_model:
                try:
                    prediction = self.local_model.predict([network_log])[0]
                    confidence = max(self.local_model.predict_proba([network_log])[0]) if hasattr(self.local_model, 'predict_proba') else 0.5
                    # Fix prediction check - model returns 'Malicious' or 'Legit'
                    verdict = "SUSPICIOUS" if prediction == "Malicious" else "NORMAL"
                    results.append(f"LOCAL_MODEL: {verdict} (confidence={confidence:.2f})")
                    logger.info(f"Network model classification: {prediction} -> {verdict} with confidence {confidence:.2f}")
                except Exception as e:
                    logger.error(f"Local model analysis failed: {e}")
                    results.append("LOCAL_MODEL: ERROR")
            else:
                results.append("LOCAL_MODEL: UNAVAILABLE")
            
            # IP-based threat intelligence analysis
            if ip_addresses:
                ip_analysis = self._analyze_ip_addresses(ip_addresses)
                results.extend(ip_analysis)
            else:
                results.append("IP_ANALYSIS: No IP addresses found in log")
            
            # Backup analysis using Gemini
            if self.model and GEMINI_AVAILABLE:
                try:
                    prompt = (
                        "Analyze this network log for security threats. "
                        "Respond with 'THREAT' or 'NORMAL' followed by a brief reason:\n"
                        f"{network_log}"
                    )
                    response = self.model.generate_content(prompt)
                    llm_text = response.text if response and response.text else "No analysis available"
                    results.append(f"GEMINI_ANALYSIS: {llm_text}")
                except Exception as e:
                    logger.warning(f"Gemini analysis failed: {e}")
                    results.append("GEMINI_ANALYSIS: FAILED")
            
            return "\n".join(results)
            
        except Exception as e:
            logger.error(f"Unexpected error in NetworkAgent: {e}")
            return f"ERROR: Network analysis failed - {str(e)}"
    
    def _extract_ip_addresses(self, text: str) -> List[str]:
        """Extract IP addresses from text using regex"""
        try:
            import re
            # IPv4 pattern
            ipv4_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
            ip_addresses = re.findall(ipv4_pattern, text)
            
            # Validate and filter IPs
            valid_ips = []
            for ip in ip_addresses:
                try:
                    ipaddress.ip_address(ip)
                    if not ipaddress.ip_address(ip).is_private:  # Focus on public IPs
                        valid_ips.append(ip)
                except ValueError:
                    continue
            
            return list(set(valid_ips))  # Remove duplicates
            
        except Exception as e:
            logger.error(f"Error extracting IP addresses: {e}")
            return []
    
    def _analyze_ip_addresses(self, ip_addresses: List[str]) -> List[str]:
        """Analyze IP addresses using various threat intelligence sources"""
        analysis_results = []
        
        for ip in ip_addresses:
            try:
                # Check against blocklist
                if self._is_ip_blocked(ip):
                    analysis_results.append(f"IP_BLOCKLIST: {ip} - BLOCKED (known malicious)")
                    continue
                
                # Check against Tor exit nodes
                if ip in self.tor_exit_nodes:
                    analysis_results.append(f"TOR_CHECK: {ip} - TOR_EXIT_NODE (anonymization network)")
                    continue
                
                # VirusTotal lookup
                vt_result = self._check_virustotal(ip)
                if vt_result:
                    analysis_results.append(f"VIRUSTOTAL: {ip} - {vt_result}")
                
                # SecurityTrail lookup
                st_result = self._check_securitytrail(ip)
                if st_result:
                    analysis_results.append(f"SECURITYTRAIL: {ip} - {st_result}")
                
                # If no threats found
                if not any(result.startswith(f"VIRUSTOTAL: {ip}") or result.startswith(f"SECURITYTRAIL: {ip}") for result in analysis_results[-2:]):
                    analysis_results.append(f"IP_REPUTATION: {ip} - CLEAN (no known threats)")
                
            except Exception as e:
                logger.error(f"Error analyzing IP {ip}: {e}")
                analysis_results.append(f"IP_ANALYSIS: {ip} - ERROR")
        
        return analysis_results
    
    def _is_ip_blocked(self, ip: str) -> bool:
        """Check if IP is in blocklist"""
        try:
            ip_obj = ipaddress.ip_address(ip)
            for blocked_range in self.blocklist:
                try:
                    network = ipaddress.ip_network(blocked_range, strict=False)
                    if ip_obj in network:
                        return True
                except ValueError:
                    continue
            return False
        except ValueError:
            return False
    
    def _check_virustotal(self, ip: str) -> Optional[str]:
        """Check IP reputation using VirusTotal API"""
        try:
            if not self.virustotal_api_key:
                return "API_KEY_MISSING"
            
            if self._is_rate_limited('virustotal'):
                return "RATE_LIMITED"
            
            url = f"https://www.virustotal.com/vtapi/v2/ip-address/report"
            params = {
                'apikey': self.virustotal_api_key,
                'ip': ip
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('response_code') == 1:
                    positives = data.get('positives', 0)
                    total = data.get('total', 0)
                    if positives > 0:
                        return f"MALICIOUS ({positives}/{total} detections)"
                    else:
                        return f"CLEAN ({total} scanners)"
                else:
                    return "NOT_FOUND"
            else:
                return f"API_ERROR ({response.status_code})"
                
        except Exception as e:
            logger.error(f"VirusTotal API error for {ip}: {e}")
            return "ERROR"
    
    def _check_securitytrail(self, ip: str) -> Optional[str]:
        """Check IP information using SecurityTrail API"""
        try:
            if not self.securitytrail_api_key:
                return "API_KEY_MISSING"
            
            if self._is_rate_limited('securitytrail'):
                return "RATE_LIMITED"
            
            url = f"https://api.securitytrails.com/v1/ips/{ip}"
            headers = {
                'APIKEY': self.securitytrail_api_key
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                # Extract useful information
                info_parts = []
                if 'country' in data:
                    info_parts.append(f"Country: {data['country']}")
                if 'organization' in data:
                    info_parts.append(f"Org: {data['organization']}")
                
                # Check for suspicious characteristics
                suspicious_indicators = []
                if 'hostnames' in data and len(data['hostnames']) > 10:
                    suspicious_indicators.append("MANY_HOSTNAMES")
                
                result = ", ".join(info_parts)
                if suspicious_indicators:
                    result += f" [SUSPICIOUS: {', '.join(suspicious_indicators)}]"
                
                return result if result else "INFO_AVAILABLE"
            else:
                return f"API_ERROR ({response.status_code})"
                
        except Exception as e:
            logger.error(f"SecurityTrail API error for {ip}: {e}")
            return "ERROR"
