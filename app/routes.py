"""Main routes for sangre-signal web interface."""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
import datetime
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired, Regexp
from flask_wtf import FlaskForm
import logging

# Import sangre-signal modules
try:
    from sangre_signal.cli import run_for_tickers, normalize_tickers
    from sangre_signal.formatters import get_formatter
    from sangre_signal.models import StockInfo, RiskAnalysis
    from sangre_signal.cache import get_cache
except ImportError as e:
    logging.error(f"Failed to import sangre_signal: {e}")
    # Fallback for development without sangre_signal installed
    run_for_tickers = None
    normalize_tickers = None
    get_formatter = None
    get_cache = None

logger = logging.getLogger(__name__)

# Create blueprint
main_bp = Blueprint('main', __name__)


class TickerForm(FlaskForm):
    """Form for entering stock tickers."""
    tickers = StringField(
        'Stock Tickers',
        validators=[
            DataRequired(message='Please enter at least one ticker'),
            Regexp(r'^[A-Z,\s]+$', message='Only uppercase letters, commas, and spaces allowed')
        ],
        description='Enter ticker symbols separated by commas (e.g., AAPL, GOOG, MSFT)'
    )
    
    format = SelectField(
        'Output Format',
        choices=[
            ('text', 'Text (Colored)'),
            ('json', 'JSON'),
            ('csv', 'CSV'),
            ('claude', 'Claude AI Analysis'),
            ('perplexity', 'Perplexity AI Analysis')
        ],
        default='text'
    )
    
    submit = SubmitField('Analyze')


@main_bp.route('/')
def index():
    """Home page with ticker input form."""
    form = TickerForm()
    return render_template('index.html', form=form)


@main_bp.route('/analyze', methods=['POST'])
def analyze():
    """Analyze stock tickers and display results."""
    form = TickerForm()
    
    if not form.validate_on_submit():
        flash('Please correct the errors in the form.', 'error')
        return render_template('index.html', form=form)
    
    if run_for_tickers is None:
        flash('sangre_signal module is not available. Please install dependencies.', 'error')
        return render_template('index.html', form=form)
    
    try:
        # Get form data
        ticker_input = form.tickers.data.upper()
        output_format = form.format.data
        
        # Normalize tickers
        tickers = normalize_tickers([ticker_input])
        
        if not tickers:
            flash('No valid tickers provided.', 'error')
            return render_template('index.html', form=form)
        
        logger.info(f"Analyzing tickers: {tickers}")
        
        # Run analysis using sangre-signal
        success = run_for_tickers(
            tickers,
            output_format=output_format,
            language='en'
        )
        
        if success:
            flash(f'Successfully analyzed {len(tickers)} ticker(s).', 'success')
            return render_template('results.html', 
                                 tickers=tickers, 
                                 format=output_format)
        else:
            flash('Failed to analyze tickers. Please check the ticker symbols.', 'error')
            return render_template('index.html', form=form)
            
    except Exception as e:
        logger.exception(f"Error analyzing tickers: {e}")
        flash(f'An error occurred: {str(e)}', 'error')
        return render_template('index.html', form=form)


@main_bp.route('/api/analyze', methods=['GET', 'POST'])
def api_analyze():
    """API endpoint for stock analysis."""
    if get_formatter is None or run_for_tickers is None:
        return jsonify({
            'error': 'sangre_signal module is not available',
            'success': False
        }), 500
    
    try:
        # Handle both GET and POST requests
        if request.method == 'GET':
            tickers = request.args.get('tickers', '').upper()
            output_format = request.args.get('format', 'json')
        else:
            data = request.get_json() or {}
            tickers = data.get('tickers', '').upper()
            output_format = data.get('format', 'json')
        
        if not tickers:
            return jsonify({
                'error': 'No tickers provided',
                'success': False
            }), 400
        
        # Normalize tickers
        ticker_list = normalize_tickers([tickers])
        
        if not ticker_list:
            return jsonify({
                'error': 'No valid tickers provided',
                'success': False
            }), 400
        
        # Get JSON formatter for API response
        json_formatter = get_formatter('json', language='en')
        
        # Run analysis and capture output
        import io
        import sys
        from contextlib import redirect_stdout
        
        # Capture stdout to get the JSON output
        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            success = run_for_tickers(
                ticker_list,
                output_format='json',
                language='en'
            )
        
        if success:
            json_output = captured_output.getvalue()
            return jsonify({
                'success': True,
                'data': json_output,
                'tickers': ticker_list
            })
        else:
            return jsonify({
                'error': 'Failed to analyze tickers',
                'success': False
        }), 500

    except Exception as e:
        logger.exception(f"API error: {e}")
        return jsonify({
            'error': str(e),
            'success': False
        }), 500


@main_bp.route('/health')
def health():
    """Health check endpoint for container verification."""
    try:
        # Check if we can import sangre_signal
        import sangre_signal
        module_available = True
    except ImportError:
        module_available = False

    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.datetime.now().isoformat(),
        'module_available': module_available
    })


@main_bp.route('/status')
def status():
    """Display cache and rate limit status."""
    if get_cache is None:
        flash('sangre_signal module is not available.', 'error')
        return redirect(url_for('main.index'))
    
    try:
        cache = get_cache()
        status_info = cache.get_rate_limit_status()
        
        return render_template('status.html', status=status_info, cache=cache)
        
    except Exception as e:
        logger.exception(f"Error getting status: {e}")
        flash(f'Error getting status: {str(e)}', 'error')
        return redirect(url_for('main.index'))


@main_bp.route('/api/status')
def api_status():
    """API endpoint for cache and rate limit status."""
    if get_cache is None:
        return jsonify({
            'error': 'sangre_signal module is not available',
            'success': False
        }), 500
    
    try:
        cache = get_cache()
        status_info = cache.get_rate_limit_status()
        
        return jsonify({
            'success': True,
            'status': status_info,
            'cache_info': {
                'db_path': str(cache.db_path),
                'ttl_hours': cache.ttl / 3600
            }
        })
        
    except Exception as e:
        logger.exception(f"API status error: {e}")
        return jsonify({
            'error': str(e),
            'success': False
        }), 500


@main_bp.route('/health')
def health_check():
    """Health check endpoint for container verification."""
    try:
        # Check if we can import sangre_signal
        import sangre_signal
        module_available = True
    except ImportError:
        module_available = False
    
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.datetime.now().isoformat(),
        'module_available': module_available
    })