from flask import Flask, jsonify
app = Flask(__name__)
grid_status = "ONLINE"
@app.route('/')
def index(): return jsonify({"system": "SCADA Node", "status": grid_status, "actions": ["/turn_off_power", "/wipe_system"]})
@app.route('/turn_off_power')
def turn_off_power():
    global grid_status
    grid_status = "OFFLINE - BLACKOUT"
    return jsonify({"message": "Power disconnected.", "status": grid_status})
@app.route('/wipe_system')
def wipe_system():
    global grid_status
    grid_status = "CORRUPTED - UNRECOVERABLE"
    return jsonify({"message": "Drives wiped.", "status": grid_status})
if __name__ == '__main__': app.run(host='0.0.0.0', port=8080)
