#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║  ICS Power Grid Simulator — Grid Simulator Engine            ║
║  Manages zones, generators, transformers, and cascade logic  ║
╚══════════════════════════════════════════════════════════════╝
"""

import random
from plc_device import PLCDevice
from utils import C, timestamp


class PowerGrid:
    """
    Main power grid simulation engine.
    Manages all PLC devices and grid-wide state.
    """

    def __init__(self):
        self.devices = {}
        self.zones = {}
        self.total_generation = 0
        self.total_load = 0
        self.grid_frequency = 60.0
        self.grid_voltage = 230.0
        self.grid_stable = True
        self.cascade_active = False
        self.events = []
        self._initialize_grid()

    def _initialize_grid(self):
        """Build the simulated power grid topology."""

        # ── 6 Breaker Zones ──
        zone_names = [
            ("ZONE-A", "Downtown District"),
            ("ZONE-B", "Industrial Park"),
            ("ZONE-C", "Residential North"),
            ("ZONE-D", "Residential South"),
            ("ZONE-E", "Commercial Center"),
            ("ZONE-F", "Critical Infrastructure"),
        ]
        for zone_id, desc in zone_names:
            device = PLCDevice(
                device_id=f"BRK-{zone_id}",
                device_type="breaker",
                zone=zone_id,
                description=f"Main breaker — {desc}"
            )
            self.devices[device.device_id] = device
            self.zones[zone_id] = {
                "name": desc,
                "breaker": device.device_id,
                "load_mw": random.randint(200, 600),
                "consumers": random.randint(10000, 80000),
                "priority": "CRITICAL" if zone_id == "ZONE-F" else "NORMAL",
            }

        # ── 3 Generator Units ──
        gen_specs = [
            ("GEN-01", "Coal Turbine Alpha",    "ZONE-A"),
            ("GEN-02", "Gas Turbine Bravo",     "ZONE-B"),
            ("GEN-03", "Nuclear Unit Charlie",  "ZONE-F"),
        ]
        for gen_id, desc, zone in gen_specs:
            device = PLCDevice(
                device_id=gen_id,
                device_type="generator",
                zone=zone,
                description=desc
            )
            self.devices[gen_id] = device

        # ── 4 Transformer Substations ──
        xfmr_specs = [
            ("XFMR-01", "Substation North",  "ZONE-C"),
            ("XFMR-02", "Substation South",  "ZONE-D"),
            ("XFMR-03", "Substation East",   "ZONE-E"),
            ("XFMR-04", "Substation West",   "ZONE-A"),
        ]
        for xf_id, desc, zone in xfmr_specs:
            device = PLCDevice(
                device_id=xf_id,
                device_type="transformer",
                zone=zone,
                description=desc
            )
            self.devices[xf_id] = device

    def get_device(self, device_id):
        return self.devices.get(device_id)

    def get_all_devices(self):
        return list(self.devices.values())

    def get_devices_by_type(self, device_type):
        return [d for d in self.devices.values() if d.device_type == device_type]

    def get_zone_info(self, zone_id):
        return self.zones.get(zone_id)

    def get_all_zones(self):
        return dict(self.zones)

    # ─── Grid-Wide Metrics ───────────────────────────────────

    def calculate_grid_state(self):
        """Calculate overall grid metrics."""
        generators = self.get_devices_by_type("generator")
        breakers = self.get_devices_by_type("breaker")

        # Total generation
        self.total_generation = sum(
            d.get_status().get("output_mw", 0)
            for d in generators
            if d.online and not d.fault_state and d.get_status().get("running", False)
        )

        # Total load (from active zones)
        self.total_load = 0
        for zone_id, zone_info in self.zones.items():
            brk_device = self.devices.get(zone_info["breaker"])
            if brk_device and brk_device.online and not brk_device.fault_state:
                brk_status = brk_device.get_status()
                if brk_status.get("breaker_closed", False):
                    self.total_load += zone_info["load_mw"]

        # Frequency — deviates from 60Hz under imbalance
        if self.total_generation > 0:
            balance_ratio = self.total_load / self.total_generation
            freq_deviation = (balance_ratio - 1.0) * 5.0  # Simplified model
            self.grid_frequency = 60.0 - freq_deviation + random.uniform(-0.05, 0.05)
        else:
            self.grid_frequency = 0.0

        # Voltage — drops under overload
        transformers = self.get_devices_by_type("transformer")
        active_xfmrs = [t for t in transformers if t.online and not t.fault_state]
        if active_xfmrs:
            avg_secondary = sum(
                t.get_status().get("secondary_kv", 0) for t in active_xfmrs
            ) / len(active_xfmrs)
            self.grid_voltage = avg_secondary
        else:
            self.grid_voltage = 0.0

        # Stability check
        self.grid_stable = (
            55.0 <= self.grid_frequency <= 65.0 and
            self.grid_voltage > 100.0 and
            self.total_generation >= self.total_load * 0.5
        )

        online_count = sum(1 for d in self.devices.values() if d.online and not d.fault_state)
        total_count = len(self.devices)

        return {
            "total_generation_mw": self.total_generation,
            "total_load_mw": self.total_load,
            "frequency_hz": round(self.grid_frequency, 2),
            "voltage_kv": round(self.grid_voltage, 1),
            "grid_stable": self.grid_stable,
            "devices_online": online_count,
            "devices_total": total_count,
            "cascade_active": self.cascade_active,
        }

    # ─── Grid Control ───────────────────────────────────────

    def toggle_breaker(self, zone_id, close=True):
        """Toggle a zone breaker open/closed."""
        zone = self.zones.get(zone_id)
        if not zone:
            return {"status": "ERROR", "message": f"Zone {zone_id} not found"}

        brk = self.devices.get(zone["breaker"])
        if not brk:
            return {"status": "ERROR", "message": "Breaker device not found"}

        result = brk.process_modbus_command(0x05, 0, close)  # Write coil 0
        action = "CLOSED" if close else "OPENED"
        consumers = zone["consumers"]

        self.events.append({
            "time": timestamp(),
            "type": "BREAKER",
            "message": f"Breaker {zone_id} {action} — {consumers:,} consumers affected",
            "severity": "WARNING" if not close else "INFO",
        })

        return {
            "status": "OK",
            "message": f"Breaker {zone_id} ({zone['name']}) {action}",
            "consumers_affected": consumers,
        }

    def set_generator_output(self, gen_id, percentage):
        """Set generator output percentage."""
        gen = self.devices.get(gen_id)
        if not gen or gen.device_type != "generator":
            return {"status": "ERROR", "message": f"Generator {gen_id} not found"}

        # Write output percentage to register 4
        gen.process_modbus_command(0x06, 4, int(percentage))

        # Calculate new MW output (max ~1000MW per unit)
        new_mw = int(10 * percentage)
        gen.process_modbus_command(0x06, 1, new_mw)

        severity = "INFO"
        if percentage > 100:
            severity = "CRITICAL"
            self.events.append({
                "time": timestamp(),
                "type": "OVERLOAD",
                "message": f"⚠ Generator {gen_id} set to {percentage}% — OVERLOAD CONDITION",
                "severity": "CRITICAL",
            })
        elif percentage > 85:
            severity = "WARNING"

        self.events.append({
            "time": timestamp(),
            "type": "GENERATOR",
            "message": f"Generator {gen_id} output set to {percentage}% ({new_mw} MW)",
            "severity": severity,
        })

        return {
            "status": "OK",
            "message": f"Generator {gen_id} output: {percentage}% ({new_mw} MW)",
        }

    def cascade_failure(self):
        """Trigger a cascading blackout across all zones."""
        self.cascade_active = True
        results = []

        # Trip all breakers
        for zone_id in self.zones:
            result = self.toggle_breaker(zone_id, close=False)
            results.append(result)

        # Overload generators
        for gen in self.get_devices_by_type("generator"):
            gen.process_modbus_command(0x06, 4, 150)  # 150% output
            gen.fault_state = True

        self.events.append({
            "time": timestamp(),
            "type": "CASCADE",
            "message": "⚠ CASCADING FAILURE — Total grid blackout initiated",
            "severity": "CRITICAL",
        })

        return results

    def wipe_all_devices(self):
        """Execute KillDisk-style wipe on all PLCs."""
        results = []
        for device in self.devices.values():
            result = device.system_wipe()
            results.append({"device": device.device_id, **result})

        self.events.append({
            "time": timestamp(),
            "type": "KILLDISK",
            "message": "⚠ SYSTEM WIPE — All PLC firmware erased (KillDisk)",
            "severity": "CRITICAL",
        })

        return results

    def reset_grid(self):
        """Reset grid to default state."""
        self._initialize_grid()
        self.cascade_active = False
        self.events.append({
            "time": timestamp(),
            "type": "RESET",
            "message": "Grid reset to default state",
            "severity": "INFO",
        })

    def get_events(self, limit=30):
        return self.events[-limit:]

    def simulate_tick(self):
        """Advance simulation by one tick."""
        for device in self.devices.values():
            device.simulate_tick()
        self.calculate_grid_state()
