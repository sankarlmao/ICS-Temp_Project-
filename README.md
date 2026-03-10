# Ukraine Power Grid Attack - Lab

- **it_workstation**: Compromised via stolen credentials (port 2222, employee:password123).
- **scada_server**: Isolated OT network controlling the grid.

## Attack
1. SSH to IT: `ssh -p 2222 employee@localhost`
2. Recon: `curl http://scada_server:8080`
3. Blackout: `curl http://scada_server:8080/turn_off_power`
4. Wipe: `curl http://scada_server:8080/wipe_system`

## Defense
1. Fix `it_workstation/Dockerfile` password.
2. Secure `scada_server/server.py` with auth.
3. Segment networks properly.
