from flask import Blueprint, current_app
from datetime import datetime, date
import os
import sys

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.country_utils import get_country_code

filters_bp = Blueprint('filters', __name__)

def init_app(app):
    # Register template filters
    app.jinja_env.filters['datetimeformat'] = format_datetime

def format_currency(value):
    """Format value as Zambian Kwacha (ZMW)"""
    try:
        return f'ZMW {float(value):,.2f}'
    except (ValueError, TypeError):
        return value

# Register the filter
@filters_bp.app_template_filter('zmw')
def zmw_currency_filter(value):
    return format_currency(value)

# This function can be used in Python code
def format_zmw(value):
    return format_currency(value)

def calculate_age(dob):
    """Calculate age from date of birth"""
    if not dob:
        return 'N/A'
    today = datetime.now().date()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

# Register the age filter
@filters_bp.app_template_filter('age')
def age_filter(dob):
    return calculate_age(dob)

# Register the country code filter
@filters_bp.app_template_filter('country_code')
def country_code_filter(country_name):
    return get_country_code(country_name)

def format_datetime(value, format_str='%Y-%m-%d %H:%M'):
    """Format a datetime object or timestamp string."""
    if value is None:
        return ''
    
    if isinstance(value, str):
        try:
            # Try to parse the string as a datetime
            if 'T' in value:
                value = datetime.fromisoformat(value.replace('Z', '+00:00'))
            else:
                value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        except (ValueError, AttributeError):
            return value
    
    if isinstance(value, (datetime, date)):
        return value.strftime(format_str)
    
    return value

# Make the format_datetime function available as a filter
# It's registered with the app in init_app()
