"""
API routes for WikiGraph application
"""

from flask import Blueprint, request, jsonify, current_app
from pathlib import Path
import logging
from config.language_manager import LanguageManager
from app.models import search_articles

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__)

@api_bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'ok'})

@api_bp.route('/languages', methods=['GET'])
def languages():
    """List available languages."""
    available_langs = LanguageManager.list_available_languages()
    return jsonify({'languages': available_langs})

@api_bp.route('/search', methods=['GET'])
def search():
    """
    Search articles endpoint.

    Query parameters:
    - q: Search query (required)
    - lang: Language code (default: pl)
    - limit: Max results (default: 50)
    - offset: Offset for pagination (default: 0)
    """
    try:
        # Get query parameters
        query = request.args.get('q', '').strip()
        lang = request.args.get('lang', current_app.config['DEFAULT_LANGUAGE'])

        # DEBUG: Print what we received
        print(f"DEBUG: Received query='{query}', lang='{lang}', bytes={query.encode('utf-8')}")
        limit_str = request.args.get('limit', '50')
        offset_str = request.args.get('offset', '0')

        # Validate query
        if not query:
            return jsonify({'error': 'Missing required parameter: q'}), 400

        if len(query) < current_app.config['SEARCH_QUERY_MIN_LENGTH']:
            return jsonify({'error': f'Query too short. Minimum length: {current_app.config["SEARCH_QUERY_MIN_LENGTH"]}'}), 400

        if len(query) > current_app.config['SEARCH_QUERY_MAX_LENGTH']:
            return jsonify({'error': f'Query too long. Maximum length: {current_app.config["SEARCH_QUERY_MAX_LENGTH"]}'}), 400

        # Validate language
        available_langs = LanguageManager.list_available_languages()
        if lang not in available_langs:
            return jsonify({'error': f'Unsupported language: {lang}. Available: {available_langs}'}), 400

        # Validate limit and offset
        try:
            limit = int(limit_str)
            offset = int(offset_str)
        except ValueError:
            return jsonify({'error': 'Invalid limit or offset parameter'}), 400

        if limit < 1 or limit > current_app.config['MAX_SEARCH_RESULTS']:
            return jsonify({'error': f'Limit must be between 1 and {current_app.config["MAX_SEARCH_RESULTS"]}'}), 400

        if offset < 0:
            return jsonify({'error': 'Offset must be non-negative'}), 400

        # Perform search
        db_path = current_app.config['DATABASE_PATH']
        results = search_articles(db_path, query, lang, limit, offset)

        logger.info(f"Search: q='{query}', lang='{lang}', results={results['total']}")

        return jsonify(results)

    except Exception as e:
        logger.error(f"Search error: {e}")
        return jsonify({'error': 'Internal server error'}), 500
