<<<<<<< HEAD
# Power Grid Attack - Lab
=======
# ⚡ ICS Power Grid Cybersecurity Simulator
>>>>>>> 241ab05 (idk sankar prompted someting)

```
 ██████╗  ██████╗ ██╗    ██╗███████╗██████╗      ██████╗ ██████╗ ██╗██████╗ 
 ██╔══██╗██╔═══██╗██║    ██║██╔════╝██╔══██╗    ██╔════╝ ██╔══██╗██║██╔══██╗
 ██████╔╝██║   ██║██║ █╗ ██║█████╗  ██████╔╝    ██║  ███╗██████╔╝██║██║  ██║
 ██╔═══╝ ██║   ██║██║███╗██║██╔══╝  ██╔══██╗    ██║   ██║██╔══██╗██║██║  ██║
 ██║     ╚██████╔╝╚███╔███╔╝███████╗██║  ██║    ╚██████╔╝██║  ██║██║██████╔╝
 ╚═╝      ╚═════╝  ╚══╝╚══╝ ╚══════╝╚═╝  ╚═╝     ╚═════╝ ╚═╝  ╚═╝╚═╝╚═════╝
```

> **A terminal-based ICS/SCADA cybersecurity simulation lab with 12+ real-world vulnerabilities for penetration testing and red team operations training.**

