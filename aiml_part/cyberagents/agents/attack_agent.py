import os
import sys
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import hashlib
import joblib
from pathlib import Path

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

class AttackAgent:
    """
    Payload detector agent that converts payloads to vectors and classifies as malicious/benign.
    """
    def __init__(self):
        try:
            # Initialize vectorizer for payload conversion
            self.vectorizer = TfidfVectorizer(
                max_features=10000,
                ngram_range=(1, 3),
                stop_words='english',
                lowercase=True
            )
            
            # Load pre-trained model if available
            self.local_model = None
            model_path = Path("/app/models/attack_model.joblib")
            if model_path.exists():
                self.local_model = joblib.load(str(model_path))
                logger.info("Loaded local Attack classifier")
            else:
                logger.warning(f"Attack model not found at {model_path}")

            # Initialize Gemini as backup
            self.model = None
            if USE_GEMINI and GEMINI_AVAILABLE:
                genai.configure(api_key=GEMINI_API_KEY)
                self.model = genai.GenerativeModel(MODEL_NAME)
                
            # Load known malicious patterns for vector comparison
            self.malicious_vectors = []
            self.benign_vectors = []
            self._load_known_patterns()
            
            logger.info("AttackAgent initialized successfully with vector analysis")
        except Exception as e:
            logger.error(f"Failed to initialize AttackAgent: {e}")
            raise
    
    def _load_known_patterns(self):
        """Load known malicious and benign patterns for vector comparison"""
        try:
            # Load from datasets directory
            datasets_dir = Path(__file__).resolve().parents[2] / "datasets"
            
            malicious_patterns = []
            benign_patterns = []
            
            # Load malicious patterns from various attack CSV files
            attack_files = [
                "sql_injection.csv", "xss.csv", "command_injection.csv",
                "directory_traversal.csv", "xxe.csv", "ssrf.csv"
            ]
            
            for file_name in attack_files:
                file_path = datasets_dir / file_name
                if file_path.exists():
                    import pandas as pd
                    df = pd.read_csv(file_path)
                    if 'Payload' in df.columns:
                        malicious_patterns.extend(df['Payload'].dropna().tolist())
            
            # Load benign patterns
            benign_file = datasets_dir / "normal_query.csv"
            if benign_file.exists():
                import pandas as pd
                df = pd.read_csv(benign_file)
                if 'Payload' in df.columns:
                    benign_patterns.extend(df['Payload'].dropna().tolist())
            
            # Convert patterns to vectors if we have enough data
            if malicious_patterns and benign_patterns:
                all_patterns = malicious_patterns + benign_patterns
                vectors = self.vectorizer.fit_transform(all_patterns)
                
                self.malicious_vectors = vectors[:len(malicious_patterns)]
                self.benign_vectors = vectors[len(malicious_patterns):]
                
                logger.info(f"Loaded {len(malicious_patterns)} malicious and {len(benign_patterns)} benign patterns")
            
        except Exception as e:
            logger.warning(f"Could not load known patterns: {e}")

    def convert_payload_to_vector(self, payload: str) -> np.ndarray:
        """Convert payload to vector representation"""
        try:
            if hasattr(self.vectorizer, 'transform'):
                vector = self.vectorizer.transform([payload])
                return vector.toarray()[0]
            else:
                # Fallback: simple hash-based vector
                payload_hash = hashlib.md5(payload.encode()).hexdigest()
                return np.array([int(char, 16) for char in payload_hash[:32]])
        except Exception as e:
            logger.error(f"Error converting payload to vector: {e}")
            return np.zeros(100)  # Return zero vector as fallback

    def detect_attack(self, api_request: str) -> str:
        """
        Converts payload to vector and analyzes for malicious/benign classification.
        """
        try:
            # Input validation
            if not api_request or not isinstance(api_request, str):
                logger.warning("Invalid or empty API request provided")
                return "ERROR: Invalid input - API request is empty or invalid"
            
            if len(api_request.strip()) == 0:
                logger.warning("Empty API request after stripping whitespace")
                return "ERROR: Empty API request provided"
            
            logger.info(f"Converting payload to vector for analysis: {api_request[:100]}...")
            
            # Convert payload to vector
            payload_vector = self.convert_payload_to_vector(api_request)
            
            # Primary analysis using pre-trained model
            if self.local_model:
                try:
                    prediction = self.local_model.predict([api_request])[0]
                    confidence = max(self.local_model.predict_proba([api_request])[0]) if hasattr(self.local_model, 'predict_proba') else 0.5
                    
                    # Fix prediction check - model returns 'Malicious' or 'Legit'
                    verdict = "MALICIOUS" if prediction == "Malicious" else "BENIGN"
                    result = f"LOCAL_MODEL_ANALYSIS: {verdict} (confidence={confidence:.2f})"
                    
                    logger.info(f"Local model classification: {prediction} -> {verdict} with confidence {confidence:.2f}")
                    
                except Exception as e:
                    logger.error(f"Local model prediction failed: {e}")
                    result = "LOCAL_MODEL_ERROR"
            else:
                result = "LOCAL_MODEL_UNAVAILABLE"
            
            # Vector similarity analysis with known patterns
            if len(self.malicious_vectors) > 0 and len(self.benign_vectors) > 0:
                try:
                    payload_vector_2d = payload_vector.reshape(1, -1)
                    
                    # Calculate similarity with malicious patterns
                    mal_similarities = cosine_similarity(payload_vector_2d, self.malicious_vectors)
                    max_mal_sim = np.max(mal_similarities)
                    
                    # Calculate similarity with benign patterns
                    ben_similarities = cosine_similarity(payload_vector_2d, self.benign_vectors)
                    max_ben_sim = np.max(ben_similarities)
                    
                    # Determine verdict based on similarity scores
                    if max_mal_sim > 0.7 and max_mal_sim > max_ben_sim:
                        vector_verdict = "MALICIOUS"
                        vector_confidence = max_mal_sim
                    elif max_ben_sim > 0.7 and max_ben_sim > max_mal_sim:
                        vector_verdict = "BENIGN"
                        vector_confidence = max_ben_sim
                    else:
                        vector_verdict = "UNKNOWN"
                        vector_confidence = max(max_mal_sim, max_ben_sim)
                    
                    result += f"\nVECTOR_SIMILARITY: {vector_verdict} (confidence={vector_confidence:.2f})"
                    
                except Exception as e:
                    logger.error(f"Vector similarity analysis failed: {e}")
            
            # Backup analysis using Gemini if available
            if self.model and GEMINI_AVAILABLE:
                try:
                    prompt = (
                        "Analyze this payload for cybersecurity threats. "
                        "Respond with 'MALICIOUS' or 'BENIGN' followed by a brief reason:\n"
                        f"{api_request}"
                    )
                    response = self.model.generate_content(prompt)
                    llm_text = response.text if response and response.text else "No response"
                    result += f"\nGEMINI_ANALYSIS: {llm_text}"
                    
                except Exception as e:
                    logger.warning(f"Gemini analysis failed: {e}")
            
            return result
            
        except Exception as e:
            logger.error(f"Unexpected error in AttackAgent: {e}")
            return f"ERROR: Analysis failed - {str(e)}"
    
    def get_payload_features(self, payload: str) -> dict:
        """Extract features from payload for analysis"""
        try:
            features = {
                'length': len(payload),
                'has_script_tags': '<script' in payload.lower(),
                'has_sql_keywords': any(kw in payload.lower() for kw in ['select', 'union', 'insert', 'delete', 'drop']),
                'has_path_traversal': any(pattern in payload for pattern in ['../', '..\\']),
                'has_command_injection': any(pattern in payload for pattern in ['|', '&&', ';', '`']),
                'has_xxe_patterns': any(pattern in payload.lower() for pattern in ['<!entity', '<!doctype']),
                'entropy': self._calculate_entropy(payload),
                'special_char_ratio': len([c for c in payload if not c.isalnum()]) / max(len(payload), 1)
            }
            return features
        except Exception as e:
            logger.error(f"Error extracting payload features: {e}")
            return {}
    
    def _calculate_entropy(self, text: str) -> float:
        """Calculate Shannon entropy of text"""
        try:
            import math
            from collections import Counter
            
            if not text:
                return 0.0
            
            counter = Counter(text)
            length = len(text)
            entropy = -sum((count / length) * math.log2(count / length) for count in counter.values())
            return entropy
        except Exception:
            return 0.0
