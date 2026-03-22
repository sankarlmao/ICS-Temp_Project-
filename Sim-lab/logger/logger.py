from flask import Flask, request, jsonify
import datetime

app = Flask(__name__)
LOG_FILE = "/var/log/scada_lab.log"

@app.route('/log', methods=['POST'])
def receive_log():
    data = request.json
    source = data.get('source', 'unknown')
    message = data.get('message', '')
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] [{source}] {message}\n")
    
    return jsonify({"status": "logged"})

@app.route('/view')
def view_logs():
    try:
        with open(LOG_FILE, "r") as f:
            content = f.read()
        return f"<pre>{content}</pre>"
    except FileNotFoundError:
        return "No logs yet."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
