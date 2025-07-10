# CHIMera QOS - Conceptual Core Services Interfaces and Classes
# Version: 0.1 (Draft) - Part 2: PECS

from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import time

print("CHIMera QOS - PECS Code Block Loading... Timestamp: " + str(time.time()))

# ==============================================================================
# SECTION 2: PECS (Physical Environment Control Service) - Interfaces & Simulators
# ==============================================================================

# --- PECS Enums & Dataclasses ---

class SubSystemType(Enum):
    """Categorizes the type of environmental sub-system."""
    CRYOGENICS = auto()
    VACUUM = auto()
    LASER_SYSTEM = auto()
    RF_ELECTRONICS = auto()
    MICROWAVE_GENERATOR = auto()
    AWG = auto()
    MAGNETIC_FIELD_CONTROL = auto()
    GENERAL_SENSOR = auto()
    POWER_SUPPLY_UNIT = auto()
    OTHER = auto()

@dataclass
class ParameterValue:
    """Represents the value of a monitored or controlled parameter."""
    value: Any
    unit: str
    timestamp: float # Unix timestamp
    status: str = "normal"  # e.g., "normal", "warning_low", "error"
    is_controllable: bool = False
    range_min: Optional[Any] = None
    range_max: Optional[Any] = None

# --- PECS Abstract Interfaces ---

class AbstractEnvironmentDevice(ABC):
    """
    Abstract Base Class for a generic environmental control or monitoring device
    managed by the Physical Environment Control Service (PECS).
    """
    @abstractmethod
    def __init__(self, device_id: str, device_config: Dict[str, Any], sub_system_type: SubSystemType):
        self.device_id: str = device_id
        self.config: Dict[str, Any] = device_config
        self.sub_system_type: SubSystemType = sub_system_type
        self._is_connected: bool = False

    @abstractmethod
    def connect(self) -> bool: pass
    @abstractmethod
    def disconnect(self) -> bool: pass
    @abstractmethod
    def get_device_name(self) -> str: pass
    @abstractmethod
    def get_status(self) -> Dict[str, ParameterValue]: pass
    @abstractmethod
    def set_parameter(self, parameter_name: str, value: Any) -> bool: pass
    @abstractmethod
    def execute_command(self, command_name: str, args: Optional[Dict[str, Any]] = None) -> Dict[str, Any]: pass
    def is_connected(self) -> bool: return self._is_connected

# --- PECS Concrete Simulated Implementations ---

