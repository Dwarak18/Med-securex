import os
from dotenv import load_dotenv
import logging
from pathlib import Path

# Configure logging for config module
logging.basicConfig(level=logging.INFO)
config_logger = logging.getLogger("Config")

# Load .env file from current directory and parent directory
local_env = Path(__file__).parent / '.env'
parent_env = Path(__file__).parent.parent / '.env'

if local_env.exists():
    config_logger.info(f"Loading .env from: {local_env}")
    load_dotenv(dotenv_path=local_env)
elif parent_env.exists():
    config_logger.info(f"Loading .env from: {parent_env}")
    load_dotenv(dotenv_path=parent_env)
else:
    config_logger.warning("No .env file found")
    load_dotenv()  # Try loading from default locations

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "gemini-2.0-flash")

# Debug output
config_logger.info(f"GEMINI_API_KEY found: {bool(GEMINI_API_KEY)}")
config_logger.info(f"MODEL_NAME: {MODEL_NAME}")
if GEMINI_API_KEY:
    config_logger.info(f"API Key starts with: {GEMINI_API_KEY[:10]}...")

def is_gemini_available() -> bool:
    if not GEMINI_API_KEY:
        config_logger.warning("GEMINI_API_KEY not found - Gemini features will be disabled")
        return False
    if len(GEMINI_API_KEY.strip()) < 10:
        config_logger.warning("GEMINI_API_KEY appears invalid - Gemini features will be disabled")
        return False
    return True

USE_GEMINI = is_gemini_available()

config_logger.info(f"Configuration loaded successfully. Model: {MODEL_NAME}, Gemini enabled: {USE_GEMINI}")
