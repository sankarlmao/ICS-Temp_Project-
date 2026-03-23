#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║  ICS Power Grid Simulator — Database Module                  ║
║  SQLite-based auth, audit logging, and config storage        ║
║                                                              ║
║  ⚠ INTENTIONAL VULNERABILITIES:                              ║
║    - SQL Injection on login (CVE-2018-10936 style)           ║
║    - Plaintext password storage                              ║
║    - Sensitive data in audit logs (BlackEnergy style)         ║
║    - Weak sequential session tokens (CVE-2015-6490)          ║
║    - No parameterized queries in auth                        ║
╚══════════════════════════════════════════════════════════════╝
"""

import sqlite3
import os
import time
import hashlib
from utils import C, timestamp

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "powergrid.db")

# ── VULNERABILITY: Weak sequential session counter ──
_session_counter = 1000


class Database:
    """
    Database layer for the ICS Power Grid Simulator.
    
    Contains INTENTIONAL vulnerabilities for cybersecurity training.
    """

    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row
        self._initialize()

    def _initialize(self):
        """Create tables and seed default data."""
        cursor = self.conn.cursor()

        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'operator',
                full_name TEXT,
                department TEXT,
                last_login TEXT,
                session_token TEXT,
                active INTEGER DEFAULT 1
            )
        """)

        # Audit log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                user TEXT,
                action TEXT NOT NULL,
                details TEXT,
                source_ip TEXT,
                severity TEXT DEFAULT 'INFO'
            )
        """)

        # Grid configuration table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS grid_config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                description TEXT,
                last_modified TEXT
            )
        """)

        # Firmware table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS firmware (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                version TEXT NOT NULL,
                data BLOB,
                uploaded_by TEXT,
                upload_time TEXT,
                checksum TEXT
            )
        """)

        # ── VULNERABILITY: Hardcoded credentials stored in PLAINTEXT ──
        # Real-world: CVE-2019-6579 (Siemens), CVE-2020-7583
        default_users = [
            ("admin",    "admin123",    "admin",    "System Administrator",  "IT Security"),
            ("operator", "power2024",   "operator", "Grid Operator",         "Operations"),
            ("engineer", "scada#eng1",  "engineer", "SCADA Engineer",        "Engineering"),
            ("readonly", "viewer",      "viewer",   "Audit Viewer",          "Compliance"),
            ("maint",    "maintenance", "operator", "Maintenance Tech",      "Field Ops"),
        ]

        for uname, pwd, role, name, dept in default_users:
            try:
                # VULNERABILITY: Passwords stored as PLAINTEXT (not hashed)
                cursor.execute(
                    "INSERT INTO users (username, password, role, full_name, department) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (uname, pwd, role, name, dept)
                )
            except sqlite3.IntegrityError:
                pass  # user already exists

        # Default grid config values
        default_config = [
            ("grid.frequency",        "60.0",     "Grid frequency in Hz"),
            ("grid.voltage_target",   "230.0",    "Target voltage in kV"),
            ("grid.max_load",         "5000",     "Maximum load capacity in MW"),
            ("grid.auto_balance",     "true",     "Automatic load balancing"),
            ("scada.polling_rate",    "5",        "SCADA polling interval in seconds"),
            ("scada.modbus_port",     "502",      "Modbus TCP port"),
            ("scada.api_key",         "SK-4f8a2b3c-d5e6-7890-abcd-ef1234567890", "SCADA API Key"),
            ("db.backup_password",    "backup_Pr0d_2024!", "Database backup encryption key"),
            ("snmp.community_string", "public",   "SNMP community string"),
            ("network.gateway",       "10.10.1.1","OT network gateway IP"),
            ("firmware.update_url",   "http://scada-internal:8080/firmware", "Firmware update server"),
        ]

        for key, value, desc in default_config:
            try:
                cursor.execute(
                    "INSERT INTO grid_config (key, value, description, last_modified) "
                    "VALUES (?, ?, ?, ?)",
                    (key, value, desc, timestamp())
                )
            except sqlite3.IntegrityError:
                pass

        self.conn.commit()

    # ─── Authentication ──────────────────────────────────────

    def authenticate(self, username, password):
        """
        Authenticate a user.
        
        ⚠ VULNERABILITY: SQL INJECTION (CVE-2018-10936 style)
        Uses string formatting instead of parameterized queries.
        Exploit: username = ' OR 1=1 --
        """
        global _session_counter
        cursor = self.conn.cursor()

        # VULNERABLE QUERY — raw string interpolation!
        query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"

        # VULNERABILITY: Log the query with credentials in plaintext
        self.log_event("SYSTEM", "AUTH_ATTEMPT",
                       f"Query: {query}", severity="INFO")

        try:
            cursor.execute(query)
            user = cursor.fetchone()

            if user:
                # VULNERABILITY: Weak sequential session token (CVE-2015-6490)
                _session_counter += 1
                token = str(_session_counter)

                cursor.execute(
                    "UPDATE users SET last_login=?, session_token=? WHERE id=?",
                    (timestamp(), token, user['id'])
                )
                self.conn.commit()

                self.log_event(user['username'], "AUTH_SUCCESS",
                               f"Session token: {token}, Role: {user['role']}")

                return dict(user), token

            self.log_event(username, "AUTH_FAILURE",
                           f"Failed login — password: {password}", severity="WARNING")
            return None, None

        except sqlite3.OperationalError as e:
            # SQL injection may trigger errors — log them too
            self.log_event("SYSTEM", "SQL_ERROR",
                           f"Error: {e} | Query: {query}", severity="ERROR")
            return None, None

    def validate_session(self, token):
        """Validate a session token. VULNERABILITY: Sequential and guessable."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE session_token=?", (token,))
        user = cursor.fetchone()
        return dict(user) if user else None

    # ─── User Management ─────────────────────────────────────

    def get_user(self, username):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def list_users(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, username, role, full_name, department, last_login, active FROM users")
        return [dict(r) for r in cursor.fetchall()]

    def update_user_role(self, username, new_role):
        """
        VULNERABILITY: No authorization check — anyone can escalate privileges.
        Real-world: CVE-2020-10625 (Advantech WebAccess)
        """
        cursor = self.conn.cursor()
        cursor.execute("UPDATE users SET role=? WHERE username=?", (new_role, username))
        self.conn.commit()
        self.log_event("SYSTEM", "ROLE_CHANGE",
                       f"User '{username}' role changed to '{new_role}'", severity="WARNING")

    # ─── Audit Logging ───────────────────────────────────────

    def log_event(self, user, action, details="", source_ip="127.0.0.1", severity="INFO"):
        """
        Log an audit event.
        
        ⚠ VULNERABILITY: Sensitive data logged in plaintext
        (passwords, session tokens, SQL queries).
        Real-world: BlackEnergy credential harvesting technique.
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO audit_log (timestamp, user, action, details, source_ip, severity) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (timestamp(), user, action, details, source_ip, severity)
        )
        self.conn.commit()

    def get_audit_logs(self, limit=50):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM audit_log ORDER BY id DESC LIMIT ?", (limit,)
        )
        return [dict(r) for r in cursor.fetchall()]

    def get_critical_logs(self):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM audit_log WHERE severity IN ('ERROR', 'CRITICAL') ORDER BY id DESC LIMIT 30"
        )
        return [dict(r) for r in cursor.fetchall()]

    # ─── Grid Configuration ──────────────────────────────────

    def get_config(self, key):
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM grid_config WHERE key=?", (key,))
        row = cursor.fetchone()
        return row['value'] if row else None

    def get_all_config(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM grid_config ORDER BY key")
        return [dict(r) for r in cursor.fetchall()]

    def set_config(self, key, value, user="SYSTEM"):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO grid_config (key, value, last_modified) VALUES (?, ?, ?)",
            (key, value, timestamp())
        )
        self.conn.commit()
        self.log_event(user, "CONFIG_CHANGE",
                       f"Key '{key}' set to '{value}'", severity="WARNING")

    # ─── Firmware ────────────────────────────────────────────

    def store_firmware(self, device_id, version, data, uploaded_by):
        """
        VULNERABILITY: No signature verification on firmware upload.
        Real-world: TRITON/TRISIS attack on Schneider Triconex (2017)
        """
        # VULNERABILITY: Checksum is computed but NEVER validated on load
        checksum = hashlib.md5(data if isinstance(data, bytes) else data.encode()).hexdigest()

        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO firmware (device_id, version, data, uploaded_by, upload_time, checksum) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (device_id, version, 
             data if isinstance(data, bytes) else data.encode(),
             uploaded_by, timestamp(), checksum)
        )
        self.conn.commit()
        self.log_event(uploaded_by, "FIRMWARE_UPLOAD",
                       f"Device: {device_id}, Version: {version}, Checksum: {checksum}",
                       severity="WARNING")
        return checksum

    def get_firmware(self, device_id):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM firmware WHERE device_id=? ORDER BY id DESC LIMIT 1",
            (device_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def close(self):
        self.conn.close()
