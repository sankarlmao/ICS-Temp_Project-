from flask import Flask, jsonify, send_from_directory
import os
import requests

app = Flask(__name__)
LOGGER_URL = "http://logger:8000/log"

def log_to_service(message):
    try:
        requests.post(LOGGER_URL, json={"source": "dmz-webserver", "message": message}, timeout=1)
    except:
        pass

@app.before_request
def log_request():
    from flask import request
    log_to_service(f"Request: {request.method} {request.path} from {request.remote_addr}")

@app.route('/')
def home():
    return "<h1>Power Grid Management Portal</h1><p>Welcome to the internal monitoring dashboard. Access restricted.</p>"

@app.route('/static/config.json')
def get_config():
    # Simulate a vulnerability: exposed credentials in a config file
    config = {
        "user": "operator",
        "pass": "grid_op_2026",
        "scada_api": "modbus://scada-server:502"
    }
    return jsonify(config)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