class SimulatedTemperatureController(AbstractEnvironmentDevice):
    """Simulated temperature controller for a cryostat stage."""
    def __init__(self, device_id: str, device_config: Dict[str, Any]):
        super().__init__(device_id, device_config, SubSystemType.CRYOGENICS)
        self._name: str = device_config.get("name", "SimCryo-" + str(device_id))
        self._current_temp_K: float = float(device_config.get("initial_temp_K", 0.010))
        self._setpoint_K: float = float(device_config.get("setpoint_K", 0.010))
        self._min_temp_K: float = float(device_config.get("min_temp_K", 0.008))
        self._max_temp_K: float = float(device_config.get("max_temp_K", 450.0))
        self._cooling_rate_K_per_s: float = float(device_config.get("cooling_rate_K_per_s", 0.001))
        self._heating_rate_K_per_s: float = float(device_config.get("heating_rate_K_per_s", 0.01))
        self._is_ramping: bool = False
        self._last_update_time: float = time.time()

    def connect(self) -> bool: self._is_connected = True; self._last_update_time = time.time(); print("SimTC connected: "+self.device_id); return True
    def disconnect(self) -> bool: self._is_connected = False; print("SimTC disconnected: "+self.device_id); return True
    def get_device_name(self) -> str: return self._name

    def _update_simulated_temperature(self):
        if not self._is_connected or not self._is_ramping: self._last_update_time = time.time(); return
        delta_time_s = time.time() - self._last_update_time
        if delta_time_s <= 0: return
        if self._current_temp_K < self._setpoint_K:
            change = self._heating_rate_K_per_s * delta_time_s
            self._current_temp_K = min(self._current_temp_K + change, self._setpoint_K)
        elif self._current_temp_K > self._setpoint_K:
            change = self._cooling_rate_K_per_s * delta_time_s
            self._current_temp_K = max(self._current_temp_K - change, self._setpoint_K)
        if abs(self._current_temp_K - self._setpoint_K) < 0.0001:
            self._current_temp_K = self._setpoint_K; self._is_ramping = False
        self._last_update_time = time.time()

    def get_status(self) -> Dict[str, ParameterValue]:
        if not self._is_connected: return {"connection_status": ParameterValue("disconnected", "", time.time(), status="error")}
        self._update_simulated_temperature(); current_ts = self._last_update_time
        temp_status = "normal"
        if not (self._min_temp_K <= self._current_temp_K <= self._max_temp_K): temp_status = "error"

        return {
            "current_temperature": ParameterValue(round(self._current_temp_K, 3), "K", current_ts, temp_status, False, self._min_temp_K, self._max_temp_K),
            "setpoint_temperature": ParameterValue(round(self._setpoint_K, 3), "K", current_ts, "normal", True, self._min_temp_K, self._max_temp_K),
            "ramping_status": ParameterValue("active" if self._is_ramping else "idle", "", current_ts)
        }

    def set_parameter(self, parameter_name: str, value: Any) -> bool:
        if not self._is_connected: return False
        if parameter_name == "setpoint_temperature":
            try:
                new_setpoint = float(value)
                if not (self._min_temp_K <= new_setpoint <= self._max_temp_K):
                    print("SimTC Error: Setpoint out of range for " + self.device_id)
                    return False
                self._setpoint_K = new_setpoint; self._is_ramping = True; self._last_update_time = time.time()
                return True
            except ValueError: return False
        return False

    def execute_command(self, command_name: str, args: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not self._is_connected: return {"status": "error", "message": "Device disconnected."}
        _args = args or {}
        if command_name == "start_cooldown_sequence":
            target = _args.get("target_K", self._min_temp_K + 0.002)
            self.set_parameter("setpoint_temperature", target)
            return {"status": "success", "message": "Cooldown initiated for " + self.device_id}
        elif command_name == "start_warmup_sequence":
            target = _args.get("target_K", min(290.0, self._max_temp_K))
            self.set_parameter("setpoint_temperature", target)
            return {"status": "success", "message": "Warmup initiated for " + self.device_id}
        elif command_name == "stop_ramp":
            self._is_ramping = False
            return {"status": "success", "message": "Ramp stopped for " + self.device_id}
        return {"status": "error", "message": "Unknown command for " + self.device_id + ": " + command_name}

# --- PECS Service Class Outline ---
class PECS:
    def __init__(self, shms_instance: Optional[Any] = None):
        self._devices: Dict[str, AbstractEnvironmentDevice] = {}
        self._devices_by_subsystem: Dict[SubSystemType, List[AbstractEnvironmentDevice]] = {st: [] for st in SubSystemType}
        self.shms = shms_instance
        print("PECS initialized.")

    def register_device(self, device_driver: AbstractEnvironmentDevice) -> bool:
        device_id = device_driver.device_id
        if device_id in self._devices: print("PECS Error: Device ID already registered: " + device_id); return False
        try:
            if not device_driver.is_connected(): device_driver.connect()
            if device_driver.is_connected():
                self._devices[device_id] = device_driver
                self._devices_by_subsystem[device_driver.sub_system_type].append(device_driver)
                print("PECS: Device registered: " + device_driver.get_device_name())
                return True
        except Exception as e: print("PECS Error on register: " + str(e))
        return False

    def unregister_device(self, device_id: str) -> bool:
        if device_id not in self._devices: return False
        device = self._devices.pop(device_id)
        if device in self._devices_by_subsystem.get(device.sub_system_type, []):
            self._devices_by_subsystem[device.sub_system_type].remove(device)
        try: device.disconnect()
        except Exception as e: print("PECS Warning: Error disconnecting " + device_id + ": " + str(e))
        return True

    def get_all_device_statuses(self) -> Dict[str, Dict[str, ParameterValue]]:
        return {did: dev.get_status() for did, dev in self._devices.items() if dev.is_connected()}

    def get_device_status(self, device_id: str) -> Optional[Dict[str, ParameterValue]]:
        dev = self._devices.get(device_id)
        if dev and dev.is_connected(): return dev.get_status()
        return None

    def control_device_parameter(self, device_id: str, parameter_name: str, value: Any) -> bool:
        dev = self._devices.get(device_id)
        if dev and dev.is_connected(): return dev.set_parameter(parameter_name, value)
        return False

    def issue_device_command(self, device_id: str, command_name: str, args: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        dev = self._devices.get(device_id)
        if dev and dev.is_connected(): return dev.execute_command(command_name, args)
        return {"status":"error", "message":"Device not found/connected."}

    def perform_all_devices_health_check(self):
        print("PECS: Performing health checks...")
        # In a real system, this would iterate, check param_value.status, and report to SHMS
        print("PECS: Health checks done.")

print("CHIMera QOS - PECS Code Block Definition Complete.")
```
