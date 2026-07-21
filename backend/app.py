"""Flask application entry point for the Monday BI Agent.

Integrates Monday.com API client, data processing, business analysis,
and AI agent for intelligent business intelligence queries.
"""

import logging
import os
from typing import Any, Dict
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

# Explicitly load .env from the backend directory before importing Config
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

from config import Config
from monday_client import MondayClient
from data_processor import DataProcessor
from business_analyzer import BusinessAnalyzer
from ai_agent import BusinessAIAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask application
app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# Initialize backend services
data_processor = DataProcessor()
business_analyzer = BusinessAnalyzer()
ai_agent = BusinessAIAgent(business_analyzer)

# Monday client will be instantiated lazily to allow graceful startup
monday_client = None
monday_init_error: str | None = None

# Global cache for processed data
# Structure: {'deals': {...}, 'work_orders': {...}, 'timestamp': '...'}
data_cache: Dict[str, Any] = {
    'deals': [],
    'work_orders': [],
    'timestamp': None
}


def get_monday_client() -> Any:
    """Return a configured MondayClient or None if it cannot be created."""
    global monday_client, monday_init_error
    if monday_client is not None:
        return monday_client
    if monday_init_error is not None:
        return None

    try:
        monday_client = MondayClient()
        logger.info("Monday client initialized")
        return monday_client
    except ValueError as e:
        monday_init_error = str(e)
        logger.warning("Monday client initialization warning: %s", monday_init_error)
        return None


def get_monday_status() -> str:
    """Return the Monday API connection status for the health endpoint."""
    state, _ = get_monday_connection_state()
    return 'connected' if state == 'connected' else 'disconnected'


def get_monday_connection_state() -> tuple[str, str]:
    """Classify Monday configuration and connection state."""
    validation = Config.validate_monday_config()
    if not validation['valid']:
        return 'missing_configuration', '; '.join(validation['errors'])

    client = get_monday_client()
    if not client:
        return 'missing_configuration', monday_init_error or 'Unable to initialize Monday client'

    try:
        if client.test_connection():
            return 'connected', 'Connected to Monday.com'
        return 'disconnected', 'Connection test failed'
    except ValueError as e:
        message = str(e).lower()
        if 'token' in message or 'authentication' in message:
            return 'invalid_api_token', 'Invalid Monday API token'
        if 'board' in message or 'not found' in message:
            return 'invalid_board_id', 'Invalid Monday board ID'
        return 'disconnected', str(e)
    except Exception as e:
        logger.debug('Monday health check failed: %s', str(e))
        return 'disconnected', str(e)


def refresh_cache() -> Dict[str, Any]:
    """Fetch, process, and cache data from Monday.com."""
    client = get_monday_client()
    if not client:
        raise ValueError('Monday.com API is not configured')

    raw_data = client.fetch_all()
    if not isinstance(raw_data, dict):
        raise ValueError('Invalid data received from Monday.com')

    deals_data = raw_data.get('deals', {})
    work_orders_data = raw_data.get('work_orders', {})

    if isinstance(deals_data, dict) and deals_data.get('success') is False:
        raise ValueError(deals_data.get('error', 'Failed to fetch deals from Monday.com'))
    if isinstance(work_orders_data, dict) and work_orders_data.get('success') is False:
        raise ValueError(work_orders_data.get('error', 'Failed to fetch work orders from Monday.com'))

    processed_data = data_processor.process_all(raw_data)
    if not isinstance(processed_data, dict):
        raise ValueError('Data processing failed')

    global data_cache
    data_cache = processed_data
    return data_cache


