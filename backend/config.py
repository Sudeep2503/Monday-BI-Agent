"""Configuration module for the Monday BI Agent."""
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / '.env'

# Load environment variables from the backend .env file
load_dotenv(ENV_PATH, override=True)


class Config:
    """Configuration class for the Flask application."""

    # API Configuration
    MONDAY_API_TOKEN = os.getenv('MONDAY_API_TOKEN', '')
    MONDAY_API_URL = os.getenv('MONDAY_API_URL', 'https://api.monday.com/v2')

    # Board Configuration
    DEALS_BOARD_ID = os.getenv('DEALS_BOARD_ID', '')
    WORK_ORDERS_BOARD_ID = os.getenv('WORK_ORDERS_BOARD_ID', '')

    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')

    # Flask Configuration
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    PORT = int(os.getenv("PORT", 10000))
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')

    @classmethod
    def validate_monday_config(cls) -> dict:
        """Validate Monday.com-related configuration values."""
        errors = []
        if not cls.MONDAY_API_TOKEN:
            errors.append('MONDAY_API_TOKEN is missing')
        if not cls.DEALS_BOARD_ID:
            errors.append('DEALS_BOARD_ID is missing')
        if not cls.WORK_ORDERS_BOARD_ID:
            errors.append('WORK_ORDERS_BOARD_ID is missing')
        return {
            'valid': not errors,
            'errors': errors,
            'token': bool(cls.MONDAY_API_TOKEN),
            'deals_board': bool(cls.DEALS_BOARD_ID),
            'work_orders_board': bool(cls.WORK_ORDERS_BOARD_ID),
        }
