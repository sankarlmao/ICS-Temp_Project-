#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════╗
║                    ICS POWER GRID SIMULATOR                          ║
║           Industrial Control Systems — Vulnerability Lab             ║
║                                                                      ║
║   A terminal-based SCADA/ICS cybersecurity training environment      ║
║   with real-world vulnerabilities for penetration testing practice    ║
║                                                                      ║
║   ⚠  FOR EDUCATIONAL & AUTHORIZED SECURITY TESTING ONLY  ⚠          ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import sys
import os
import argparse

# Ensure module resolution
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import Database, DB_PATH
from grid_simulator import PowerGrid
from scada_server import SCADAServer
from config_manager import ConfigManager
from hmi_terminal import HMITerminal
from utils import C, clear_screen, MAIN_BANNER, print_success, print_error, print_info


def run_self_test():
    """Run automated self-test to validate all components."""
    print(f"\n{C.BCYAN}{C.BOLD}  ═══ ICS Power Grid Simulator — Self Test ═══{C.RESET}\n")
    passed = 0
    failed = 0

    def check(name, condition):
        nonlocal passed, failed
        if condition:
            print(f"  {C.BGREEN}✓ PASS{C.RESET} — {name}")
            passed += 1
        else:
            print(f"  {C.BRED}✗ FAIL{C.RESET} — {name}")
            failed += 1

    # 1. Database
    print(f"\n  {C.BCYAN}[Database]{C.RESET}")
    db = Database()
    check("Database initialized", db.conn is not None)
    user, token = db.authenticate("admin", "admin123")
    check("Hardcoded admin login works", user is not None)
    check("Session token generated", token is not None)
    logs = db.get_audit_logs(5)
    check("Audit logging works", len(logs) > 0)

    # 2. Power Grid
    print(f"\n  {C.BCYAN}[Power Grid]{C.RESET}")
    grid = PowerGrid()
    check("Grid initialized with 13 devices", len(grid.devices) == 13)
    check("6 breaker zones created", len(grid.get_devices_by_type("breaker")) == 6)
    check("3 generators created", len(grid.get_devices_by_type("generator")) == 3)
    check("4 transformers created", len(grid.get_devices_by_type("transformer")) == 4)

    state = grid.calculate_grid_state()
    check("Grid state calculation works", state is not None)
    check("Grid is initially stable", state['grid_stable'])

    # 3. PLC Devices
    print(f"\n  {C.BCYAN}[PLC Devices]{C.RESET}")
    brk = grid.get_device("BRK-ZONE-A")
    check("Breaker device accessible", brk is not None)
    result = brk.process_modbus_command(0x03, 0)
    check("Modbus READ_REG works", result['status'] == 'OK')
    result = brk.process_modbus_command(0x06, 0, 0)
    check("Modbus WRITE_REG works (no auth!)", result['status'] == 'OK')

    # Buffer overflow test
    result = brk.process_modbus_command(0x06, 150, 9999)
    check("Buffer overflow detected on out-of-bounds write", result['status'] == 'OVERFLOW')

    # 4. SCADA Server
    print(f"\n  {C.BCYAN}[SCADA Server]{C.RESET}")
    scada = SCADAServer(grid, db)
    result = scada.raw_modbus_command("READ_REG GEN-01 1")
    check("Raw Modbus command parsing works", result.get('status') == 'OK')

    # 5. Config Manager
    print(f"\n  {C.BCYAN}[Config Manager]{C.RESET}")
    config = ConfigManager(db)
    cfg = config.read_config()
    check("Config file created and readable", len(cfg) > 0)
    check("Plaintext secrets present in config",
          'password' in str(cfg.get('DATABASE', {}).get('password', '')).lower() or
          cfg.get('DATABASE', {}).get('password', '') != '')

    # SQL Injection test
    print(f"\n  {C.BCYAN}[Vulnerability Checks]{C.RESET}")
    sqli_user, _ = db.authenticate("' OR 1=1 --", "anything")
    check("SQL Injection bypass works", sqli_user is not None)

    # Summary
    total = passed + failed
    print(f"\n  {C.BOLD}Results: {passed}/{total} passed, {failed} failed{C.RESET}")
    if failed == 0:
        print(f"  {C.BGREEN}{C.BOLD}All tests passed! ✓{C.RESET}\n")
    else:
        print(f"  {C.BRED}{C.BOLD}Some tests failed ✗{C.RESET}\n")

    db.close()
    return failed == 0


def reset_lab():
    """Reset the lab to a clean state."""
    print(f"\n{C.BYELLOW}  Resetting lab to clean state...{C.RESET}")

    # Remove database
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print_success("Database removed")

    # Remove config directory
    config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "configs")
    if os.path.exists(config_dir):
        import shutil
        shutil.rmtree(config_dir)
        print_success("Config directory removed")

    # Remove temp log
    if os.path.exists("/tmp/scada_device_log.txt"):
        os.remove("/tmp/scada_device_log.txt")
        print_success("Temp logs removed")

    if os.path.exists("/tmp/scada_audit.log"):
        os.remove("/tmp/scada_audit.log")
        print_success("Audit log file removed")

    print_success("Lab reset complete — run again to initialize fresh state\n")


def main():
    parser = argparse.ArgumentParser(
        description="ICS Power Grid Cybersecurity Simulator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 main.py              Launch the HMI terminal
  python3 main.py --test       Run self-test suite
  python3 main.py --reset      Reset lab to clean state
  python3 main.py --debug      Launch with debug output
        """
    )
    parser.add_argument("--test", action="store_true", help="Run self-test suite")
    parser.add_argument("--reset", action="store_true", help="Reset lab to clean state")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")

    args = parser.parse_args()

    if args.reset:
        reset_lab()
        return

    if args.test:
        success = run_self_test()
        sys.exit(0 if success else 1)

    # ── Launch HMI Terminal ──
    try:
        clear_screen()

        # Initialize components
        db = Database()
        grid = PowerGrid()
        scada = SCADAServer(grid, db)
        config = ConfigManager(db)
        hmi = HMITerminal(scada, grid, db, config)

        if args.debug:
            print_info("Debug mode enabled")
            print_info(f"Database: {DB_PATH}")
            print_info(f"Config: {config.get_config_path()}")
            print_info(f"Devices: {len(grid.devices)}")

        # Login
        if hmi.login_screen():
            hmi.main_menu()

        # Cleanup
        db.close()
        clear_screen()
        print(f"\n{C.BCYAN}  Session terminated. Stay safe.{C.RESET}\n")

    except KeyboardInterrupt:
        print(f"\n\n{C.BYELLOW}  Session interrupted (Ctrl+C). Exiting...{C.RESET}\n")
        try:
            db.close()
        except:
            pass


if __name__ == "__main__":
    main()
