# CHIMera QOS - Physical Environment Control Service (PECS) Blueprint
# Version: 0.2 (Consolidated & Refined)

import time
import uuid
from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Callable, Type
from dataclasses import dataclass, field

# --- PECS Custom Exceptions ---

class PECSException(Exception):
    """Base exception for PECS-related errors."""
    pass

class PECSDeviceError(PECSException):
    """Error related to a specific environmental device."""
    pass

class PECSParameterError(PECSException):
    """Error related to accessing or setting a device parameter."""
    pass

class PECSCommandError(PECSException):
    """Error related to executing a command on a device."""
    pass

# --- PECS Enums & Dataclasses ---

class SubSystemType(Enum):
    """Categorizes the type of environmental sub-system."""
    CRYOGENICS = "Cryogenics"
    VACUUM = "VacuumSystem"
    LASER_SYSTEM = "LaserSystem"
    RF_ELECTRONICS = "RF_Electronics"
    MICROWAVE_GENERATOR = "MicrowaveGenerator"
    AWG = "ArbitraryWaveformGenerator"
    MAGNETIC_FIELD_CONTROL = "MagneticFieldControl"
    GENERAL_SENSOR = "GeneralSensor"
    POWER_SUPPLY_UNIT = "PowerSupplyUnit"
    INTERLOCK = "InterlockSystem"
    OTHER = "Other"

@dataclass
class ParameterDefinition:
    """Defines metadata for a device parameter."""
    name: str
    description: str
    unit: str
    data_type: Type # e.g., float, int, str, bool
    is_readable: bool = True
    is_writable: bool = False
    range_min: Optional[Any] = None
    range_max: Optional[Any] = None
    enum_values: Optional[List[Any]] = None # For parameters with discrete allowed values

@dataclass
class ParameterValue:
    """Represents the value of a monitored or controlled parameter."""
    value: Any
    unit: str
    timestamp: float = field(default_factory=time.time)
    status: str = "NORMAL"  # e.g., "NORMAL", "WARNING_LOW", "ALARM_HIGH", "STALE", "ERROR"

    # Optional metadata that could be copied from ParameterDefinition if needed here
    parameter_name: Optional[str] = None


# --- PECS Abstract Interfaces ---