@app.route('/', methods=['GET'])
def index():
    """Application status endpoint."""
    logger.debug('GET / called')
    return jsonify({
        'project': 'Monday BI Agent',
        'status': 'running',
        'version': '1.0'
    }), 200


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint for backend and Monday API."""
    logger.debug('GET /health called')
    return jsonify({
        'status': 'healthy',
        'monday_api': get_monday_status()
    }), 200


@app.route('/refresh', methods=['GET'])
def refresh():
    """Fetch and cache fresh data from Monday.com."""
    logger.info('GET /refresh called - refreshing data')
    try:
        processed_data = refresh_cache()
        deals_count = len(processed_data.get('deals', {}).get('items', []))
        work_orders_count = len(processed_data.get('work_orders', {}).get('items', []))
        logger.info('Data refreshed: %s deals, %s work orders', deals_count, work_orders_count)
        return jsonify({
            'status': 'success',
            'deals': deals_count,
            'work_orders': work_orders_count
        }), 200

    except ValueError as e:
        logger.error('Refresh failed: %s', str(e))
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 503

    except Exception as e:
        logger.error('Unexpected refresh error: %s', str(e))
        return jsonify({
            'status': 'error',
            'message': 'Failed to refresh data. Please try again.'
        }), 500


@app.route('/ask', methods=['POST'])
def ask():
    """Answer natural language business questions."""
    logger.info('POST /ask called')
    if not request.is_json:
        logger.warning('Invalid request format (not JSON)')
        return jsonify({
            'status': 'error',
            'message': 'Request must be JSON'
        }), 400

    payload = request.get_json(silent=True)
    if not payload or not isinstance(payload, dict):
        logger.warning('Invalid JSON payload')
        return jsonify({
            'status': 'error',
            'message': 'Invalid JSON payload'
        }), 400

    question = str(payload.get('question', '')).strip()
    if not question:
        logger.warning('Empty question provided')
        return jsonify({
            'status': 'error',
            'message': 'Question cannot be empty'
        }), 400

    try:
        if not data_cache.get('deals') or not data_cache.get('work_orders'):
            logger.info('Cache empty, auto-refreshing data for ask')
            refresh_cache()

        response = ai_agent.answer(question, data_cache)
        logger.info('Response generated with intent: %s', response.get('intent'))
        return jsonify({
            'question': question,
            'intent': response.get('intent'),
            'answer': response.get('response')
        }), 200

    except ValueError as e:
        logger.error('Ask endpoint failed: %s', str(e))
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 503

    except Exception as e:
        logger.error('Unexpected ask error: %s', str(e))
        return jsonify({
            'status': 'error',
            'message': 'Unable to process your question. Please try again.'
        }), 500


@app.route('/summary', methods=['GET'])
def summary():
    """Return leadership summary for the current cached business data."""
    logger.info('GET /summary called')
    try:
        if not data_cache.get('deals') or not data_cache.get('work_orders'):
            logger.info('Cache empty, auto-refreshing data for summary')
            refresh_cache()

        summary_text = business_analyzer.leadership_summary(data_cache)
        logger.info('Leadership summary generated')
        return jsonify({
            'summary': summary_text
        }), 200

    except ValueError as e:
        logger.error('Summary failed: %s', str(e))
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 503

    except Exception as e:
        logger.error('Unexpected summary error: %s', str(e))
        return jsonify({
            'status': 'error',
            'message': 'Unable to generate summary. Please try again.'
        }), 500


@app.errorhandler(404)
def not_found(error):
    logger.debug('404 error: %s', request.path)
    return jsonify({
        'status': 'error',
        'message': 'Endpoint not found'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error('500 error: %s', str(error))
    return jsonify({
        'status': 'error',
        'message': 'Internal server error'
    }), 500


if __name__ == '__main__':
    logger.info('Starting Monday BI Agent Flask application...')
    
    # Pre-load cache on startup to ensure data is available for all requests
    try:
        logger.info('Pre-loading data cache at startup...')
        processed_data = refresh_cache()
        deals_count = len(processed_data.get('deals', {}).get('items', []))
        work_orders_count = len(processed_data.get('work_orders', {}).get('items', []))
        logger.info('Cache pre-loaded successfully: %s deals, %s work orders', 
                   deals_count, work_orders_count)
    except Exception as e:
        logger.warning('Could not pre-load cache at startup: %s', str(e))
        logger.info('Cache will be loaded on first request instead')
    
    app.run(
        host='127.0.0.1',
        port=app.config['PORT'],
        debug=app.config['DEBUG']
    )
