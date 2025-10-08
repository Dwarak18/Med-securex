import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import GEMINI_API_KEY, MODEL_NAME, USE_GEMINI
from utils.logger import logger
import google.generativeai as genai
from google.api_core import exceptions
import joblib
from pathlib import Path

class AttackAgent:
    def __init__(self):
        try:
            self.local_model = None
            model_path = Path(__file__).resolve().parents[1] / "models" / "attack_model.joblib"
            if model_path.exists():
                self.local_model = joblib.load(str(model_path))
                logger.info("Loaded local Attack classifier")

            self.model = None
            if USE_GEMINI:
                genai.configure(api_key=GEMINI_API_KEY)
                self.model = genai.GenerativeModel(MODEL_NAME)
            logger.info("AttackAgent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize AttackAgent: {e}")
            raise

    def detect_attack(self, api_request: str) -> str:
        """Analyzes an API request log and detects possible attacks."""
        try:
            # Input validation
            if not api_request or not isinstance(api_request, str):
                logger.warning("Invalid or empty API request provided")
                return "ERROR: Invalid input - API request is empty or invalid"
            
            if len(api_request.strip()) == 0:
                logger.warning("Empty API request after stripping whitespace")
                return "ERROR: Empty API request provided"
            
            logger.info(f"Analyzing API request: {api_request[:100]}...")
            
            if self.local_model:
                label = self.local_model.predict([api_request])[0]
                proba = max(self.local_model.predict_proba([api_request])[0]) if hasattr(self.local_model, 'predict_proba') else 0.5
                result = f"LOCAL_MODEL_VERDICT: {label} (confidence={proba:.2f})"
            else:
                result = "LOCAL_MODEL_UNAVAILABLE"

            if self.model:
                prompt = (
                    "Provide a cybersecurity verdict (SAFE or ATTACK) with a one-line reason for this API request:\n"
                    f"{api_request}"
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
            logger.error("API quota exceeded for AttackAgent")
            return "ERROR: API quota exceeded. Please try again later."
        except exceptions.InvalidArgument as e:
            logger.error(f"Invalid argument provided to API: {e}")
            return f"ERROR: Invalid request - {e}"
        except exceptions.ServiceUnavailable:
            logger.error("Gemini API service unavailable")
            return "ERROR: AI service temporarily unavailable"
        except Exception as e:
            logger.error(f"Unexpected error in AttackAgent: {e}")
            return f"ERROR: Analysis failed - {str(e)}"
