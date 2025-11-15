from app import app, db
from models import Product, ProductCategory, TeamSettings
from sqlalchemy import text
import logging
from datetime import datetime

def get_logs():
    log_file = 'app.log'  # Default log file name
    try:
        # Try to get log file from app config
        if 'LOG_FILE' in app.config:
            log_file = app.config['LOG_FILE']
        
        with open(log_file, 'r') as f:
            # Read last 100 lines of the log file
            return f"<pre>" + "\n".join(f.read().split("\n")[-100:]) + "</pre>"
    except Exception as e:
        return f"<pre>Error reading log file: {str(e)}</pre>"

# Add a test route to view logs
@app.route('/test/logs')
def view_logs():
    return get_logs()

if __name__ == '__main__':
    with app.app_context():
        print(get_logs())
