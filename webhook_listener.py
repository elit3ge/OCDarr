from flask import Flask, render_template, request, redirect, url_for, jsonify
import subprocess
import os
import logging
import json
import sonarr_utils
from datetime import datetime
from dotenv import load_dotenv

app = Flask(__name__)

# Load environment variables from .env file
load_dotenv()

# Load environment variables
SONARR_URL = os.getenv('SONARR_URL')
MISSING_LOG_PATH = os.getenv('MISSING_LOG_PATH', '/app/logs/missing.log')

# Setup logging to capture all logs
logging.basicConfig(filename=os.getenv('LOG_PATH', '/app/logs/app.log'), 
                    level=logging.DEBUG if os.getenv('FLASK_DEBUG', 'false').lower() == 'true' else logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Adding stream handler to also log to console for Docker logs to capture
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG if os.getenv('FLASK_DEBUG', 'false').lower() == 'true' else logging.INFO)
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
stream_handler.setFormatter(formatter)
app.logger.addHandler(stream_handler)

# Configuration management
config_path = os.path.join(app.root_path, 'config', 'config.json')

def load_config():
    try:
        with open(config_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        default_config = {
            'get_option': 'episode',
            'action_option': 'search',
            'keep_watched': 1,
            'monitor_watched': False,
            'always_keep': []
        }
        save_config(default_config)
        return default_config

def normalize_name(name):
    return ' '.join(word.capitalize() for word in name.replace('_', ' ').split())

def save_config(config):
    with open(config_path, 'w') as file:
        json.dump(config, file, indent=4)

def get_missing_log_content():
    try:
        with open(MISSING_LOG_PATH, 'r') as file:
            return file.read()
    except FileNotFoundError:
        return "No missing entries logged."
    except Exception as e:
        app.logger.error(f"Failed to read missing log: {str(e)}")
        return "Failed to read log."


@app.route('/')
def home():
    config = load_config()
    preferences = sonarr_utils.load_preferences()
    current_series = sonarr_utils.fetch_series_and_episodes(preferences)
    upcoming_premieres = sonarr_utils.fetch_upcoming_premieres(preferences)
    missing_log_content = get_missing_log_content()  # Fetch the missing log content here
    return render_template('index.html', config=config, current_series=current_series, upcoming_premieres=upcoming_premieres, sonarr_url=SONARR_URL, missing_log=missing_log_content)




@app.route('/settings')
def settings():
    config = load_config()
    missing_log_content = get_missing_log_content()
    message = request.args.get('message', '')

    # Debugging: Print or log the content to ensure it's read correctly
    app.logger.debug(f"Missing Log Content: {missing_log_content}")
    
    # Also check if any specific parameter forces the settings section to be displayed
    show_settings = request.args.get('show_settings', 'false').lower() == 'true'
    
    # Return the rendered template with all necessary variables
    return render_template('index.html', 
                           config=config, 
                           message=message, 
                           missing_log=missing_log_content, 
                           sonarr_url=SONARR_URL, 
                           show_settings=show_settings)


@app.route('/update-settings', methods=['POST'])
def update_settings():
    config = load_config()
    config['get_option'] = request.form.get('get_option')
    config['action_option'] = request.form.get('action_option')
    config['keep_watched'] = request.form.get('keep_watched')
    config['always_keep'] = [normalize_name(name.strip()) for name in request.form.get('always_keep', '').split(',') if name.strip()]
    config['monitor_watched'] = request.form.get('monitor_watched', 'false').lower() == 'true'
    save_config(config)
    return redirect(url_for('home', section='settings', message="Settings updated successfully"))

@app.route('/webhook', methods=['POST'])
def handle_server_webhook():
    app.logger.info("Received POST request from Tautulli")
    data = request.json
    if data:
        app.logger.info(f"Webhook received with data: {data}")
        try:
            with open('/app/temp/data_from_tautulli.json', 'w') as f:
                json.dump(data, f)
            app.logger.info("Data successfully written to data_from_tautulli.json")
            result = subprocess.run(["python3", "/app/servertosonarr.py"], capture_output=True, text=True)
            if result.stderr:
                app.logger.error("Errors from servertosonarr.py: " + result.stderr)
        except Exception as e:
            app.logger.error(f"Failed to handle data or run script: {e}")
            return jsonify({'status': 'error', 'message': str(e)}), 500
        return jsonify({'status': 'success', 'message': 'Script triggered successfully'}), 200
    else:
        return jsonify({'status': 'error', 'message': 'No data received'}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=os.getenv('FLASK_DEBUG', 'false').lower() == 'true')
