import os
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
from google.generativeai.generative_models import GenerativeModel
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from google.generativeai import types as genai_types

logger = logging.getLogger(__name__)

class GeminiPayloadAnalyzer:
    """
    Utility class to analyze legitimate payloads using Gemini API
    to understand patterns and enhance security detection capabilities.
    """
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.0-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model_name
        self.model = None
        
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        try:
            self.model = GenerativeModel(model_name=self.model_name)
            logger.info(f"Gemini model {self.model_name} initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini model: {e}")
            raise
    
    def analyze_payload_batch(self, payloads: List[str], max_batch_size: int = 10) -> List[Dict[str, Any]]:
        """
        Analyze a batch of payloads using Gemini to understand their patterns and characteristics.
        
        Args:
            payloads: List of payload strings to analyze
            max_batch_size: Maximum number of payloads to analyze in one API call
            
        Returns:
            List of analysis results for each payload
        """
        results = []
        
        # Process payloads in batches to avoid API limits
        for i in range(0, len(payloads), max_batch_size):
            batch = payloads[i:i + max_batch_size]
            batch_results = self._analyze_single_batch(batch)
            results.extend(batch_results)
            
            # Add delay to respect API rate limits
            time.sleep(1)
        
        return results
    
    def _analyze_single_batch(self, payloads: List[str]) -> List[Dict[str, Any]]:
        """Analyze a single batch of payloads."""
        try:
            if self.model is None:
                logger.error("Gemini model not initialized")
                return [self._create_default_analysis(payload) for payload in payloads]
                
            # Create prompt for batch analysis
            prompt = self._create_analysis_prompt(payloads)
            
            # Configure safety settings to allow security content analysis
            safety_settings = {
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            }
            
            response = self.model.generate_content(
                prompt,
                safety_settings=safety_settings,
                generation_config=genai_types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=4000,
                )
            )
            
            # Parse the response
            return self._parse_analysis_response(response.text, payloads)
            
        except Exception as e:
            logger.error(f"Error analyzing payload batch: {e}")
            # Return default analysis for failed requests
            return [self._create_default_analysis(payload) for payload in payloads]
    
    def _create_analysis_prompt(self, payloads: List[str]) -> str:
        """Create analysis prompt for Gemini."""
        payload_list = "\n".join([f"{i+1}. {payload}" for i, payload in enumerate(payloads)])
        
        return f"""
As a cybersecurity expert, analyze these web payloads and provide detailed insights for each one.
For each payload, determine:

1. CLASSIFICATION: Is this payload LEGITIMATE or MALICIOUS?
2. PATTERN_TYPE: What type of request/attack pattern does this represent?
3. CHARACTERISTICS: Key technical characteristics (encoding, special chars, etc.)
4. INTENT: What is the likely intent or purpose?
5. RISK_LEVEL: Low/Medium/High risk assessment
6. SECURITY_INSIGHTS: What security patterns can be learned from this?

PAYLOADS TO ANALYZE:
{payload_list}

Please respond in this exact format for each payload:

PAYLOAD_1:
CLASSIFICATION: [LEGITIMATE/MALICIOUS]
PATTERN_TYPE: [type description]
CHARACTERISTICS: [key characteristics]
INTENT: [likely intent]
RISK_LEVEL: [Low/Medium/High]
SECURITY_INSIGHTS: [security learnings]

Continue this format for all payloads...
"""
    
    def _parse_analysis_response(self, response_text: str, payloads: List[str]) -> List[Dict[str, Any]]:
        """Parse Gemini's analysis response into structured data."""
        results = []
        
        try:
            # Split response by payload sections
            payload_sections = response_text.split("PAYLOAD_")
            
            for i, payload in enumerate(payloads):
                if i + 1 < len(payload_sections):
                    section = payload_sections[i + 1]
                    analysis = self._extract_analysis_fields(section)
                else:
                    analysis = self._create_default_analysis(payload)
                
                analysis['original_payload'] = payload
                analysis['analyzed_by'] = 'gemini'
                results.append(analysis)
                
        except Exception as e:
            logger.error(f"Error parsing Gemini response: {e}")
            # Fallback to default analysis
            results = [self._create_default_analysis(payload) for payload in payloads]
        
        return results
    
    def _extract_analysis_fields(self, section: str) -> Dict[str, Any]:
        """Extract analysis fields from a payload section."""
        analysis = {}
        
        field_mappings = {
            'CLASSIFICATION': 'classification',
            'PATTERN_TYPE': 'pattern_type', 
            'CHARACTERISTICS': 'characteristics',
            'INTENT': 'intent',
            'RISK_LEVEL': 'risk_level',
            'SECURITY_INSIGHTS': 'security_insights'
        }
        
        for field, key in field_mappings.items():
            try:
                if f"{field}:" in section:
                    value = section.split(f"{field}:")[1].split("\n")[0].strip()
                    analysis[key] = value
                else:
                    analysis[key] = "Unknown"
            except:
                analysis[key] = "Unknown"
        
        return analysis
    
    def _create_default_analysis(self, payload: str) -> Dict[str, Any]:
        """Create default analysis when Gemini analysis fails."""
        return {
            'classification': 'Unknown',
            'pattern_type': 'Unknown',
            'characteristics': 'Analysis failed',
            'intent': 'Unknown',
            'risk_level': 'Medium',
            'security_insights': 'Requires manual review',
            'original_payload': payload,
            'analyzed_by': 'fallback'
        }
    
    def analyze_legitimate_patterns(self, legitimate_payloads: List[str]) -> Dict[str, Any]:
        """
        Specialized analysis for legitimate payloads to understand normal patterns.
        
        Args:
            legitimate_payloads: List of legitimate payload strings
            
        Returns:
            Dictionary containing pattern analysis and insights
        """
        logger.info(f"Analyzing {len(legitimate_payloads)} legitimate payloads with Gemini")
        
        # Sample payloads if too many to avoid API limits and costs
        if len(legitimate_payloads) > 100:
            import random
            sample_payloads = random.sample(legitimate_payloads, 100)
            logger.info(f"Sampling 100 payloads from {len(legitimate_payloads)} for analysis")
        else:
            sample_payloads = legitimate_payloads
        
        # Analyze payloads in batches
        all_analyses = self.analyze_payload_batch(sample_payloads, max_batch_size=5)
        
        # Aggregate insights
        pattern_summary = self._aggregate_pattern_insights(all_analyses)
        pattern_summary['total_analyzed'] = len(all_analyses)
        pattern_summary['total_legitimate'] = len(legitimate_payloads)
        
        return pattern_summary
    
    def _aggregate_pattern_insights(self, analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate individual payload analyses into overall pattern insights."""
        
        # Count classifications
        classifications = {}
        pattern_types = {}
        risk_levels = {}
        
        legitimate_characteristics = []
        security_insights = []
        
        for analysis in analyses:
            # Count classifications
            classification = analysis.get('classification', 'Unknown')
            classifications[classification] = classifications.get(classification, 0) + 1
            
            # Count pattern types
            pattern = analysis.get('pattern_type', 'Unknown')
            pattern_types[pattern] = pattern_types.get(pattern, 0) + 1
            
            # Count risk levels
            risk = analysis.get('risk_level', 'Unknown')
            risk_levels[risk] = risk_levels.get(risk, 0) + 1
            
            # Collect characteristics and insights
            if classification.upper() == 'LEGITIMATE':
                characteristics = analysis.get('characteristics', '')
                if characteristics and characteristics != 'Unknown':
                    legitimate_characteristics.append(characteristics)
                
                insights = analysis.get('security_insights', '')
                if insights and insights != 'Unknown':
                    security_insights.append(insights)
        
        return {
            'classification_distribution': classifications,
            'pattern_type_distribution': pattern_types,
            'risk_level_distribution': risk_levels,
            'legitimate_characteristics': legitimate_characteristics,
            'security_insights': security_insights,
            'analysis_timestamp': time.time()
        }