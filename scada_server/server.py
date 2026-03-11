from flask import Flask, jsonify
from pymodbus.client import ModbusTcpClient

app = Flask(__name__)
PLC_HOST = 'plc-device'
PLC_PORT = 502

def get_modbus_client():
    return ModbusTcpClient(PLC_HOST, port=PLC_PORT)

@app.route('/')
def index():
    try:
        client = get_modbus_client()
        client.connect()
        result = client.read_holding_registers(0, 1)
        if result.isError():
            status = "ERROR"
        else:
            val = result.registers[0]
            if val == 1: status = "ONLINE"
            elif val == 0: status = "OFFLINE - BLACKOUT"
            elif val == 999: status = "CORRUPTED - UNRECOVERABLE"
            else: status = "UNKNOWN"
        client.close()
    except Exception as e:
        status = "CONNECTION_REFUSED"
    return jsonify({"system": "SCADA Node", "status": status, "actions": ["/turn_off_power", "/wipe_system"]})

@app.route('/turn_off_power')
def turn_off_power():
    try:
        client = get_modbus_client()
        client.connect()
        client.write_register(0, 0)
        client.close()
        return jsonify({"message": "Power disconnected.", "status": "OFFLINE - BLACKOUT"})
    except:
        return jsonify({"message": "Error connecting to PLC."}), 500

@app.route('/wipe_system')
def wipe_system():
    try:
        client = get_modbus_client()
        client.connect()
        client.write_register(0, 999)
        client.close()
        return jsonify({"message": "Drives wiped.", "status": "CORRUPTED - UNRECOVERABLE"})
    except:
        return jsonify({"message": "Error connecting to PLC."}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
