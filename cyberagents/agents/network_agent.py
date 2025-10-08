import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import GEMINI_API_KEY, MODEL_NAME, USE_GEMINI
from utils.logger import logger
import google.generativeai as genai
from google.api_core import exceptions
import joblib
from pathlib import Path

class NetworkAgent:
    def __init__(self):
        try:
            self.local_model = None
            model_path = Path(__file__).resolve().parents[1] / "models" / "network_model.joblib"
            if model_path.exists():
                self.local_model = joblib.load(str(model_path))
                logger.info("Loaded local Network classifier")

            self.model = None
            if USE_GEMINI:
                genai.configure(api_key=GEMINI_API_KEY)
                self.model = genai.GenerativeModel(MODEL_NAME)
            logger.info("NetworkAgent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize NetworkAgent: {e}")
            raise

    def analyze_traffic(self, network_log: str) -> str:
        """Detects suspicious network activity."""
        try:
            # Input validation
            if not network_log or not isinstance(network_log, str):
                logger.warning("Invalid or empty network log provided")
                return "ERROR: Invalid input - Network log is empty or invalid"
            
            if len(network_log.strip()) == 0:
                logger.warning("Empty network log after stripping whitespace")
                return "ERROR: Empty network log provided"
            
            logger.info(f"Analyzing network log: {network_log[:100]}...")
            
            if self.local_model:
                label = self.local_model.predict([network_log])[0]
                proba = max(self.local_model.predict_proba([network_log])[0]) if hasattr(self.local_model, 'predict_proba') else 0.5
                result = f"LOCAL_MODEL_VERDICT: {label} (confidence={proba:.2f})"
            else:
                result = "LOCAL_MODEL_UNAVAILABLE"

            if self.model:
                prompt = (
                    "Provide a network security verdict (NORMAL or THREAT) with a one-line reason for this log:\n"
                    f"{network_log}"
                )
                try:
                    response = self.model.generate_content(prompt)
                    llm_text = response.text if response and response.text else ""
                    return f"{result}\nGEMINI_VERDICT: {llm_text}"
                except Exception as e:
                    logger.warning(f"Gemini augmentation failed: {e}")
                    return result
            return result
            
        except exceptions.ResourceExhausted:
            logger.error("API quota exceeded for NetworkAgent")
            return "ERROR: API quota exceeded. Please try again later."
        except exceptions.InvalidArgument as e:
            logger.error(f"Invalid argument provided to API: {e}")
            return f"ERROR: Invalid request - {e}"
        except exceptions.ServiceUnavailable:
            logger.error("Gemini API service unavailable")
            return "ERROR: AI service temporarily unavailable"
        except Exception as e:
            logger.error(f"Unexpected error in NetworkAgent: {e}")
            return f"ERROR: Analysis failed - {str(e)}"