class AbstractEnvironmentDevice(ABC):
    """
    Abstract Base Class for a generic environmental control or monitoring device
    managed by the Physical Environment Control Service (PECS).
    """
    def __init__(self, device_id: str, device_name: str, device_config: Dict[str, Any],
                 sub_system_type: SubSystemType, pecs_service_callback: Optional[Callable] = None):
        self.device_id: str = device_id
        self.device_name: str = device_name
        self.config: Dict[str, Any] = device_config
        self.sub_system_type: SubSystemType = sub_system_type
        self._is_connected: bool = False
        self._status_message: str = "Uninitialized"
        self._parameters: Dict[str, ParameterDefinition] = {} # name -> Definition
        self._pecs_callback = pecs_service_callback # For alerts or async status updates

    @abstractmethod
    def connect(self) -> bool:
        """Establishes connection to the physical device."""
        pass

    @abstractmethod
    def disconnect(self) -> bool:
        """Closes connection to the physical device."""
        pass

    def is_connected(self) -> bool: return self._is_connected

    def get_device_id(self) -> str: return self.device_id
    def get_device_name(self) -> str: return self.device_name
    def get_sub_system_type(self) -> SubSystemType: return self.sub_system_type

    @abstractmethod
    def get_device_status_summary(self) -> Dict[str, Any]:
        """Returns a brief summary of device health/status."""
        pass

    @abstractmethod
    def list_parameters(self) -> List[ParameterDefinition]:
        """Lists all parameters exposed by this device."""
        return list(self._parameters.values())

    @abstractmethod
    def get_parameter_value(self, parameter_name: str) -> ParameterValue:
        """Reads the current value of a specific parameter."""
        pass

    def get_multiple_parameter_values(self, parameter_names: List[str]) -> Dict[str, ParameterValue]:
        """Reads current values for multiple parameters."""
        return {name: self.get_parameter_value(name) for name in parameter_names}

    @abstractmethod
    def set_parameter_value(self, parameter_name: str, value: Any) -> bool:
        """Sets the value of a controllable parameter."""
        pass

    @abstractmethod
    def execute_command(self, command_name: str, args: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Executes a pre-defined command on the device (e.g., 'start_ramp', 'self_test')."""
        pass

    def _register_parameter(self, definition: ParameterDefinition):
        self._parameters[definition.name] = definition

    def _notify_pecs(self, event_type: str, data: Dict[str, Any]):
        if self._pecs_callback:
            try:
                self._pecs_callback(self.device_id, event_type, data)
            except Exception as e:
                print(f"PECSDEV_ERROR [{self.device_id}]: Failed to notify PECS: {e}")


# --- PECS Concrete Simulated Implementations ---

class SimulatedTemperatureController(AbstractEnvironmentDevice):
    def __init__(self, device_id: str, device_name: str, device_config: Dict[str, Any], pecs_service_callback: Optional[Callable] = None):
        super().__init__(device_id, device_name, device_config, SubSystemType.CRYOGENICS, pecs_service_callback)

        self._current_temp_K: float = float(device_config.get("initial_temp_K", 4.2))
        self._setpoint_K: float = float(device_config.get("setpoint_K", self._current_temp_K))
        self._min_temp_K: float = float(device_config.get("min_temp_K", 0.010))
        self._max_temp_K: float = float(device_config.get("max_temp_K", 300.0))
        self._cooling_power_W: float = float(device_config.get("cooling_power_W", 1.0)) # Effective
        self._heating_power_W: float = float(device_config.get("heating_power_W", 5.0))
        self._thermal_mass_J_per_K: float = float(device_config.get("thermal_mass_J_per_K", 1000.0))

        self._is_ramping: bool = False
        self._heater_on: bool = False
        self._heater_level_percent: float = 0.0 # 0-100
        self._last_update_time: float = time.time()

        self._register_parameter(ParameterDefinition("current_temperature_K", "Current stage temperature", "K", float, is_writable=False, range_min=0, range_max=500))
        self._register_parameter(ParameterDefinition("setpoint_temperature_K", "Target temperature for control loop", "K", float, True, self._min_temp_K, self._max_temp_K))
        self._register_parameter(ParameterDefinition("is_ramping", "Indicates if temperature is actively ramping to setpoint", "", bool, is_writable=False))
        self._register_parameter(ParameterDefinition("heater_power_percent", "Heater output level", "%", float, True, 0, 100))


    def connect(self) -> bool:
        self._is_connected = True; self._last_update_time = time.time(); self._status_message = "Connected"
        print(f"PECS.SimTempCtrl [{self.device_id}]: Connected."); return True

    def disconnect(self) -> bool:
        self._is_connected = False; self._status_message = "Disconnected"
        print(f"PECS.SimTempCtrl [{self.device_id}]: Disconnected."); return True

    def get_device_status_summary(self) -> Dict[str, Any]:
        self._update_simulated_state()
        return {
            "connection": "CONNECTED" if self._is_connected else "DISCONNECTED",
            "temperature_K": round(self._current_temp_K, 3),
            "setpoint_K": round(self._setpoint_K, 3),
            "ramping": self._is_ramping,
            "heater_active": self._heater_on,
            "status_message": self._status_message
        }

    def _update_simulated_state(self):
        if not self._is_connected: self._last_update_time = time.time(); return

        now = time.time()
        delta_time_s = now - self._last_update_time
        if delta_time_s <= 0.01: return # Avoid too frequent updates / zero delta

        # Simplified thermal model: P_net * dt = C * dT => dT = (P_net / C) * dt
        # P_net = P_heater - P_cooler (P_cooler is an effective constant cooling power here)

        effective_heater_W = (self._heater_level_percent / 100.0) * self._heating_power_W if self._heater_on else 0

        # Simple ramp logic
        if self._is_ramping:
            if abs(self._current_temp_K - self._setpoint_K) < 0.001 * self._setpoint_K: # within 0.1%
                self._current_temp_K = self._setpoint_K
                self._is_ramping = False
                self._heater_on = (self._current_temp_K > self._min_temp_K + 0.001) # Basic hold logic
                self._status_message = f"Setpoint {self._setpoint_K}K reached."
                self._notify_pecs("ramp_complete", {"setpoint_K": self._setpoint_K})
            elif self._current_temp_K < self._setpoint_K: # Heating needed
                self._heater_on = True
                # Assume heater is powerful enough to overcome cooling for ramp up
                net_power_W = effective_heater_W - self._cooling_power_W
                if net_power_W < 0 and self._current_temp_K < self._setpoint_K : # If heater not enough to heat
                     net_power_W = self._heating_power_W * 0.1 # Minimal heating if trying to ramp up but cooling is stronger

                delta_T = (net_power_W / self._thermal_mass_J_per_K) * delta_time_s
                self._current_temp_K = min(self._current_temp_K + delta_T, self._setpoint_K)
            elif self._current_temp_K > self._setpoint_K: # Cooling needed
                self._heater_on = False
                net_power_W = -self._cooling_power_W # Only cooling active
                delta_T = (net_power_W / self._thermal_mass_J_per_K) * delta_time_s
                self._current_temp_K = max(self._current_temp_K + delta_T, self._setpoint_K)
        else: # Not actively ramping, try to hold setpoint or drift if heater off
            if self._heater_on: # Holding
                net_power_W = effective_heater_W - self._cooling_power_W
                delta_T = (net_power_W / self._thermal_mass_J_per_K) * delta_time_s
                self._current_temp_K += delta_T
            else: # Drifting (only cooling)
                delta_T = (-self._cooling_power_W / self._thermal_mass_J_per_K) * delta_time_s
                self._current_temp_K += delta_T

        self._current_temp_K = max(self._current_temp_K, self._min_temp_K) # Physical floor
        self._current_temp_K = min(self._current_temp_K, self._max_temp_K) # Physical ceiling

        self._last_update_time = now

    def get_parameter_value(self, parameter_name: str) -> ParameterValue:
        if not self._is_connected: raise PECSDeviceError(f"Device {self.device_id} disconnected.")
        self._update_simulated_state()
        now = time.time()

        if parameter_name == "current_temperature_K":
            return ParameterValue(round(self._current_temp_K, 4), "K", now)
        elif parameter_name == "setpoint_temperature_K":
            return ParameterValue(round(self._setpoint_K, 4), "K", now)
        elif parameter_name == "is_ramping":
            return ParameterValue(self._is_ramping, "", now)
        elif parameter_name == "heater_power_percent":
            return ParameterValue(round(self._heater_level_percent,1) if self._heater_on else 0.0, "%", now)
        else:
            raise PECSParameterError(f"Unknown parameter '{parameter_name}' for device {self.device_id}")

    def set_parameter_value(self, parameter_name: str, value: Any) -> bool:
        if not self._is_connected: raise PECSDeviceError(f"Device {self.device_id} disconnected.")
        self._update_simulated_state()
        if parameter_name == "setpoint_temperature_K":
            try:
                new_setpoint = float(value)
                if not (self._min_temp_K <= new_setpoint <= self._max_temp_K):
                    self._status_message = f"Error: Setpoint {new_setpoint}K out of range."
                    raise PECSParameterError(self._status_message)
                self._setpoint_K = new_setpoint
                self._is_ramping = True
                self._status_message = f"Ramping to {self._setpoint_K}K."
                print(f"PECS.SimTempCtrl [{self.device_id}]: {self._status_message}")
                return True
            except ValueError:
                self._status_message = f"Error: Invalid value {value} for setpoint."
                raise PECSParameterError(self._status_message)
        elif parameter_name == "heater_power_percent":
            try:
                level = float(value)
                if not (0 <= level <= 100): raise PECSParameterError("Heater level must be 0-100.")
                self._heater_level_percent = level
                self._heater_on = level > 0
                self._is_ramping = False # Manual heater override stops ramp to setpoint
                self._status_message = f"Heater set to {level}%."
                return True
            except ValueError: raise PECSParameterError("Invalid heater level.")
        else:
            raise PECSParameterError(f"Parameter '{parameter_name}' is not writable or unknown for device {self.device_id}")

    def execute_command(self, command_name: str, args: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not self._is_connected: raise PECSDeviceError(f"Device {self.device_id} disconnected.")
        _args = args or {}
        if command_name == "start_ramp_to_setpoint":
            target = _args.get("target_K", self._setpoint_K) # Can optionally provide a new setpoint
            return {"success": self.set_parameter_value("setpoint_temperature_K", target), "message": self._status_message}
        elif command_name == "stop_ramp":
            self._is_ramping = False; self._heater_on = False; self._heater_level_percent = 0.0
            self._status_message = "Ramp stopped by command."
            return {"success": True, "message": self._status_message}
        raise PECSCommandError(f"Unknown command '{command_name}' for device {self.device_id}")


# --- PECS Service Class ---
class PECS_Service:
    def __init__(self, shms_integration_callback: Optional[Callable] = None):
        self._devices: Dict[str, AbstractEnvironmentDevice] = {}
        self._devices_by_subsystem: Dict[SubSystemType, List[AbstractEnvironmentDevice]] = {st: [] for st in SubSystemType}
        self._shms_callback = shms_integration_callback # For logging critical events/telemetry
        print("PECS_Service: Initialized.")

    def _log_to_shms(self, level: str, message: str, data: Optional[Dict[str, Any]] = None):
        if self._shms_callback:
            log_entry = {"timestamp": time.time(), "source": "PECS", "level": level, "message": message, "data": data or {}}
            self._shms_callback(log_entry)
        else: # Fallback to print if no SHMS
            print(f"PECS_LOG [{level}]: {message}" + (f" Data: {data}" if data else ""))

    def _internal_device_callback(self, device_id: str, event_type: str, event_data: Dict[str, Any]):
        """Callback for devices to report critical events to PECS/SHMS."""
        message = f"Device {device_id} reported event: {event_type}"
        self._log_to_shms("INFO", message, event_data)
        # Potentially trigger other actions based on event_type

    def register_device(self, device_class: Type[AbstractEnvironmentDevice], device_id: str, device_name: str,
                        device_config: Dict[str, Any], sub_system_type: SubSystemType) -> bool:
        if device_id in self._devices:
            self._log_to_shms("ERROR", f"Device ID '{device_id}' already registered.", {"device_name": device_name})
            return False
        try:
            device_driver = device_class(device_id, device_name, device_config, sub_system_type, self._internal_device_callback)
            if not device_driver.is_connected():
                device_driver.connect()

            if device_driver.is_connected():
                self._devices[device_id] = device_driver
                if sub_system_type not in self._devices_by_subsystem: self._devices_by_subsystem[sub_system_type] = []
                self._devices_by_subsystem[sub_system_type].append(device_driver)
                self._log_to_shms("INFO", f"Device '{device_name}' ({device_id}) registered to PECS.", {"sub_system": sub_system_type.value})
                return True
            else:
                self._log_to_shms("ERROR", f"Failed to connect device '{device_name}' ({device_id}).", {"config": device_config})
                return False
        except Exception as e:
            self._log_to_shms("ERROR", f"Exception registering device '{device_name}' ({device_id}): {e}", {"config": device_config})
            return False

    def unregister_device(self, device_id: str) -> bool:
        device = self._devices.pop(device_id, None)
        if device:
            sub_system = device.get_sub_system_type()
            if device in self._devices_by_subsystem.get(sub_system, []):
                self._devices_by_subsystem[sub_system].remove(device)
            try: device.disconnect()
            except Exception as e:
                self._log_to_shms("WARNING", f"Error disconnecting device '{device_id}': {e}")
            self._log_to_shms("INFO", f"Device '{device.get_device_name()}' ({device_id}) unregistered from PECS.")
            return True
        self._log_to_shms("WARNING", f"Attempt to unregister non-existent device ID '{device_id}'.")
        return False

    def get_all_devices_summary(self) -> List[Dict[str, Any]]:
        summaries = []
        for dev_id, dev_obj in self._devices.items():
            summaries.append({
                "device_id": dev_id, "device_name": dev_obj.get_device_name(),
                "sub_system": dev_obj.get_sub_system_type().value,
                "is_connected": dev_obj.is_connected(),
                "status_summary": dev_obj.get_device_status_summary() if dev_obj.is_connected() else {"state": "DISCONNECTED"}
            })
        return summaries

    def get_device_parameters(self, device_id: str) -> List[ParameterDefinition]:
        device = self._devices.get(device_id)
        if not device or not device.is_connected():
            raise PECSDeviceError(f"Device '{device_id}' not found or not connected.")
        return device.list_parameters()

    def read_device_parameter(self, device_id: str, parameter_name: str) -> ParameterValue:
        device = self._devices.get(device_id)
        if not device or not device.is_connected():
            raise PECSDeviceError(f"Device '{device_id}' not found or not connected.")
        return device.get_parameter_value(parameter_name)

    def write_device_parameter(self, device_id: str, parameter_name: str, value: Any) -> bool:
        device = self._devices.get(device_id)
        if not device or not device.is_connected():
            raise PECSDeviceError(f"Device '{device_id}' not found or not connected.")
        success = device.set_parameter_value(parameter_name, value)
        level = "INFO" if success else "ERROR"
        self._log_to_shms(level, f"Set parameter '{parameter_name}' to {value} for device '{device_id}'. Success: {success}")
        return success

    def send_device_command(self, device_id: str, command_name: str, args: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        device = self._devices.get(device_id)
        if not device or not device.is_connected():
            raise PECSDeviceError(f"Device '{device_id}' not found or not connected.")
        result = device.execute_command(command_name, args)
        self._log_to_shms("INFO", f"Command '{command_name}' sent to device '{device_id}'. Result: {result.get('status','unknown')}", {"args": args, "result": result})
        return result

    def get_subsystem_overview(self, sub_system_type: SubSystemType) -> List[Dict[str, Any]]:
        """Provides statuses for all devices within a given subsystem."""
        devices_in_subsystem = self._devices_by_subsystem.get(sub_system_type, [])
        return [
            {"device_id": dev.device_id, "device_name": dev.get_device_name(), "status": dev.get_device_status_summary()}
            for dev in devices_in_subsystem if dev.is_connected()
        ]

print("CHIMera QOS - PECS Service Blueprint Definition Complete.")
