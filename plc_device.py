#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║  ICS Power Grid Simulator — PLC Device Module                ║
║  Simulated Programmable Logic Controllers                    ║
║                                                              ║
║  ⚠ INTENTIONAL VULNERABILITIES:                              ║
║    - Unauthenticated Modbus read/write (Stuxnet recon)       ║
║    - Buffer overflow on oversized register writes            ║
║      (CVE-2015-7937 — Schneider Modicon)                     ║
║    - Insecure firmware upload with no signature check         ║
║      (TRITON/TRISIS style)                                   ║
╚══════════════════════════════════════════════════════════════╝
"""

import random
import time
from utils import C, timestamp


class PLCRegister:
    """Simulates a PLC register bank (coils + holding registers)."""

    # VULNERABILITY: Fixed-size register bank — writes beyond this corrupt state
    MAX_REGISTERS = 100
    MAX_COILS = 50

    def __init__(self):
        self.holding_registers = [0] * self.MAX_REGISTERS
        self.coils = [False] * self.MAX_COILS
        self.input_registers = [0] * self.MAX_REGISTERS  # read-only in real PLCs

    def read_register(self, address):
        """Read a holding register."""
        if 0 <= address < self.MAX_REGISTERS:
            return self.holding_registers[address]
        return None

    def write_register(self, address, value):
        """
        Write to a holding register.
        
        ⚠ VULNERABILITY: BUFFER OVERFLOW — No bounds checking!
        Writing beyond MAX_REGISTERS corrupts adjacent memory (state).
        Real-world: CVE-2015-7937 (Schneider Modicon M340)
        """
        # VULNERABLE: No upper bound check allows out-of-bounds write
        if address >= 0:
            try:
                if address < self.MAX_REGISTERS:
                    self.holding_registers[address] = value
                else:
                    # "Buffer overflow" — corrupts coil state by overwriting
                    overflow_idx = address - self.MAX_REGISTERS
                    if overflow_idx < self.MAX_COILS:
                        self.coils[overflow_idx] = bool(value)
                    return "OVERFLOW"
                return "OK"
            except (IndexError, Exception):
                return "FAULT"
        return "INVALID"

    def read_coil(self, address):
        """Read a coil (boolean) value."""
        if 0 <= address < self.MAX_COILS:
            return self.coils[address]
        return None

    def write_coil(self, address, value):
        """
        Write to a coil.
        
        ⚠ VULNERABILITY: NO AUTHENTICATION required for coil writes.
        Real-world: Modbus TCP has zero built-in authentication.
        Used in Stuxnet reconnaissance phase.
        """
        if 0 <= address < self.MAX_COILS:
            self.coils[address] = bool(value)
            return "OK"
        return "INVALID"


class PLCDevice:
    """
    Simulates a single PLC device — represents a field device
    controlling physical infrastructure (breakers, generators, etc.)
    """

    def __init__(self, device_id, device_type, zone, description=""):
        self.device_id = device_id
        self.device_type = device_type  # "breaker", "generator", "transformer"
        self.zone = zone
        self.description = description
        self.registers = PLCRegister()
        self.online = True
        self.firmware_version = "1.0.0"
        self.firmware_data = None
        self.uptime = 0
        self.last_command = None
        self.last_command_time = None
        self.fault_state = False
        self.locked = False  # Safety interlock

        # Initialize device-specific registers
        self._init_device_registers()

    def _init_device_registers(self):
        """Set up initial register values based on device type."""
        if self.device_type == "breaker":
            # Register 0: Breaker status (1=closed/ON, 0=open/OFF)
            self.registers.write_register(0, 1)
            # Register 1: Current flow (amps)
            self.registers.write_register(1, random.randint(200, 800))
            # Register 2: Voltage (kV * 10)
            self.registers.write_register(2, 2300)  # 230.0 kV
            # Register 3: Fault flag
            self.registers.write_register(3, 0)
            # Coil 0: Breaker trip command
            self.registers.write_coil(0, True)

        elif self.device_type == "generator":
            # Register 0: Generator status (1=running, 0=stopped)
            self.registers.write_register(0, 1)
            # Register 1: Output power (MW)
            self.registers.write_register(1, random.randint(500, 900))
            # Register 2: Frequency (Hz * 100)
            self.registers.write_register(2, 6000)  # 60.00 Hz
            # Register 3: Temperature (°C)
            self.registers.write_register(3, random.randint(65, 85))
            # Register 4: Output percentage (0-100)
            self.registers.write_register(4, 75)
            # Register 5: RPM
            self.registers.write_register(5, 3600)

        elif self.device_type == "transformer":
            # Register 0: Transformer status (1=online, 0=offline)
            self.registers.write_register(0, 1)
            # Register 1: Primary voltage (kV * 10)
            self.registers.write_register(1, 5000)  # 500.0 kV
            # Register 2: Secondary voltage (kV * 10)
            self.registers.write_register(2, 2300)  # 230.0 kV
            # Register 3: Temperature (°C)
            self.registers.write_register(3, random.randint(55, 75))
            # Register 4: Load percentage
            self.registers.write_register(4, random.randint(40, 80))
            # Register 5: Oil level percentage
            self.registers.write_register(5, random.randint(85, 98))

    def process_modbus_command(self, function_code, address, value=None):
        """
        Process a Modbus-like command.
        
        ⚠ VULNERABILITY: No authentication — any user can send any command.
        Real-world: Modbus TCP protocol has zero authentication by design.
        
        Function codes:
          0x01 — Read Coil
          0x02 — Read Input Register
          0x03 — Read Holding Register
          0x05 — Write Single Coil
          0x06 — Write Single Register
          0x0F — Write Multiple Coils
          0x10 — Write Multiple Registers
          0xFF — Diagnostic / System Command
        """
        if not self.online:
            return {"status": "DEVICE_OFFLINE", "device": self.device_id}

        self.last_command = f"FC={hex(function_code)} ADDR={address} VAL={value}"
        self.last_command_time = timestamp()

        result = {"device": self.device_id, "function": hex(function_code)}

        if function_code == 0x01:  # Read Coil
            val = self.registers.read_coil(address)
            result.update({"status": "OK", "value": val})

        elif function_code == 0x02:  # Read Input Register
            val = self.registers.input_registers[address] if 0 <= address < PLCRegister.MAX_REGISTERS else None
            result.update({"status": "OK", "value": val})

        elif function_code == 0x03:  # Read Holding Register
            val = self.registers.read_register(address)
            result.update({"status": "OK", "value": val})

        elif function_code == 0x05:  # Write Coil
            status = self.registers.write_coil(address, value)
            result.update({"status": status})
            # If breaker trip coil toggled, update breaker status
            if self.device_type == "breaker" and address == 0:
                self.registers.write_register(0, 1 if value else 0)

        elif function_code == 0x06:  # Write Holding Register
            status = self.registers.write_register(address, value)
            result.update({"status": status})
            if status == "OVERFLOW":
                result["warning"] = "REGISTER_OVERFLOW — Memory corruption possible"
                self.fault_state = True

        elif function_code == 0xFF:  # Diagnostic / System
            result.update(self._handle_system_command(address, value))

        else:
            result.update({"status": "UNSUPPORTED_FUNCTION"})

        return result

    def _handle_system_command(self, cmd_type, data):
        """
        Handle system-level PLC commands.
        
        ⚠ VULNERABILITY: Destructive commands available without authorization.
        """
        if cmd_type == 0x00:  # Device info
            return {
                "status": "OK",
                "info": {
                    "device_id": self.device_id,
                    "type": self.device_type,
                    "firmware": self.firmware_version,
                    "uptime": self.uptime,
                    "online": self.online,
                    "fault": self.fault_state,
                }
            }

        elif cmd_type == 0x01:  # Restart device
            self.fault_state = False
            self._init_device_registers()
            return {"status": "OK", "message": "Device restarted"}

        elif cmd_type == 0x02:  # Force offline
            self.online = False
            return {"status": "OK", "message": "Device forced OFFLINE"}

        elif cmd_type == 0xFE:  # Flash firmware
            return self.flash_firmware(data)

        elif cmd_type == 0xFF:  # SYSTEM WIPE (KillDisk equivalent)
            return self.system_wipe()

        return {"status": "UNKNOWN_COMMAND"}

    def flash_firmware(self, firmware_data):
        """
        Flash firmware to the PLC.
        
        ⚠ VULNERABILITY: NO SIGNATURE VERIFICATION!
        Any data is accepted as valid firmware.
        Real-world: TRITON/TRISIS (2017) — attacked Schneider Triconex SIS
        """
        if firmware_data is None:
            return {"status": "ERROR", "message": "No firmware data provided"}

        # VULNERABLE: Accepts ANY data without checking signatures or integrity
        self.firmware_data = firmware_data
        self.firmware_version = f"CUSTOM-{hash(str(firmware_data)) % 10000:04d}"

        # Check if firmware is "malicious" (contains trigger words)
        fw_str = str(firmware_data).lower()
        if any(keyword in fw_str for keyword in ["malicious", "exploit", "payload", "shell"]):
            self.fault_state = True
            self.online = False
            return {
                "status": "FIRMWARE_CORRUPTED",
                "message": "⚠ Malicious firmware detected AFTER flashing — device BRICKED!"
            }

        return {
            "status": "OK",
            "message": f"Firmware flashed successfully — Version: {self.firmware_version}",
            "warning": "⚠ No signature verification was performed"
        }

    def system_wipe(self):
        """
        Execute a system wipe — destroys all PLC state.
        
        ⚠ VULNERABILITY: KillDisk-style destructive command with NO confirmation.
        Real-world: Ukraine 2015 — Industroyer/CrashOverride (2016)
        """
        self.registers = PLCRegister()  # Wipe all registers
        self.firmware_version = "WIPED"
        self.firmware_data = None
        self.online = False
        self.fault_state = True
        return {
            "status": "WIPED",
            "message": "⚠ SYSTEM WIPE EXECUTED — All registers cleared, firmware erased, device OFFLINE"
        }

    def get_status(self):
        """Return current device status."""
        status = "FAULT" if self.fault_state else ("ONLINE" if self.online else "OFFLINE")

        info = {
            "device_id": self.device_id,
            "type": self.device_type,
            "zone": self.zone,
            "status": status,
            "firmware": self.firmware_version,
            "description": self.description,
        }

        if self.device_type == "breaker":
            breaker_on = self.registers.read_register(0) == 1
            info.update({
                "breaker_closed": breaker_on,
                "current_amps": self.registers.read_register(1),
                "voltage_kv": self.registers.read_register(2) / 10.0,
                "fault_flag": self.registers.read_register(3),
            })
        elif self.device_type == "generator":
            info.update({
                "running": self.registers.read_register(0) == 1,
                "output_mw": self.registers.read_register(1),
                "frequency_hz": self.registers.read_register(2) / 100.0,
                "temperature_c": self.registers.read_register(3),
                "output_pct": self.registers.read_register(4),
                "rpm": self.registers.read_register(5),
            })
        elif self.device_type == "transformer":
            info.update({
                "active": self.registers.read_register(0) == 1,
                "primary_kv": self.registers.read_register(1) / 10.0,
                "secondary_kv": self.registers.read_register(2) / 10.0,
                "temperature_c": self.registers.read_register(3),
                "load_pct": self.registers.read_register(4),
                "oil_level_pct": self.registers.read_register(5),
            })

        return info

    def simulate_tick(self):
        """Simulate one time tick — update readings with slight variance."""
        if not self.online or self.fault_state:
            return

        self.uptime += 1

        if self.device_type == "breaker":
            if self.registers.read_register(0) == 1:  # breaker closed
                # Fluctuate current
                current = self.registers.read_register(1)
                current += random.randint(-20, 20)
                current = max(0, min(current, 1200))
                self.registers.write_register(1, current)

        elif self.device_type == "generator":
            if self.registers.read_register(0) == 1:  # running
                # Fluctuate frequency around 60Hz
                freq = self.registers.read_register(2)
                freq += random.randint(-5, 5)
                freq = max(5900, min(freq, 6100))
                self.registers.write_register(2, freq)
                # Temperature fluctuation
                temp = self.registers.read_register(3)
                temp += random.randint(-1, 2)
                temp = max(50, min(temp, 120))
                self.registers.write_register(3, temp)

        elif self.device_type == "transformer":
            if self.registers.read_register(0) == 1:  # online
                # Temperature fluctuation
                temp = self.registers.read_register(3)
                temp += random.randint(-1, 1)
                temp = max(40, min(temp, 100))
                self.registers.write_register(3, temp)
                # Load fluctuation
                load = self.registers.read_register(4)
                load += random.randint(-2, 2)
                load = max(10, min(load, 100))
                self.registers.write_register(4, load)
