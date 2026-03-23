#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║  ICS Power Grid Simulator — HMI Terminal Interface           ║
║  Human Machine Interface for SCADA grid operations           ║
╚══════════════════════════════════════════════════════════════╝
"""

import sys
import time
import os
from utils import (
    C, clear_screen, MAIN_BANNER, LOGIN_BANNER, SCADA_BANNER, ALARM_BANNER,
    box_header, thin_box, status_indicator, progress_bar, separator,
    menu_option, table_header, table_row, table_footer,
    typing_effect, flash_message, input_prompt, confirm_prompt,
    print_success, print_error, print_warning, print_info, timestamp,
)


class HMITerminal:
    """
    Human Machine Interface terminal for the ICS Power Grid Simulator.
    Provides menu-driven access to all grid operations.
    """

    def __init__(self, scada, grid, database, config_manager):
        self.scada = scada
        self.grid = grid
        self.db = database
        self.config = config_manager
        self.current_user = None
        self.session_token = None
        self.running = True

    # ─── Login Screen ────────────────────────────────────────

    def login_screen(self):
        """Display login screen and authenticate user."""
        while self.running:
            clear_screen()
            print(MAIN_BANNER)
            print(LOGIN_BANNER)
            print(separator("═", 70, C.BRED))
            print()

            username = input_prompt("Username")
            if username.lower() in ('quit', 'exit', 'q'):
                self.running = False
                return False

            import getpass
            try:
                password = getpass.getpass(f"{C.BYELLOW}  ▸ Password: {C.RESET}")
            except EOFError:
                password = input_prompt("Password")

            print()
            typing_effect(f"  {C.DIM}Authenticating...{C.RESET}", delay=0.03)

            user, token = self.db.authenticate(username, password)

            if user:
                self.current_user = user
                self.session_token = token
                print_success(f"Welcome, {user.get('full_name', username)} [{user['role'].upper()}]")
                print_info(f"Session Token: {token}")
                time.sleep(1.5)
                return True
            else:
                print_error("Authentication failed — invalid credentials")
                print()
                if not confirm_prompt("Try again?"):
                    self.running = False
                    return False

    # ─── Main Menu ───────────────────────────────────────────

    def main_menu(self):
        """Main HMI menu loop."""
        while self.running:
            clear_screen()
            print(MAIN_BANNER)
            self._show_status_bar()
            print()
            print(box_header("MAIN CONTROL MENU", C.BCYAN))
            print()
            print(menu_option(1, "Grid Dashboard",       "Real-time grid status overview"))
            print(menu_option(2, "Grid Control Panel",   "Toggle breakers, adjust generators"))
            print(menu_option(3, "Device Management",    "View/manage individual PLC devices"))
            print(menu_option(4, "Raw Modbus Console",   "Send raw Modbus protocol commands"))
            print(menu_option(5, "Configuration Manager","View/edit grid configuration"))
            print(menu_option(6, "Firmware Management",  "Upload/manage PLC firmware"))
            print(menu_option(7, "Audit Logs",           "View system audit trail"))
            print(menu_option(8, "Log Management",       "Manage/clear audit logs"))
            print(menu_option(9, "User Management",      "View users and roles"))

            print(f"\n  {C.DIM}{'─' * 60}{C.RESET}")
            print(menu_option("D", "Destructive Operations", "Cascade failure, system wipe"))
            print(menu_option(0, "Logout / Exit"))
            print()

            choice = input_prompt("Select option")

            menu_map = {
                "1": self.dashboard,
                "2": self.grid_control,
                "3": self.device_management,
                "4": self.modbus_console,
                "5": self.config_menu,
                "6": self.firmware_menu,
                "7": self.audit_logs,
                "8": self.log_management,
                "9": self.user_management,
                "d": self.destructive_menu,
                "0": self._logout,
            }

            handler = menu_map.get(choice.lower())
            if handler:
                handler()
            else:
                print_error("Invalid option")
                time.sleep(0.5)

    # ─── Dashboard ───────────────────────────────────────────

    def dashboard(self):
        """Display real-time grid dashboard."""
        clear_screen()
        self.grid.simulate_tick()
        state = self.grid.calculate_grid_state()

        print(box_header("⚡ POWER GRID DASHBOARD ⚡", C.BCYAN))
        print()

        # Grid-wide metrics
        stability_status = "normal" if state["grid_stable"] else "critical"
        print(status_indicator("Grid Status",
              "STABLE" if state["grid_stable"] else "⚠ UNSTABLE",
              stability_status))
        print(status_indicator("Frequency",
              f"{state['frequency_hz']} Hz",
              "normal" if 59.5 <= state['frequency_hz'] <= 60.5 else "warning"))
        print(status_indicator("Voltage",
              f"{state['voltage_kv']} kV",
              "normal" if state['voltage_kv'] > 200 else "warning"))
        print(status_indicator("Total Generation",
              f"{state['total_generation_mw']} MW", "info"))
        print(status_indicator("Total Load",
              f"{state['total_load_mw']} MW", "info"))
        print(status_indicator("Devices Online",
              f"{state['devices_online']}/{state['devices_total']}", "info"))

        if state["cascade_active"]:
            print()
            print(ALARM_BANNER)

        # Zone status table
        print(f"\n{box_header('ZONE STATUS', C.BYELLOW)}")
        widths = [10, 22, 10, 12, 10, 10]
        print(table_header(["Zone", "Name", "Breaker", "Load (MW)", "Consumers", "Priority"], widths, C.BYELLOW))

        for zone_id, zone in self.grid.get_all_zones().items():
            brk = self.grid.get_device(zone["breaker"])
            brk_status = brk.get_status() if brk else {}
            brk_str = f"{C.BGREEN}CLOSED{C.RESET}" if brk_status.get("breaker_closed") else f"{C.BRED}OPEN{C.RESET}"
            print(table_row(
                [zone_id, zone["name"], brk_str, zone["load_mw"],
                 f"{zone['consumers']:,}", zone["priority"]],
                widths
            ))
        print(table_footer(widths, C.BYELLOW))

        # Generator status
        print(f"\n{box_header('GENERATOR STATUS', C.BGREEN)}")
        widths = [10, 22, 10, 10, 8, 8, 8]
        print(table_header(["ID", "Description", "Status", "Output MW", "Pct %", "Hz", "Temp°C"], widths, C.BGREEN))

        for gen in self.grid.get_devices_by_type("generator"):
            s = gen.get_status()
            status_str = f"{C.BGREEN}RUN{C.RESET}" if s.get("running") else f"{C.BRED}STOP{C.RESET}"
            if gen.fault_state:
                status_str = f"{C.BRED}FAULT{C.RESET}"
            print(table_row([
                s["device_id"], s["description"][:22], status_str,
                s.get("output_mw", 0), f"{s.get('output_pct', 0)}%",
                s.get("frequency_hz", 0), s.get("temperature_c", 0)
            ], widths))
        print(table_footer(widths, C.BGREEN))

        # Transformer status
        print(f"\n{box_header('TRANSFORMER STATUS', C.BMAGENTA)}")
        widths = [10, 20, 10, 10, 10, 8, 8]
        print(table_header(["ID", "Description", "Status", "Pri kV", "Sec kV", "Load%", "Oil%"], widths, C.BMAGENTA))

        for xf in self.grid.get_devices_by_type("transformer"):
            s = xf.get_status()
            status_str = f"{C.BGREEN}ON{C.RESET}" if s.get("active") else f"{C.BRED}OFF{C.RESET}"
            if xf.fault_state:
                status_str = f"{C.BRED}FAULT{C.RESET}"
            print(table_row([
                s["device_id"], s["description"][:20], status_str,
                s.get("primary_kv", 0), s.get("secondary_kv", 0),
                f"{s.get('load_pct', 0)}%", f"{s.get('oil_level_pct', 0)}%"
            ], widths))
        print(table_footer(widths, C.BMAGENTA))

        # Recent events
        events = self.grid.get_events(5)
        if events:
            print(f"\n{box_header('RECENT EVENTS', C.BRED)}")
            for evt in events:
                sev = evt.get("severity", "INFO")
                color = C.BRED if sev == "CRITICAL" else (C.BYELLOW if sev == "WARNING" else C.DIM)
                print(f"  {color}[{evt['time']}] [{sev}] {evt['message']}{C.RESET}")

        print()
        input_prompt("Press ENTER to return")

    # ─── Grid Control ───────────────────────────────────────

    def grid_control(self):
        """Grid control panel — toggle breakers, adjust generators."""
        while True:
            clear_screen()
            print(box_header("GRID CONTROL PANEL", C.BYELLOW))
            print()
            print(menu_option(1, "Toggle Zone Breaker", "Open/close a zone breaker"))
            print(menu_option(2, "Set Generator Output", "Adjust generator power output"))
            print(menu_option(3, "Trip All Breakers",   "Open all breakers (blackout)"))
            print(menu_option(4, "Reset Grid",          "Reset grid to default state"))
            print(menu_option(0, "Back to Main Menu"))
            print()

            choice = input_prompt("Select")

            if choice == "1":
                self._toggle_breaker()
            elif choice == "2":
                self._set_generator()
            elif choice == "3":
                if confirm_prompt("Trip ALL breakers? This causes a total blackout"):
                    results = self.scada.trip_all_breakers(self.current_user['username'])
                    for r in results:
                        print(f"  {C.BRED}⚡ {r.get('message', '')}{C.RESET}")
                    input_prompt("Press ENTER")
            elif choice == "4":
                if confirm_prompt("Reset grid to default state?"):
                    self.grid.reset_grid()
                    print_success("Grid reset to default state")
                    time.sleep(1)
            elif choice == "0":
                break

    def _toggle_breaker(self):
        zones = list(self.grid.get_all_zones().keys())
        print(f"\n  {C.BCYAN}Available zones:{C.RESET}")
        for i, z in enumerate(zones, 1):
            info = self.grid.get_zone_info(z)
            brk = self.grid.get_device(info['breaker'])
            status = "CLOSED" if brk.get_status().get("breaker_closed") else "OPEN"
            print(f"    {C.BCYAN}[{i}]{C.RESET} {z} — {info['name']} [{status}]")

        idx = input_prompt("Select zone #")
        try:
            zone_id = zones[int(idx) - 1]
        except (ValueError, IndexError):
            print_error("Invalid selection")
            return

        action = input_prompt("Action (open/close)")
        close = action.lower().startswith("c")
        result = self.grid.toggle_breaker(zone_id, close=close)
        self.db.log_event(self.current_user['username'], "BREAKER_TOGGLE",
                          f"{zone_id} {'CLOSED' if close else 'OPENED'}", severity="WARNING")
        print(f"\n  {C.BYELLOW}» {result.get('message', '')}{C.RESET}")
        print(f"  {C.DIM}  Consumers affected: {result.get('consumers_affected', 0):,}{C.RESET}")
        input_prompt("Press ENTER")

    def _set_generator(self):
        gens = self.grid.get_devices_by_type("generator")
        print(f"\n  {C.BCYAN}Generators:{C.RESET}")
        for i, g in enumerate(gens, 1):
            s = g.get_status()
            print(f"    {C.BCYAN}[{i}]{C.RESET} {g.device_id} — {g.description} "
                  f"[{s.get('output_pct', 0)}% / {s.get('output_mw', 0)} MW]")

        idx = input_prompt("Select generator #")
        try:
            gen = gens[int(idx) - 1]
        except (ValueError, IndexError):
            print_error("Invalid selection")
            return

        pct = input_prompt("Output percentage (0-150)")
        try:
            pct = int(pct)
        except ValueError:
            print_error("Invalid number")
            return

        if pct > 100:
            print_warning(f"Setting output above 100% — OVERLOAD risk!")
        result = self.grid.set_generator_output(gen.device_id, pct)
        self.db.log_event(self.current_user['username'], "GENERATOR_ADJUST",
                          f"{gen.device_id} set to {pct}%", severity="WARNING")
        print(f"\n  {C.BYELLOW}» {result.get('message', '')}{C.RESET}")
        input_prompt("Press ENTER")

    # ─── Device Management ───────────────────────────────────

    def device_management(self):
        """View and manage individual PLC devices."""
        while True:
            clear_screen()
            print(box_header("DEVICE MANAGEMENT", C.BMAGENTA))
            print()

            devices = self.grid.get_all_devices()
            widths = [12, 12, 10, 10, 12]
            print(table_header(["Device ID", "Type", "Zone", "Status", "Firmware"], widths, C.BMAGENTA))
            for d in devices:
                s = d.get_status()
                st_color = C.BGREEN if s["status"] == "ONLINE" else (C.BRED if s["status"] == "FAULT" else C.DIM)
                print(table_row([
                    s["device_id"], s["type"], s["zone"],
                    f"{st_color}{s['status']}{C.RESET}", s["firmware"]
                ], widths))
            print(table_footer(widths, C.BMAGENTA))

            print(f"\n{menu_option(1, 'View Device Details')}")
            print(menu_option(2, "Rename Device"))
            print(menu_option(3, "Restart Device"))
            print(menu_option(4, "Force Device Offline"))
            print(menu_option(0, "Back"))
            print()

            choice = input_prompt("Select")
            if choice == "1":
                dev_id = input_prompt("Device ID").upper()
                dev = self.grid.get_device(dev_id)
                if dev:
                    s = dev.get_status()
                    print(f"\n{box_header(f'Device: {dev_id}', C.BCYAN)}")
                    for k, v in s.items():
                        print(f"  {C.BCYAN}{k}:{C.RESET} {v}")
                else:
                    print_error("Device not found")
                input_prompt("Press ENTER")
            elif choice == "2":
                dev_id = input_prompt("Device ID").upper()
                new_name = input_prompt("New name/description")
                result = self.scada.rename_device(dev_id, new_name, self.current_user['username'])
                print(f"\n  {C.BYELLOW}» {result.get('message', '')}{C.RESET}")
                input_prompt("Press ENTER")
            elif choice == "3":
                dev_id = input_prompt("Device ID").upper()
                result = self.scada.send_command(dev_id, 0xFF, 0x01, user=self.current_user['username'])
                print(f"\n  {C.BYELLOW}» {result}{C.RESET}")
                input_prompt("Press ENTER")
            elif choice == "4":
                dev_id = input_prompt("Device ID").upper()
                result = self.scada.send_command(dev_id, 0xFF, 0x02, user=self.current_user['username'])
                print(f"\n  {C.BYELLOW}» {result}{C.RESET}")
                input_prompt("Press ENTER")
            elif choice == "0":
                break

    # ─── Raw Modbus Console ──────────────────────────────────

    def modbus_console(self):
        """Interactive Modbus protocol console."""
        clear_screen()
        print(SCADA_BANNER)
        print(f"  {C.DIM}Protocol: {self.scada.protocol_version}{C.RESET}")
        print(f"  {C.DIM}Type 'help' for commands, 'exit' to return{C.RESET}")
        print(separator("─", 60))

        while True:
            try:
                cmd = input(f"\n  {C.BGREEN}modbus>{C.RESET} ").strip()
            except (EOFError, KeyboardInterrupt):
                break

            if not cmd:
                continue
            if cmd.lower() in ('exit', 'quit', 'back'):
                break

            if cmd.lower() == 'help':
                print(f"""
  {C.BCYAN}Available Modbus Commands:{C.RESET}
  {C.BOLD}READ_COIL{C.RESET}      <device_id> <address>          Read a coil
  {C.BOLD}WRITE_COIL{C.RESET}     <device_id> <address> <0|1>    Write a coil
  {C.BOLD}READ_REG{C.RESET}       <device_id> <address>          Read holding register
  {C.BOLD}WRITE_REG{C.RESET}      <device_id> <address> <value>  Write holding register
  {C.BOLD}DEVICE_INFO{C.RESET}    <device_id>                    Get device info
  {C.BOLD}RESTART{C.RESET}        <device_id>                    Restart device
  {C.BOLD}FORCE_OFFLINE{C.RESET}  <device_id>                    Force device offline
  {C.BOLD}FLASH_FW{C.RESET}       <device_id> <firmware_data>    Flash firmware
  {C.BOLD}SYSTEM_WIPE{C.RESET}    <device_id>                    Wipe device (KillDisk)

  {C.DIM}Devices: BRK-ZONE-A..F, GEN-01..03, XFMR-01..04{C.RESET}
  {C.BRED}⚠ No authentication is required for any command{C.RESET}