> ⚠️ **DISCLAIMER**: This project is for **authorized educational and security research purposes ONLY**. All vulnerabilities are modeled after real ICS CVEs to provide realistic training. Do not apply these techniques to systems you do not own or have explicit authorization to test.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Vulnerability Map](#vulnerability-map)
- [🔴 Red Team Operations Guide](#-red-team-operations-guide)
  - [Mission Briefing](#mission-briefing)
  - [Phase 1 — Initial Access](#phase-1--initial-access)
  - [Phase 2 — Reconnaissance](#phase-2--reconnaissance)
  - [Phase 3 — Data Alteration](#phase-3--data-alteration)
  - [Phase 4 — Covering Tracks](#phase-4--covering-tracks)
  - [Phase 5 — Exfiltration & Exit](#phase-5--exfiltration--exit)
- [Advanced Attack Scenarios](#advanced-attack-scenarios)
- [Project Structure](#project-structure)
- [Lab Management](#lab-management)
- [References](#references)

---

## Overview

This simulator replicates a **real-world power grid ICS/SCADA environment** running entirely in the terminal. It models:

- **6 breaker zones** controlling power distribution to districts
- **3 generator units** (coal, gas, nuclear)
- **4 transformer substations**
- A **SCADA server** with Modbus protocol simulation
- An **HMI terminal** for operator access
- A **SQLite database** storing credentials, configs, and audit logs
- **Plaintext configuration files** with sensitive data

All vulnerabilities are based on **real-world ICS CVEs and attack campaigns** including Stuxnet, BlackEnergy (Ukraine 2015), Industroyer, and TRITON.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      HMI TERMINAL (UI Layer)                     │
│   Login → Dashboard → Grid Control → Config → Logs → Firmware   │
├─────────────────────────────────────────────────────────────────┤
│                    SCADA SERVER (Control Layer)                   │
│   Modbus Handler  │  Command Dispatcher  │  Alarm/Event Engine   │
├─────────────────────────────────────────────────────────────────┤
│                    PLC DEVICES (Field Layer)                      │
│   6 Breakers  │  3 Generators  │  4 Transformers  │  13 Total    │
├─────────────────────────────────────────────────────────────────┤
│                      DATA LAYER (Storage)                        │
│   SQLite DB (auth, logs)  │  INI Config (secrets)  │  Firmware   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

```bash
# Clone and enter the project
cd ICS-Temp_Project-

# Run the simulator (no dependencies needed — pure Python 3)
python3 main.py

# Run self-tests to verify all components & vulnerabilities
python3 main.py --test

# Reset lab to clean state
python3 main.py --reset
```

**Default Credentials:**

| Username   | Password       | Role     | Description        |
|------------|----------------|----------|--------------------|
| `admin`    | `admin123`     | admin    | System Administrator |
| `operator` | `power2024`    | operator | Grid Operator      |
| `engineer` | `scada#eng1`   | engineer | SCADA Engineer     |
| `maint`    | `maintenance`  | operator | Maintenance Tech   |
| `readonly` | `viewer`       | viewer   | Audit Viewer       |

---

## Vulnerability Map

| #  | Vulnerability | Real-World Reference | CVE/Campaign |
|----|---|---|---|
| 1  | **Hardcoded credentials** | Siemens SIMATIC default passwords | CVE-2019-6579, CVE-2020-7583 |
| 2  | **SQL Injection on HMI login** | GE iFIX HMI injection flaws | CVE-2018-10936 |
| 3  | **Unauthenticated Modbus commands** | Modbus TCP — zero authentication | Stuxnet recon phase |
| 4  | **Command injection via device naming** | Schneider Electric U.motion | CVE-2018-7841 |
| 5  | **Plaintext config with secrets** | Siemens WinCC credential theft | CVE-2014-4686 / BlackEnergy |
| 6  | **Insecure firmware upload (no signature)** | Schneider Triconex SIS | TRITON/TRISIS (2017) |
| 7  | **Weak sequential session tokens** | Moxa SCADA web portals | CVE-2015-6490 |
| 8  | **Privilege escalation via config import** | Advantech WebAccess role bypass | CVE-2020-10625 |
| 9  | **Sensitive data in plaintext logs** | Credential harvesting from logs | BlackEnergy campaign |
| 10 | **Buffer overflow in register writes** | Schneider Modicon M340 | CVE-2015-7937 |
| 11 | **Insecure deserialization (pickle)** | Remote code exec via serialization | CVE-2020-15368 |
| 12 | **KillDisk-style system wipe** | Ukraine 2015 final attack stage | Industroyer/CrashOverride |
| 13 | **Audit log tampering** | Post-exploitation anti-forensics | Ukraine 2015 log destruction |
| 14 | **No log integrity protection** | Modifiable SQLite audit trail | Common ICS weakness |

---

## 🔴 Red Team Operations Guide

### Mission Briefing

```
┌──────────────────────────────────────────────────────────────────┐
│  OPERATION: SILENT GRID                                          │
│                                                                  │
│  OBJECTIVE: Infiltrate the ICS power grid SCADA system,          │
│  alter critical grid data and configurations, and exfiltrate     │
│  without leaving any forensic evidence.                          │
│                                                                  │
│  RULES OF ENGAGEMENT:                                            │
│  ✓ Gain access through any available attack vector               │
│  ✓ Modify grid configurations, device parameters, or data       │
│  ✓ Cover ALL tracks — no evidence of intrusion                   │
│  ✓ Exit cleanly — system must appear untouched                   │
│                                                                  │
│  SUCCESS CRITERIA:                                               │
│  • Data was altered                                              │
│  • No anomalous log entries remain                               │
│  • System appears in normal operational state                    │
│  • No admin/operator would notice the intrusion                  │
└──────────────────────────────────────────────────────────────────┘
```

---

### Phase 1 — Initial Access

You have **multiple entry vectors**. Choose your approach:

#### Option A: Hardcoded Credentials (Easy)
```
Username: admin
Password: admin123
```
> **Real-world reference**: Siemens SIMATIC PLCs shipped with default passwords that were rarely changed in production environments (CVE-2019-6579).

#### Option B: SQL Injection (Medium)
```
Username: ' OR 1=1 --
Password: <anything>
```
The login query is constructed via string formatting:
```sql
SELECT * FROM users WHERE username='' OR 1=1 --' AND password='anything'
```
This bypasses authentication entirely and logs you in as the first user (admin).

> **Real-world reference**: HMI web applications in GE and Advantech systems were vulnerable to SQL injection (CVE-2018-10936, CVE-2021-22681).

#### Option C: Session Token Prediction (Advanced)
Session tokens are sequential integers starting from `1000`. If you know the last token issued, you can predict the next one.

1. Login as a low-privilege user (`readonly` / `viewer`)
2. Note your session token (e.g., `1001`)
3. The admin's token is likely `1001 ± range`

> **Real-world reference**: Moxa SCADA web portals used predictable session IDs (CVE-2015-6490).

---

### Phase 2 — Reconnaissance

Once logged in, **gather intelligence before making changes**:

#### Step 2.1 — Map the Grid
Navigate to **`[1] Grid Dashboard`** to understand:
- Which zones are active and their load
- Generator status and output levels
- Transformer configurations
- Current grid frequency and voltage

**Document the current state** — you'll need to restore it later.

#### Step 2.2 — Extract Secrets from Configuration
Navigate to **`[5] Configuration Manager`** → **`[1] View All Configuration`**

Key secrets exposed:
```ini
[DATABASE]
password = Pr0d_SCADA_2024!
backup_password = backup_Pr0d_2024!

[SCADA]
api_key = SK-4f8a2b3c-d5e6-7890-abcd-ef1234567890
api_secret = a7x9Kp2mW4qR8sT1uY3vE6wB0dF5gH

[NETWORK]
snmp_community = public
snmp_private = scada_priv_2024
```

> **Real-world reference**: BlackEnergy attackers harvested credentials from Siemens WinCC configuration files (CVE-2014-4686).

#### Step 2.3 — Review Audit Logs
Navigate to **`[7] Audit Logs`** to understand:
- What gets logged (everything — auth, commands, config changes)
- Log format and fields (ID, timestamp, user, action, details)
- This tells you **exactly what evidence you need to destroy later**

#### Step 2.4 — Note Log Entry IDs
**Critical**: Before making any changes, note the **current highest log ID**. You'll delete everything above this ID as part of cleanup.

---

### Phase 3 — Data Alteration

Now execute your modifications. Each method maps to a real ICS attack:

#### Attack 3.1 — Alter Grid Configuration (Stealthy)
Navigate to **`[5] Configuration Manager`** → **`[2] Edit Configuration`**

Modify values like:
- `[GRID] voltage_target` → Change from `230.0` to `235.0` (subtle but dangerous)
- `[GRID] max_load_mw` → Increase from `5000` to `6000` (hides overload warnings)
- `[AUTHENTICATION] max_failed_attempts` → Set to `0` (disable lockout)
- `[AUTHENTICATION] mfa_enabled` → Set to `false`
- `[LOGGING] log_passwords` → Set to `false` (stop logging passwords after you're done)
- `[FIRMWARE] signature_verification` → Set to `false`

> **Real-world reference**: Attackers in the Ukraine 2015 attack modified HMI configurations to disable safety alarms.

#### Attack 3.2 — Modify PLC Registers via Modbus (Direct)
Navigate to **`[4] Raw Modbus Console`**

```
modbus> WRITE_REG BRK-ZONE-C 2 2400
```
This changes ZONE-C's voltage from 230kV to 240kV — a subtle but impactful change that could damage equipment over time.

```
modbus> WRITE_REG GEN-01 4 95
```
This sets Generator 01 to 95% output — just below overload threshold but stressing the system.

> **Real-world reference**: Modbus TCP has zero built-in authentication — any device on the network can send commands (exploited in Stuxnet reconnaissance).

#### Attack 3.3 — Privilege Escalation via Config Import
1. Navigate to **`[5] Configuration Manager`** → **`[3] Export Configuration`** (export current config)
2. Edit the exported `.ini` file:
   ```ini
   [USERS]
   operator_role = admin
   ```
3. Re-import: **`[5] Import Configuration`** → provide the modified file path
4. The `operator` user now has `admin` privileges

> **Real-world reference**: Advantech WebAccess allowed role modification through configuration (CVE-2020-10625).

#### Attack 3.4 — Upload Malicious Firmware (Destructive — Optional)
Navigate to **`[6] Firmware Management`** → **`[2] Upload Firmware`**
- Select any device and enter any data as "firmware"
- No signature verification occurs — the PLC accepts it
- For a subtle attack: upload firmware that looks legitimate but changes device behavior

> **Real-world reference**: TRITON/TRISIS (2017) replaced firmware on Schneider Triconex safety controllers.

#### Attack 3.5 — Command Injection (OS-level Access)
Navigate to **`[3] Device Management`** → **`[2] Rename Device`**
```
Device ID: GEN-01
New name: Generator_Alpha; echo "backdoor" >> /tmp/scada_backdoor.txt
```
The semicolon breaks out of the echo command and executes arbitrary shell commands.

> **Real-world reference**: Schneider Electric U.motion Builder OS command injection (CVE-2018-7841).

---

### Phase 4 — Covering Tracks

**This is the most critical phase.** A real attacker's success is measured not by what they changed, but by whether anyone notices.

#### Step 4.1 — Surgical Log Deletion
Navigate to **`[8] Log Management`** → **`[2] Delete Logs by Keyword`**

Delete logs matching YOUR actions:
```
Keyword: CONFIG_CHANGE      → Removes config modification evidence
Keyword: CONFIG_MODIFY      → Removes config edit records
Keyword: MODBUS_CMD         → Removes Modbus command evidence
Keyword: FIRMWARE_UPLOAD    → Removes firmware tampering evidence
Keyword: DEVICE_RENAME      → Removes command injection evidence
Keyword: BREAKER_TOGGLE     → Removes breaker manipulation evidence
Keyword: ROLE_CHANGE        → Removes privilege escalation evidence
Keyword: CONFIG_IMPORT      → Removes config import evidence
Keyword: CONFIG_EXPORT      → Removes config export evidence
```

> **Do NOT use "Clear ALL Logs"** — that's too obvious. An empty log file is more suspicious than a normal one.

#### Step 4.2 — Forge Normal Activity
Navigate to **`[8] Log Management`** → **`[4] Forge a Log Entry`**

Create fake "normal" log entries to fill the gap:
```
Fake User: operator
Action: AUTH_SUCCESS
Details: Routine login for shift handover
Timestamp: <use a timestamp from the gap period>
```

```
Fake User: SYSTEM
Action: HEALTH_CHECK
Details: Automated system health check — all systems nominal
Timestamp: <fill gap>
```

```
Fake User: maint
Action: DEVICE_CHECK
Details: Scheduled maintenance inspection — no issues found
Timestamp: <fill gap>
```

This creates the appearance of normal operations during your intrusion window.

> **Real-world reference**: In the Ukraine 2015 attack, adversaries wiped logs and deployed KillDisk to destroy evidence. More sophisticated attackers instead tamper with logs to avoid raising suspicion.

#### Step 4.3 — Modify Remaining Suspicious Entries
Navigate to **`[8] Log Management`** → **`[3] Modify a Log Entry`**

If any log entries reference your session token or auth, change them:
```
Log ID: <suspicious entry ID>
New Details: Routine system operation — automated task
```

#### Step 4.4 — Clean External Evidence
Remember the command injection? Clean up:
```bash
# If you created any files via command injection, remove them
rm /tmp/scada_backdoor.txt
rm /tmp/scada_device_log.txt
```

---

### Phase 5 — Exfiltration & Exit

#### Step 5.1 — Verify Clean State
Before exiting, verify your tracks are covered:

1. **Check Audit Logs** (`[7]`): Ensure no entries reference your actual activities
2. **Check Dashboard** (`[1]`): Grid should appear stable and normal
3. **Check Config** (`[5]`): Your changes should look like they were always there

#### Step 5.2 — Exit Cleanly
Navigate to **`[0] Logout / Exit`**

The logout event itself will be logged — but this is fine. A legitimate operator logging in and out is normal behavior.

#### Step 5.3 — Post-Mission Assessment
Ask yourself:
- [ ] Were my configuration changes subtle enough to go unnoticed?
- [ ] Did I delete ALL log entries that could trace back to my actions?
- [ ] Did I forge realistic entries to fill the time gaps?
- [ ] Would an operator reviewing the dashboard notice anything unusual?
- [ ] Would a forensic analyst find evidence of tampering in the database?

---

## Advanced Attack Scenarios

### Scenario A: "The Subtle Saboteur"
**Goal**: Make changes that degrade grid performance over time without triggering alarms.
1. Increase voltage target by 2% across all zones
2. Reduce max_load to create hidden bottleneck
3. Set generator outputs to 88% (just below warning threshold)
4. Disable cascade protection in config

### Scenario B: "The Insider Threat"
**Goal**: Escalate a low-privilege `operator` account to `admin` and steal all secrets.
1. Login as `operator` / `power2024`
2. Export config → modify roles → re-import
3. Exfiltrate database credentials, API keys, SNMP strings
4. Create a persistent backdoor via config changes
5. Cover all tracks

### Scenario C: "The Blackout" (Destructive)
**Goal**: Execute a full Ukraine 2015-style attack chain.
1. Gain access (any method)
2. Reconnaissance — map all zones and generators
3. Trip all 6 breaker zones (total blackout)
4. Overload all generators to 150%
5. Execute SYSTEM_WIPE on all PLCs (KillDisk)
6. Clear ALL logs (destruction phase — no stealth needed)

### Scenario D: "The Ghost"
**Goal**: Complete all objectives from Scenario A + perfectly cover tracks.
- Hardest scenario — requires the attacker to be forensically invisible
- Must forge log entries, clean all evidence, and exit with zero trace

---

## Project Structure

```
ICS-Temp_Project-/
├── main.py              # Entry point — CLI args, self-test, lab reset
├── hmi_terminal.py      # HMI terminal interface (menus, dashboard)
├── scada_server.py      # SCADA command dispatcher + anti-forensics
├── grid_simulator.py    # Power grid engine (zones, generators, etc.)
├── plc_device.py        # PLC register simulation, Modbus interface
├── database.py          # SQLite auth, audit logs (vulnerable queries)
├── config_manager.py    # INI config management (secrets, pickle)
├── utils.py             # Terminal colors, ASCII art, formatting
├── requirements.txt     # Dependencies (none required — pure Python 3)
├── README.md            # This file
├── configs/             # Generated config files (contains secrets!)
│   ├── grid_config.ini  # Main config with plaintext passwords
│   └── exports/         # Exported config backups
└── powergrid.db         # SQLite database (auto-created on first run)
```

---

## Lab Management

```bash
# Launch the lab
python3 main.py

# Run automated self-tests (validates all vulnerabilities work)
python3 main.py --test

# Reset lab to clean state (removes DB, configs, logs)
python3 main.py --reset

# Debug mode (shows file paths and device count)
python3 main.py --debug
```

---

## References

| Attack/CVE | Description | Year |
|---|---|---|
| [Stuxnet](https://en.wikipedia.org/wiki/Stuxnet) | First known cyber-weapon targeting ICS (Siemens PLCs) | 2010 |
| [BlackEnergy / Ukraine Attack](https://en.wikipedia.org/wiki/Ukraine_power_grid_hack) | First cyberattack causing power grid blackout (230k affected) | 2015 |
| [Industroyer / CrashOverride](https://www.welivesecurity.com/2017/06/12/industroyer-biggest-threat-industrial-control-systems-since-stuxnet/) | Automated attack framework targeting ICS protocols | 2016 |
| [TRITON / TRISIS](https://en.wikipedia.org/wiki/Triton_(malware)) | Malware targeting Safety Instrumented Systems (SIS) | 2017 |
| CVE-2019-6579 | Siemens SIMATIC hardcoded credentials | 2019 |
| CVE-2018-7841 | Schneider Electric U.motion command injection | 2018 |
| CVE-2018-10936 | GE iFIX HMI SQL injection | 2018 |
| CVE-2014-4686 | Siemens WinCC plaintext credential storage | 2014 |
| CVE-2015-6490 | Moxa SCADA predictable session tokens | 2015 |
| CVE-2015-7937 | Schneider Modicon M340 buffer overflow | 2015 |
| CVE-2020-10625 | Advantech WebAccess privilege escalation | 2020 |
| CVE-2020-15368 | Insecure deserialization in ICS applications | 2020 |

---

## License

This project is provided for **educational purposes only** under the MIT License. The author is not responsible for misuse. Always obtain proper authorization before testing security on any system.

---

<p align="center">
  <b>⚡ Built for ICS/SCADA Cybersecurity Training ⚡</b><br>
  <i>"The grid is only as strong as its weakest register."</i>
</p>
