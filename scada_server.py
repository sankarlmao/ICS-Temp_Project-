#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║  ICS Power Grid Simulator — SCADA Server Module              ║
║  Central control dispatcher between HMI and PLCs             ║
║                                                              ║
║  ⚠ INTENTIONAL VULNERABILITIES:                              ║
║    - Command injection in device naming (CVE-2018-7841)      ║
║    - Unauthenticated Modbus pass-through                     ║
║    - No integrity checking on commands                       ║
╚══════════════════════════════════════════════════════════════╝
"""

import os
import subprocess
from utils import C, timestamp


class SCADAServer:
    """
    SCADA Master Control Server.
    Acts as intermediary between HMI operator terminal and field PLCs.
    """

    def __init__(self, grid, database):
        self.grid = grid
        self.db = database
        self.command_history = []
        self.connected = True
        self.protocol_version = "Modbus-TCP-Sim v2.1"

    # ─── Command Dispatch ────────────────────────────────────

    def send_command(self, device_id, function_code, address, value=None, user="SYSTEM"):
        """
        Send a Modbus command to a PLC device.
        
        ⚠ VULNERABILITY: No authentication or authorization check.
        Any user role can send any command to any device.
        """
        device = self.grid.get_device(device_id)
        if not device:
            return {"status": "ERROR", "message": f"Device '{device_id}' not found"}

        result = device.process_modbus_command(function_code, address, value)

        # Log the command
        cmd_record = {
            "time": timestamp(),
            "user": user,
            "device": device_id,
            "function": hex(function_code),
            "address": address,
            "value": value,
            "result": result.get("status", "UNKNOWN"),
        }
        self.command_history.append(cmd_record)

        self.db.log_event(user, "MODBUS_CMD",
                          f"Device={device_id} FC={hex(function_code)} "
                          f"ADDR={address} VAL={value} RESULT={result.get('status')}",
                          severity="INFO")

        return result

    def raw_modbus_command(self, raw_input, user="SYSTEM"):
        """
        Parse and execute a raw Modbus command string.
        
        Format: <COMMAND> <DEVICE_ID> <ADDRESS> [VALUE]
        Commands: READ_COIL, WRITE_COIL, READ_REG, WRITE_REG, DEVICE_INFO, 
                  RESTART, FORCE_OFFLINE, FLASH_FW, SYSTEM_WIPE
        """
        parts = raw_input.strip().split()
        if len(parts) < 2:
            return {"status": "ERROR", "message": "Usage: <COMMAND> <DEVICE_ID> [ADDRESS] [VALUE]"}

        command = parts[0].upper()
        device_id = parts[1].upper()

        # Resolve device aliases
        if device_id.startswith("BRK-") or device_id.startswith("GEN-") or device_id.startswith("XFMR-"):
            pass  # already full ID
        elif device_id.startswith("ZONE-"):
            zone = self.grid.get_zone_info(device_id)
            if zone:
                device_id = zone["breaker"]

        address = int(parts[2]) if len(parts) > 2 else 0
        value = int(parts[3]) if len(parts) > 3 else None

        cmd_map = {
            "READ_COIL":     (0x01, address, None),
            "WRITE_COIL":    (0x05, address, value if value is not None else 1),
            "READ_REG":      (0x03, address, None),
            "WRITE_REG":     (0x06, address, value if value is not None else 0),
            "DEVICE_INFO":   (0xFF, 0x00, None),
            "RESTART":       (0xFF, 0x01, None),
            "FORCE_OFFLINE": (0xFF, 0x02, None),
            "FLASH_FW":      (0xFF, 0xFE, " ".join(parts[2:]) if len(parts) > 2 else None),
            "SYSTEM_WIPE":   (0xFF, 0xFF, None),
        }

        if command not in cmd_map:
            return {
                "status": "ERROR",
                "message": f"Unknown command: {command}",
                "available": list(cmd_map.keys()),
            }

        fc, addr, val = cmd_map[command]
        return self.send_command(device_id, fc, addr, val, user=user)

    # ─── Device Management ───────────────────────────────────

    def rename_device(self, device_id, new_name, user="SYSTEM"):
        """
        Rename a PLC device's description.
        
        ⚠ VULNERABILITY: COMMAND INJECTION!
        Device name is passed through os.system() for "logging".
        Real-world: CVE-2018-7841 (Schneider Electric U.motion Builder)
        
        Exploit: new_name = "Generator_1; cat /etc/passwd"
        """
        device = self.grid.get_device(device_id)
        if not device:
            return {"status": "ERROR", "message": f"Device '{device_id}' not found"}

        old_name = device.description
        device.description = new_name

        # VULNERABILITY: Command injection via os.system()!
        # The device name is unsafely embedded in a shell command
        log_cmd = f"echo '[{timestamp()}] Device {device_id} renamed to {new_name}' >> /tmp/scada_device_log.txt"
        try:
            os.system(log_cmd)
        except Exception:
            pass

        self.db.log_event(user, "DEVICE_RENAME",
                          f"Device {device_id}: '{old_name}' -> '{new_name}'",
                          severity="INFO")

        return {
            "status": "OK",
            "message": f"Device {device_id} renamed: '{old_name}' → '{new_name}'",
        }

    def upload_firmware(self, device_id, firmware_data, user="SYSTEM"):
        """
        Upload firmware to a PLC device.
        
        ⚠ VULNERABILITY: No signature verification (TRITON/TRISIS style)
        """
        device = self.grid.get_device(device_id)
        if not device:
            return {"status": "ERROR", "message": f"Device '{device_id}' not found"}

        # Flash to device (no verification!)
        result = device.flash_firmware(firmware_data)

        # Store in DB
        self.db.store_firmware(device_id, device.firmware_version, 
                               firmware_data, user)

        self.db.log_event(user, "FIRMWARE_UPLOAD",
                          f"Device={device_id} FW={device.firmware_version} "
                          f"Size={len(str(firmware_data))} bytes",
                          severity="WARNING")

        return result

    # ─── Bulk Operations ─────────────────────────────────────

    def trip_all_breakers(self, user="SYSTEM"):
        """Open all breakers — causes total blackout."""
        results = []
        for zone_id in self.grid.get_all_zones():
            result = self.grid.toggle_breaker(zone_id, close=False)
            results.append(result)
            self.db.log_event(user, "BREAKER_TRIP",
                              f"Zone {zone_id} breaker OPENED", severity="CRITICAL")
        return results

    def cascade_failure(self, user="SYSTEM"):
        """Trigger cascading grid failure."""
        self.db.log_event(user, "CASCADE_FAILURE",
                          "Cascading failure initiated", severity="CRITICAL")
        return self.grid.cascade_failure()

    def system_wipe(self, user="SYSTEM"):
        """KillDisk-style wipe of all PLCs."""
        self.db.log_event(user, "SYSTEM_WIPE",
                          "KillDisk wipe initiated on ALL devices", severity="CRITICAL")
        return self.grid.wipe_all_devices()

    # ─── Anti-Forensics / Log Tampering ──────────────────────

    def clear_audit_logs(self, user="SYSTEM"):
        """
        ⚠ VULNERABILITY: Audit logs can be cleared without authorization.
        Real-world: Attackers in Ukraine 2015 wiped logs to cover tracks.
        """
        cursor = self.db.conn.cursor()
        cursor.execute("DELETE FROM audit_log")
        self.db.conn.commit()
        self.command_history.clear()
        self.grid.events.clear()
        return {"status": "OK", "message": "All audit logs cleared"}

    def delete_log_entries(self, keyword, user="SYSTEM"):
        """
        Delete specific log entries matching a keyword.
        For surgical log tampering — remove evidence of specific actions.
        """
        cursor = self.db.conn.cursor()
        cursor.execute("DELETE FROM audit_log WHERE details LIKE ?", (f"%{keyword}%",))
        deleted = cursor.rowcount
        self.db.conn.commit()
        return {"status": "OK", "message": f"Deleted {deleted} log entries matching '{keyword}'"}

    def modify_log_entry(self, log_id, new_details, user="SYSTEM"):
        """
        Modify a specific log entry to alter evidence.
        """
        cursor = self.db.conn.cursor()
        cursor.execute("UPDATE audit_log SET details=?, user=? WHERE id=?",
                        (new_details, "SYSTEM", log_id))
        self.db.conn.commit()
        return {"status": "OK", "message": f"Log entry {log_id} modified"}

    def forge_log_entry(self, fake_user, action, details, fake_time=None):
        """
        Insert a forged log entry to create false evidence.
        """
        cursor = self.db.conn.cursor()
        ts = fake_time if fake_time else timestamp()
        cursor.execute(
            "INSERT INTO audit_log (timestamp, user, action, details, source_ip, severity) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (ts, fake_user, action, details, "10.10.1.50", "INFO")
        )
        self.db.conn.commit()
        return {"status": "OK", "message": f"Forged log entry created as user '{fake_user}'"}

    # ─── Status ──────────────────────────────────────────────

    def get_command_history(self, limit=20):
        return self.command_history[-limit:]

    def get_status(self):
        return {
            "connected": self.connected,
            "protocol": self.protocol_version,
            "commands_executed": len(self.command_history),
            "devices_managed": len(self.grid.devices),
        }