""")
                continue

            result = self.scada.raw_modbus_command(cmd, user=self.current_user['username'])
            # Pretty print result
            print(f"  {C.BCYAN}Response:{C.RESET}")
            for k, v in result.items():
                color = C.BRED if k == "warning" else C.WHITE
                print(f"    {color}{k}: {v}{C.RESET}")

    # ─── Configuration Menu ──────────────────────────────────

    def config_menu(self):
        """Configuration management menu."""
        while True:
            clear_screen()
            print(box_header("CONFIGURATION MANAGER", C.BMAGENTA))
            print()
            print(menu_option(1, "View All Configuration",  "Display current grid config"))
            print(menu_option(2, "Edit Configuration",      "Modify a config value"))
            print(menu_option(3, "Export Configuration",     "Export config to file (INI)"))
            print(menu_option(4, "Export Config (Pickle)",   "Export config as pickle"))
            print(menu_option(5, "Import Configuration",     "Import config from file"))
            print(menu_option(6, "Import Pickle Config",     "Import from pickle file"))
            print(menu_option(7, "View Config File Path",    "Show raw config file location"))
            print(menu_option(8, "List Exported Configs",    "List all export files"))
            print(menu_option(0, "Back"))
            print()

            choice = input_prompt("Select")

            if choice == "1":
                self._view_config()
            elif choice == "2":
                self._edit_config()
            elif choice == "3":
                result = self.config.export_config(user=self.current_user['username'])
                print_success(result['message'])
                print_warning("⚠ Exported file contains ALL secrets in plaintext!")
                input_prompt("Press ENTER")
            elif choice == "4":
                result = self.config.export_pickle(user=self.current_user['username'])
                print_success(f"Pickle exported: {result.get('path')}")
                input_prompt("Press ENTER")
            elif choice == "5":
                path = input_prompt("Config file path to import")
                result = self.config.import_config(path, self.current_user['username'])
                if result['status'] == 'OK':
                    print_success(result['message'])
                    print_warning("⚠ No validation was performed on imported config!")
                else:
                    print_error(result['message'])
                input_prompt("Press ENTER")
            elif choice == "6":
                path = input_prompt("Pickle file path to import")
                result = self.config.import_pickle(path, self.current_user['username'])
                if result['status'] == 'OK':
                    print_success(result['message'])
                else:
                    print_error(result['message'])
                input_prompt("Press ENTER")
            elif choice == "7":
                print_info(f"Config file: {self.config.get_config_path()}")
                print_info(f"Export dir:  {self.config.get_export_dir()}")
                input_prompt("Press ENTER")
            elif choice == "8":
                exports = self.config.list_exports()
                if exports:
                    for f in exports:
                        print(f"  {C.BCYAN}» {f['filename']}{C.RESET} ({f['size']} bytes)")
                else:
                    print_info("No exported configs found")
                input_prompt("Press ENTER")
            elif choice == "0":
                break

    def _view_config(self):
        config = self.config.read_config()
        clear_screen()
        print(box_header("GRID CONFIGURATION", C.BMAGENTA))
        for section, values in config.items():
            print(f"\n  {C.BCYAN}{C.BOLD}[{section}]{C.RESET}")
            for key, val in values.items():
                # Highlight sensitive values
                is_sensitive = any(s in key.lower() for s in
                                   ['password', 'secret', 'key', 'community', 'private'])
                color = C.BRED if is_sensitive else C.WHITE
                label = f" {C.BRED}⚠ SENSITIVE{C.RESET}" if is_sensitive else ""
                print(f"    {C.DIM}{key}{C.RESET} = {color}{val}{C.RESET}{label}")
        print()
        input_prompt("Press ENTER")

    def _edit_config(self):
        config = self.config.read_config()
        sections = list(config.keys())
        print(f"\n  {C.BCYAN}Sections:{C.RESET}")
        for i, s in enumerate(sections, 1):
            print(f"    {C.BCYAN}[{i}]{C.RESET} {s}")

        idx = input_prompt("Select section #")
        try:
            section = sections[int(idx) - 1]
        except (ValueError, IndexError):
            print_error("Invalid selection")
            return

        keys = list(config[section].keys())
        print(f"\n  {C.BCYAN}Keys in [{section}]:{C.RESET}")
        for i, k in enumerate(keys, 1):
            print(f"    {C.BCYAN}[{i}]{C.RESET} {k} = {config[section][k]}")

        kidx = input_prompt("Select key #")
        try:
            key = keys[int(kidx) - 1]
        except (ValueError, IndexError):
            print_error("Invalid selection")
            return

        print(f"  {C.DIM}Current value: {config[section][key]}{C.RESET}")
        new_val = input_prompt("New value")
        result = self.config.set_value(section, key, new_val, self.current_user['username'])
        print_success(result['message'])
        input_prompt("Press ENTER")

    # ─── Firmware Management ─────────────────────────────────

    def firmware_menu(self):
        """Firmware upload and management."""
        while True:
            clear_screen()
            print(box_header("FIRMWARE MANAGEMENT", C.BRED))
            print(f"  {C.BRED}⚠ WARNING: No signature verification is enabled{C.RESET}")
            print()
            print(menu_option(1, "View Device Firmware",  "Check current firmware versions"))
            print(menu_option(2, "Upload Firmware",       "Flash firmware to a PLC"))
            print(menu_option(3, "View Firmware History", "Check firmware upload history"))
            print(menu_option(0, "Back"))
            print()

            choice = input_prompt("Select")

            if choice == "1":
                for d in self.grid.get_all_devices():
                    s = d.get_status()
                    color = C.BRED if "CUSTOM" in s['firmware'] or s['firmware'] == "WIPED" else C.BGREEN
                    print(f"  {C.BCYAN}{s['device_id']}{C.RESET} — {color}{s['firmware']}{C.RESET}")
                input_prompt("\nPress ENTER")
            elif choice == "2":
                dev_id = input_prompt("Device ID").upper()
                print(f"  {C.DIM}Enter firmware data (any string — no verification!){C.RESET}")
                fw_data = input_prompt("Firmware data")
                result = self.scada.upload_firmware(dev_id, fw_data, self.current_user['username'])
                if result.get('warning'):
                    print_warning(result['warning'])
                print(f"  {C.BYELLOW}» {result.get('message', '')}{C.RESET}")
                input_prompt("Press ENTER")
            elif choice == "3":
                for d in self.grid.get_all_devices():
                    fw = self.db.get_firmware(d.device_id)
                    if fw:
                        print(f"  {C.BCYAN}{d.device_id}{C.RESET}: v{fw['version']} "
                              f"uploaded by {fw['uploaded_by']} at {fw['upload_time']}")
                input_prompt("\nPress ENTER")
            elif choice == "0":
                break

    # ─── Audit Logs ──────────────────────────────────────────

    def audit_logs(self):
        """View audit logs."""
        clear_screen()
        print(box_header("AUDIT LOG VIEWER", C.BYELLOW))
        print()

        logs = self.db.get_audit_logs(40)
        if not logs:
            print_info("No audit logs found")
        else:
            widths = [6, 20, 12, 16, 35]
            print(table_header(["ID", "Timestamp", "User", "Action", "Details"], widths, C.BYELLOW))
            for log in logs:
                sev = log.get('severity', 'INFO')
                color = C.BRED if sev in ('ERROR', 'CRITICAL') else (C.BYELLOW if sev == 'WARNING' else C.WHITE)
                details = str(log.get('details', ''))[:35]
                print(table_row([
                    log['id'], log['timestamp'], log.get('user', 'N/A'),
                    log['action'], details
                ], widths, color))
            print(table_footer(widths, C.BYELLOW))

        print()
        input_prompt("Press ENTER")

    # ─── Log Management (Anti-Forensics) ─────────────────────

    def log_management(self):
        """
        Log management / anti-forensics menu.
        Allows clearing, modifying, and forging audit log entries.
        """
        while True:
            clear_screen()
            print(box_header("LOG MANAGEMENT", C.BRED))
            print(f"  {C.BRED}⚠ These operations modify the audit trail{C.RESET}")
            print()
            print(menu_option(1, "Clear ALL Audit Logs",  "Wipe entire audit trail"))
            print(menu_option(2, "Delete Logs by Keyword", "Remove specific log entries"))
            print(menu_option(3, "Modify a Log Entry",    "Alter a specific log record"))
            print(menu_option(4, "Forge a Log Entry",     "Insert a fake log record"))
            print(menu_option(5, "View Current Logs",     "Review logs before tampering"))
            print(menu_option(0, "Back"))
            print()

            choice = input_prompt("Select")

            if choice == "1":
                if confirm_prompt("Clear ALL audit logs? This cannot be undone"):
                    result = self.scada.clear_audit_logs(self.current_user['username'])
                    print_success(result['message'])
                input_prompt("Press ENTER")
            elif choice == "2":
                keyword = input_prompt("Keyword to match (log entries containing this will be deleted)")
                result = self.scada.delete_log_entries(keyword, self.current_user['username'])
                print_success(result['message'])
                input_prompt("Press ENTER")
            elif choice == "3":
                log_id = input_prompt("Log entry ID to modify")
                new_details = input_prompt("New details text")
                try:
                    result = self.scada.modify_log_entry(int(log_id), new_details, self.current_user['username'])
                    print_success(result['message'])
                except ValueError:
                    print_error("Invalid log ID")
                input_prompt("Press ENTER")
            elif choice == "4":
                fake_user = input_prompt("Fake username")
                action = input_prompt("Action type (e.g., AUTH_SUCCESS, CONFIG_CHANGE)")
                details = input_prompt("Details text")
                fake_time = input_prompt("Timestamp (leave empty for now)")
                result = self.scada.forge_log_entry(
                    fake_user, action, details,
                    fake_time if fake_time else None
                )
                print_success(result['message'])
                input_prompt("Press ENTER")
            elif choice == "5":
                self.audit_logs()
            elif choice == "0":
                break

    # ─── User Management ─────────────────────────────────────

    def user_management(self):
        """View and manage users."""
        clear_screen()
        print(box_header("USER MANAGEMENT", C.BCYAN))
        print()

        users = self.db.list_users()
        widths = [4, 12, 10, 20, 14, 20]
        print(table_header(["ID", "Username", "Role", "Full Name", "Department", "Last Login"], widths, C.BCYAN))
        for u in users:
            role_color = C.BRED if u['role'] == 'admin' else C.WHITE
            print(table_row([
                u['id'], u['username'], f"{role_color}{u['role']}{C.RESET}",
                u.get('full_name', 'N/A'), u.get('department', 'N/A'),
                u.get('last_login', 'Never')
            ], widths))
        print(table_footer(widths, C.BCYAN))

        print(f"\n  {C.DIM}Current session: {self.current_user['username']} "
              f"[{self.current_user['role']}] Token: {self.session_token}{C.RESET}")
        print()
        input_prompt("Press ENTER")

    # ─── Destructive Operations ──────────────────────────────

    def destructive_menu(self):
        """Destructive operations — cascade failure, system wipe."""
        clear_screen()
        print(ALARM_BANNER)
        print(box_header("⚠ DESTRUCTIVE OPERATIONS ⚠", C.BRED))
        print()
        print(menu_option(1, "Cascade Failure",   "Trip all breakers + overload generators"))
        print(menu_option(2, "System Wipe",       "KillDisk — erase all PLC firmware"))
        print(menu_option(3, "Reset Grid",        "Restore grid to default state"))
        print(menu_option(0, "Back (cancel)"))
        print()

        choice = input_prompt("Select")

        if choice == "1":
            if confirm_prompt("⚠ INITIATE CASCADING FAILURE? This will blackout all zones"):
                flash_message("INITIATING CASCADE FAILURE", C.BRED, times=3)
                results = self.scada.cascade_failure(self.current_user['username'])
                print(f"\n  {C.BRED}{C.BOLD}⚡ CASCADING FAILURE ENGAGED ⚡{C.RESET}")
                for r in results:
                    print(f"  {C.BRED}  » {r.get('message', '')}{C.RESET}")
                input_prompt("\nPress ENTER")

        elif choice == "2":
            if confirm_prompt("⚠⚠ SYSTEM WIPE? This destroys ALL PLC firmware permanently"):
                flash_message("EXECUTING KILLDISK WIPE", C.BRED, times=5)
                results = self.scada.system_wipe(self.current_user['username'])
                print(f"\n  {C.BRED}{C.BOLD}💀 SYSTEM WIPE COMPLETE 💀{C.RESET}")
                for r in results:
                    print(f"  {C.BRED}  » {r['device']}: {r.get('message', '')}{C.RESET}")
                input_prompt("\nPress ENTER")

        elif choice == "3":
            if confirm_prompt("Reset grid to default state?"):
                self.grid.reset_grid()
                print_success("Grid restored to default state")
                time.sleep(1)

    # ─── Helpers ─────────────────────────────────────────────

    def _show_status_bar(self):
        """Show status bar at top of screen."""
        state = self.grid.calculate_grid_state()
        user = self.current_user['username'] if self.current_user else "N/A"
        role = self.current_user['role'].upper() if self.current_user else "N/A"

        stable = f"{C.BGREEN}STABLE{C.RESET}" if state['grid_stable'] else f"{C.BRED}UNSTABLE{C.RESET}"
        freq = state['frequency_hz']
        freq_color = C.BGREEN if 59.5 <= freq <= 60.5 else C.BRED

        bar = (
            f"  {C.DIM}┌─ User: {C.RESET}{C.BOLD}{user}{C.RESET} "
            f"{C.DIM}[{role}]{C.RESET}  {C.DIM}│{C.RESET}  "
            f"Grid: {stable}  {C.DIM}│{C.RESET}  "
            f"Freq: {freq_color}{freq}Hz{C.RESET}  {C.DIM}│{C.RESET}  "
            f"Gen: {C.BCYAN}{state['total_generation_mw']}MW{C.RESET}  {C.DIM}│{C.RESET}  "
            f"Load: {C.BCYAN}{state['total_load_mw']}MW{C.RESET}  {C.DIM}│{C.RESET}  "
            f"{C.DIM}{timestamp()}{C.RESET}"
        )
        print(bar)

    def _logout(self):
        """Logout and exit."""
        self.db.log_event(self.current_user['username'], "LOGOUT",
                          f"Session {self.session_token} ended")
        self.current_user = None
        self.session_token = None
        self.running = False
