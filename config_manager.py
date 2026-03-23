#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║  ICS Power Grid Simulator — Configuration Manager            ║
║  INI-based grid configuration with import/export             ║
║                                                              ║
║  ⚠ INTENTIONAL VULNERABILITIES:                              ║
║    - Plaintext secrets in config files (CVE-2014-4686)       ║
║    - Insecure deserialization via pickle (CVE-2020-15368)     ║
║    - Config-based privilege escalation (CVE-2020-10625)      ║
╚══════════════════════════════════════════════════════════════╝
"""

import os
import configparser
import pickle
import base64
import json
from utils import C, timestamp

CONFIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "configs")
MAIN_CONFIG = os.path.join(CONFIG_DIR, "grid_config.ini")
BACKUP_CONFIG = os.path.join(CONFIG_DIR, "grid_backup.ini")
EXPORT_DIR = os.path.join(CONFIG_DIR, "exports")


class ConfigManager:
    """
    Configuration manager for the power grid.
    Handles reading/writing INI config files.
    
    Contains INTENTIONAL vulnerabilities for cybersecurity training.
    """

    def __init__(self, database):
        self.db = database
        self._ensure_dirs()
        self._initialize_config()

    def _ensure_dirs(self):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        os.makedirs(EXPORT_DIR, exist_ok=True)

    def _initialize_config(self):
        """Create the main config file with sensitive data in PLAINTEXT."""
        if os.path.exists(MAIN_CONFIG):
            return

        config = configparser.ConfigParser()

        config["GRID"] = {
            "frequency_target": "60.0",
            "voltage_target": "230.0",
            "max_load_mw": "5000",
            "auto_balance": "true",
            "cascade_protection": "true",
        }

        config["SCADA"] = {
            "polling_rate_sec": "5",
            "modbus_port": "502",
            "protocol_version": "Modbus-TCP-Sim v2.1",
            "api_key": "SK-4f8a2b3c-d5e6-7890-abcd-ef1234567890",
            "api_secret": "a7x9Kp2mW4qR8sT1uY3vE6wB0dF5gH",
        }

        # VULNERABILITY: Plaintext credentials in config file!
        # Real-world: CVE-2014-4686 (Siemens WinCC / BlackEnergy campaign)
        config["DATABASE"] = {
            "host": "localhost",
            "port": "5432",
            "name": "scada_prod",
            "username": "scada_admin",
            "password": "Pr0d_SCADA_2024!",
            "backup_password": "backup_Pr0d_2024!",
        }

        config["NETWORK"] = {
            "ot_gateway": "10.10.1.1",
            "ot_subnet": "10.10.1.0/24",
            "dmz_gateway": "172.16.0.1",
            "corporate_gateway": "192.168.1.1",
            "snmp_community": "public",
            "snmp_private": "scada_priv_2024",
        }

        config["AUTHENTICATION"] = {
            "session_timeout_min": "30",
            "max_failed_attempts": "0",
            "lockout_duration_min": "0",
            "password_policy": "none",
            "mfa_enabled": "false",
        }

        config["FIRMWARE"] = {
            "update_server": "http://scada-internal:8080/firmware",
            "signature_verification": "false",
            "auto_update": "false",
            "rollback_enabled": "false",
        }

        config["LOGGING"] = {
            "log_level": "DEBUG",
            "log_passwords": "true",
            "log_sessions": "true",
            "log_modbus_commands": "true",
            "log_file": "/tmp/scada_audit.log",
            "rotate_logs": "false",
            "encrypt_logs": "false",
        }

        # VULNERABILITY: User roles stored in config — editable!
        config["USERS"] = {
            "admin_role": "admin",
            "operator_role": "operator",
            "engineer_role": "engineer",
            "viewer_role": "viewer",
        }

        with open(MAIN_CONFIG, 'w') as f:
            config.write(f)

    # ─── Read/Write Config ───────────────────────────────────

    def read_config(self):
        """Read the full config file."""
        config = configparser.ConfigParser()
        config.read(MAIN_CONFIG)
        result = {}
        for section in config.sections():
            result[section] = dict(config[section])
        return result

    def get_value(self, section, key):
        """Get a specific config value."""
        config = configparser.ConfigParser()
        config.read(MAIN_CONFIG)
        try:
            return config[section][key]
        except KeyError:
            return None

    def set_value(self, section, key, value, user="SYSTEM"):
        """Set a specific config value."""
        config = configparser.ConfigParser()
        config.read(MAIN_CONFIG)

        if section not in config:
            config[section] = {}

        old_value = config[section].get(key, "<new>")
        config[section][key] = value

        with open(MAIN_CONFIG, 'w') as f:
            config.write(f)

        # Also update DB config
        self.db.set_config(f"{section.lower()}.{key}", value, user)
        self.db.log_event(user, "CONFIG_MODIFY",
                          f"[{section}] {key}: '{old_value}' -> '{value}'",
                          severity="WARNING")

        return {"status": "OK", "message": f"[{section}] {key} = {value}"}

    def add_section(self, section, values, user="SYSTEM"):
        """Add a new section to the config."""
        config = configparser.ConfigParser()
        config.read(MAIN_CONFIG)
        config[section] = values
        with open(MAIN_CONFIG, 'w') as f:
            config.write(f)
        self.db.log_event(user, "CONFIG_ADD_SECTION",
                          f"Added section [{section}] with {len(values)} keys",
                          severity="WARNING")
        return {"status": "OK"}

    # ─── Export/Import ───────────────────────────────────────

    def export_config(self, filename=None, user="SYSTEM"):
        """
        Export configuration to a file.
        
        ⚠ VULNERABILITY: Exports contain ALL secrets in plaintext!
        Real-world: BlackEnergy campaign harvested WinCC config files.
        """
        if not filename:
            filename = f"grid_export_{timestamp().replace(' ', '_').replace(':', '-')}.ini"

        export_path = os.path.join(EXPORT_DIR, filename)

        # Read and copy entire config (including secrets!)
        config = configparser.ConfigParser()
        config.read(MAIN_CONFIG)

        with open(export_path, 'w') as f:
            f.write(f"; ICS Power Grid Configuration Export\n")
            f.write(f"; Exported: {timestamp()}\n")
            f.write(f"; Exported by: {user}\n")
            f.write(f"; ⚠ CONTAINS SENSITIVE DATA — HANDLE WITH CARE\n\n")
            config.write(f)

        self.db.log_event(user, "CONFIG_EXPORT",
                          f"Config exported to: {export_path}",
                          severity="INFO")

        return {
            "status": "OK",
            "path": export_path,
            "message": f"Configuration exported to: {export_path}",
        }

    def import_config(self, filepath, user="SYSTEM"):
        """
        Import a configuration file.
        
        ⚠ VULNERABILITY: No validation on imported configs!
        An attacker can import a config that:
          - Changes user roles (privilege escalation — CVE-2020-10625)
          - Modifies security settings
          - Disables logging
          - Changes network routes
        """
        if not os.path.exists(filepath):
            return {"status": "ERROR", "message": f"File not found: {filepath}"}

        # Backup current config
        config = configparser.ConfigParser()
        config.read(MAIN_CONFIG)
        with open(BACKUP_CONFIG, 'w') as f:
            config.write(f)

        # Import new config WITHOUT ANY VALIDATION
        new_config = configparser.ConfigParser()
        new_config.read(filepath)

        # Overwrite main config
        with open(MAIN_CONFIG, 'w') as f:
            new_config.write(f)

        # Apply relevant settings to DB
        for section in new_config.sections():
            for key, value in new_config[section].items():
                self.db.set_config(f"{section.lower()}.{key}", value, user)

        # VULNERABILITY: If the imported config changes user roles,
        # update them in the database too (privilege escalation!)
        if "USERS" in new_config:
            for key, value in new_config["USERS"].items():
                username = key.replace("_role", "")
                user_record = self.db.get_user(username)
                if user_record:
                    self.db.update_user_role(username, value)

        self.db.log_event(user, "CONFIG_IMPORT",
                          f"Config imported from: {filepath}", severity="WARNING")

        return {
            "status": "OK",
            "message": f"Configuration imported from: {filepath}",
            "sections": new_config.sections(),
        }

    def import_pickle(self, filepath, user="SYSTEM"):
        """
        Import configuration from a pickle file.
        
        ⚠ VULNERABILITY: INSECURE DESERIALIZATION!
        Pickle can execute arbitrary code during deserialization.
        Real-world: CVE-2020-15368 and many others.
        
        Exploit: Create a malicious pickle file that executes code.
        """
        if not os.path.exists(filepath):
            return {"status": "ERROR", "message": f"File not found: {filepath}"}

        try:
            # VULNERABLE: Loads arbitrary pickle data!
            with open(filepath, 'rb') as f:
                data = pickle.load(f)

            # Apply imported config
            if isinstance(data, dict):
                for section, values in data.items():
                    if isinstance(values, dict):
                        self.add_section(section, values, user)

            self.db.log_event(user, "CONFIG_IMPORT_PICKLE",
                              f"Pickle config imported from: {filepath}",
                              severity="WARNING")

            return {"status": "OK", "message": f"Pickle config imported: {filepath}"}

        except Exception as e:
            return {"status": "ERROR", "message": f"Pickle import failed: {e}"}

    def export_pickle(self, filename=None, user="SYSTEM"):
        """Export config as a pickle file (for "backup compatibility")."""
        if not filename:
            filename = f"grid_export_{timestamp().replace(' ', '_').replace(':', '-')}.pkl"

        export_path = os.path.join(EXPORT_DIR, filename)
        config_data = self.read_config()

        with open(export_path, 'wb') as f:
            pickle.dump(config_data, f)

        self.db.log_event(user, "CONFIG_EXPORT_PICKLE",
                          f"Pickle config exported to: {export_path}",
                          severity="INFO")

        return {"status": "OK", "path": export_path}

    # ─── Config Listing ──────────────────────────────────────

    def list_exports(self):
        """List all exported config files."""
        files = []
        if os.path.exists(EXPORT_DIR):
            for f in os.listdir(EXPORT_DIR):
                path = os.path.join(EXPORT_DIR, f)
                files.append({
                    "filename": f,
                    "path": path,
                    "size": os.path.getsize(path),
                })
        return files

    def get_config_path(self):
        return MAIN_CONFIG

    def get_export_dir(self):
        return EXPORT_DIR
