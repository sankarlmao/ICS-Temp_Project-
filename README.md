# Ukraine Power Grid Attack - Lab

This lab simulates a complex, realistic attack on an Operational Technology (OT) network, inspired by the Ukraine Power Grid attack.

## Architecture
The lab consists of three segmented networks:
- **Corporate Network**: `corporate_net`
- **DMZ Network**: `dmz_net`
- **OT Network**: `ot_net`

### Services
1. **it_workstation**: A vulnerable employee workstation in the Corporate Network. Compromised via stolen SSH credentials.
2. **firewall**: Acts as a reverse proxy/gateway allowing limited access from Corporate to the HMI in the DMZ.
3. **hmi_server**: A web-based Human Machine Interface in the DMZ. Connects to the SCADA server. Vulnerable to simple SQL injection or weak credentials (`admin:admin123`).
4. **scada_server**: The central control server in the OT network. It acts as a Modbus Master.
5. **plc_device**: A simulated Programmable Logic Controller (PLC) acting as a Modbus Server (port 502) representing the physical power grid infrastructure.

## Attack Path
1. **Initial Access**: SSH into `it_workstation` (`ssh -p 2222 employee@localhost`, password: `password123`).
2. **Lateral Movement**: From the IT workstation, discover and access the `firewall` service which routes to the `hmi_server`. (e.g., `curl http://firewall:80`).
3. **Exploitation**: Exploit the HMI login bypass (e.g. `' OR 1=1`) or use weak credentials.
4. **Impact**: Use the HMI interface to send commands to the SCADA server, which in turn sends Modbus commands to the PLC to cause a blackout (`turn_off_power`) or a catastrophic firmware wipe (`wipe_system`).

## Running the Lab
```bash
docker-compose up --build
```
Access the HMI (if routing allows) or attack from the IT Workstation container.
