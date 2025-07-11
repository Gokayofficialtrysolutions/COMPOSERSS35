# CHIMera QOS - Quantum Hardware Abstraction Layer (QHAL) Service Blueprint
# Version: 0.2 (Consolidated & Refined)

import uuid
import time
import random
from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple, Union, Callable, Type
from dataclasses import dataclass, field

# --- QHAL Custom Exceptions ---

class QHALException(Exception):
    """Base exception for QHAL-related errors."""
    pass

class QHALConnectionError(QHALException):
    """Error during device connection or disconnection."""
    pass

class QHALDriverError(QHALException):
    """Error related to a specific QuantumDeviceDriver."""
    pass

class QHALExecutionError(QHALException):
    """Error during the execution of a quantum operation or sequence."""
    pass

class QHALCalibrationError(QHALException):
    """Error related to calibration routines or data."""
    pass

class QHALResourceError(QHALException):
    """Error related to qubit or device resource access."""
    pass


# --- QHAL Enums & Dataclasses ---

class QubitStatus(Enum):
    """Represents the operational status of a qubit."""
    IDLE = auto()
    ACTIVE = auto()
    CALIBRATING = auto()
    ERROR = auto()
    UNAVAILABLE = auto()

@dataclass
class QubitProperties:
    """
    Holds static and dynamic properties of a qubit.
    Fidelities are typically represented as probabilities (0.0 to 1.0).
    Coherence times are in seconds.
    """
    qubit_id: Any  # Local ID within its parent device driver
    global_qubit_id: Optional[str] = None # Globally unique ID, e.g., "device_id::local_qubit_id"
    t1_time: Optional[float] = None  # in seconds
    t2_star_time: Optional[float] = None  # in seconds
    t2_echo_time: Optional[float] = None # Hahn echo T2, often longer
    readout_fidelity: float = 0.99
    single_qubit_gate_fidelities: Dict[str, float] = field(default_factory=lambda: {"id": 1.0, "x": 0.999, "h": 0.998, "rz": 0.999})
    two_qubit_gate_fidelities: Dict[str, float] = field(default_factory=lambda: {"cx": 0.99, "cz":0.99})
    frequency_ghz: Optional[float] = 5.0
    anharmonicity_ghz: Optional[float] = -0.25 # Typically negative
    gate_times_ns: Dict[str, float] = field(default_factory=lambda: {"id": 10, "x": 30, "h": 30, "cx": 200, "measure": 1000})
    other_info: Dict[str, Any] = field(default_factory=dict) # For backend-specific extra properties

class GateType(Enum):
    """Standard gate operations supported by QHAL."""
    # Single Qubit Gates
    I = "IDENTITY"; X = "PAULI_X"; Y = "PAULI_Y"; Z = "PAULI_Z"; H = "HADAMARD"
    S = "S"; SDG = "S_DAG"; T = "T"; TDG = "T_DAG"; SX = "SQRT_X"; SXDG = "SQRT_X_DAG"
    RZ = "RZ_ANGLE"; RX = "RX_ANGLE"; RY = "RY_ANGLE"; U = "U_UNIVERSAL" # U(theta,phi,lambda)
    P = "PHASE_ANGLE" # P(lambda) equivalent to RZ(lambda) for some conventions or U(0,0,lambda)

    # Two Qubit Gates
    CX = "CONTROLLED_X"; CY = "CONTROLLED_Y"; CZ = "CONTROLLED_Z"; SWAP = "SWAP"
    CRX = "CONTROLLED_RX"; CRY = "CONTROLLED_RY"; CRZ = "CONTROLLED_RZ"; CU = "CONTROLLED_U"
    CP = "CONTROLLED_PHASE" # Controlled P(lambda)

    # Multi Qubit Gates (conceptual, decomposition may vary)
    CCX = "TOFFOLI" # Controlled-Controlled-X
    CSWAP = "FREDKIN" # Controlled-SWAP

    # Non-Unitary Operations
    MEASURE = "MEASURE"; RESET = "RESET"; BARRIER = "BARRIER"
    DELAY = "DELAY_PULSE" # Introduce a delay/wait time

@dataclass
class GateCommand:
    """Represents a single gate operation in a sequence for QHAL."""
    gate_type: GateType
    target_qubit_ids: List[Any] # Local IDs for the driver
    parameters: Optional[Dict[str, Any]] = None # e.g., {'phi': np.pi/2} for RZ, or control/target for multi-qubit
    condition: Optional[Tuple[Any, int]] = None # (classical_reg_id, required_value) for conditional execution

@dataclass
class PulseShape:
    """Describes a generic pulse. (Details depend on hardware capabilities)"""
    waveform_name: str  # e.g., 'gaussian', 'square', 'drag'
    duration_ns: float
    amplitude: float    # Arbitrary units or Volts, depending on backend
    frequency_mhz: Optional[float] = None # Carrier frequency, if applicable
    phase_rad: Optional[float] = 0.0
    parameters: Optional[Dict[str, Any]] = None # e.g., {'sigma_ns': 5, 'beta_drag': 0.1}
    channel_id: Optional[Any] = None # Target physical channel, if not implied by qubit

# --- QHAL Abstract Interfaces ---

class AbstractQubit(ABC):
    """Abstract representation of a single qubit managed by a QHAL driver."""
    @abstractmethod
    def get_id(self) -> Any:
        """Returns the local ID of the qubit within its parent device."""
        pass

    @abstractmethod
    def get_global_id(self) -> str:
        """Returns the globally unique ID of the qubit (device_id::local_id)."""
        pass

    @abstractmethod
    def get_status(self) -> QubitStatus:
        """Returns the current operational status of the qubit."""
        pass

    @abstractmethod
    def set_status(self, status: QubitStatus) -> None:
        """Sets the operational status of the qubit."""
        pass

    @abstractmethod
    def get_properties(self) -> QubitProperties:
        """Returns the static and dynamic properties of the qubit."""
        pass

    @abstractmethod
    def update_properties(self, new_properties: Dict[str, Any]) -> None:
        """Updates specific properties of the qubit, e.g., after calibration."""
        pass

class QuantumDeviceDriver(ABC):
    """
    Abstract interface for a driver controlling a specific quantum device (real or simulated).
    Manages local qubit IDs and translates QHAL commands into device-specific instructions.
    """
    def __init__(self, device_id: str, device_config: Dict[str, Any], qhal_service_callback: Callable):
        self.device_id: str = device_id
        self.config: Dict[str, Any] = device_config
        self._is_connected: bool = False
        self._qubits: Dict[Any, AbstractQubit] = {} # Local ID to Qubit object
        self._qhal_service_callback = qhal_service_callback # To notify QHALService of async events / status changes

    @abstractmethod
    def connect(self) -> None:
        """Establishes connection to the quantum device and initializes qubits."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnects from the quantum device."""
        pass

    def is_connected(self) -> bool:
        return self._is_connected

    @abstractmethod
    def get_device_name(self) -> str:
        """Returns a human-readable name or model of the device."""
        pass

    @abstractmethod
    def get_device_status(self) -> Dict[str, Any]:
        """Returns overall status of the device (e.g., 'ONLINE', 'MAINTENANCE', error codes)."""
        pass

    @abstractmethod
    def list_qubits(self) -> List[AbstractQubit]:
        """Returns a list of all qubit objects managed by this driver."""
        pass

    @abstractmethod
    def get_qubit(self, local_qubit_id: Any) -> Optional[AbstractQubit]:
        """Retrieves a specific qubit object by its local ID."""
        pass

    @abstractmethod
    def execute_gate_commands(self, commands: List[GateCommand]) -> Dict[str, Any]:
        """
        Executes a sequence of gate commands.
        Returns a dictionary, potentially with job ID, status, or immediate results for simulators.
        For hardware, this is likely asynchronous; QHALService will manage job status polling via PTSS.
        """
        pass

    @abstractmethod
    def apply_pulse_sequence(self, target_channel_or_qubit_id: Any, sequence: List[PulseShape]) -> None:
        """Applies a raw pulse sequence. (Advanced/Optional based on hardware support)"""
        raise NotImplementedError("Pulse control not implemented by this driver.")

    @abstractmethod
    def measure_qubits_blocking(self, local_qubit_ids: List[Any], measurement_options: Optional[Dict[str, Any]] = None) -> Dict[Any, int]:
        """
        Performs a blocking measurement of specified qubits.
        Returns a dictionary mapping local qubit ID to measurement outcome (0 or 1).
        This is more typical for simulators or very simple hardware interactions.
        """
        pass

    @abstractmethod
    def reset_qubits(self, local_qubit_ids: List[Any]) -> None:
        """Resets specified qubits to the |0> state."""
        pass

    @abstractmethod
    def run_calibration_routine(self, routine_name: str, target_qubits: Optional[List[Any]] = None, params: Optional[Dict[str,Any]] = None) -> Dict[str, Any]:
        """
        Initiates a calibration routine. Returns results or status.
        (e.g., 'T1_measurement', 'RB_single_qubit').
        """
        raise NotImplementedError("Calibration routines not implemented by this driver.")

    @abstractmethod
    def update_device_calibration_data(self, calibration_data: Dict[str, Any]) -> None:
        """
        Applies new calibration data to the device or updates driver's internal model.
        This could update QubitProperties.
        """
        pass

# --- QHAL Concrete Simulated Implementations ---

class SimulatedQubitImpl(AbstractQubit):
    def __init__(self, local_id: Any, global_id: str, initial_properties: Optional[QubitProperties] = None):
        self._local_id: Any = local_id
        self._global_id: str = global_id
        self._status: QubitStatus = QubitStatus.IDLE
        self._properties: QubitProperties
        if initial_properties:
            self._properties = initial_properties
            self._properties.qubit_id = local_id # Ensure local_id consistency
            self._properties.global_qubit_id = global_id
        else:
            self._properties = QubitProperties(qubit_id=local_id, global_qubit_id=global_id)

        # For basic simulation without full Qiskit state vector per qubit
        self._simulated_state_value: int = 0 # 0 or 1

    def get_id(self) -> Any: return self._local_id
    def get_global_id(self) -> str: return self._global_id
    def get_status(self) -> QubitStatus: return self._status
    def set_status(self, status: QubitStatus) -> None: self._status = status
    def get_properties(self) -> QubitProperties: return self._properties
    def update_properties(self, new_props_dict: Dict[str, Any]) -> None:
        for key, value in new_props_dict.items():
            if hasattr(self._properties, key):
                setattr(self._properties, key, value)
        # Potentially notify QHALService or log this update

class SimulatedQPU_Driver(QuantumDeviceDriver):
    """
    A simulated QPU driver, potentially using Qiskit Aer for backend operations if available.
    """
    def __init__(self, device_id: str, device_config: Dict[str, Any], qhal_service_callback: Callable):
        super().__init__(device_id, device_config, qhal_service_callback)
        self.num_qubits: int = device_config.get("num_qubits", 2)
        self._device_status_dict: Dict[str, Any] = {"state": "UNINITIALIZED", "message": "Driver created but not connected."}

        self._qiskit_qc_class: Optional[Type[QuantumCircuit]] = None
        self._qasm_simulator: Optional[Any] = None # QasmSimulator instance
        self._current_qiskit_circuit: Optional[QuantumCircuit] = None

        try:
            from qiskit import QuantumCircuit as QKCircuit # type: ignore
            from qiskit.providers.aer import QasmSimulator as QKQasmSimulator # type: ignore
            self._qiskit_qc_class = QKCircuit
            self._qasm_simulator = QKQasmSimulator()
            print(f"QHAL.SimulatedQPU_Driver[{self.device_id}]: Qiskit Aer found and will be used for simulation.")
        except ImportError:
            print(f"QHAL.SimulatedQPU_Driver[{self.device_id}]: Qiskit not found. Simulation will be highly simplified (placeholder).")

    def connect(self) -> None:
        if self._is_connected:
            print(f"QHAL.SimulatedQPU_Driver[{self.device_id}]: Already connected.")
            return

        self._qubits = {}
        for i in range(self.num_qubits):
            local_id = f"q{i}"
            global_id = f"{self.device_id}::{local_id}"
            # Example: Allow config to specify some properties
            qubit_config_props = self.config.get("qubit_properties", {}).get(local_id, {})
            props = QubitProperties(qubit_id=local_id, global_qubit_id=global_id, **qubit_config_props)
            self._qubits[local_id] = SimulatedQubitImpl(local_id, global_id, initial_properties=props)

        if self._qiskit_qc_class:
            self._current_qiskit_circuit = self._qiskit_qc_class(self.num_qubits, self.num_qubits) # Qubits, Classical bits

        self._is_connected = True
        self._device_status_dict = {"state": "ONLINE", "message": "Simulated device connected."}
        print(f"QHAL.SimulatedQPU_Driver[{self.device_id}]: Connected. {self.num_qubits} simulated qubits available.")

    def disconnect(self) -> None:
        self._is_connected = False
        self._qubits = {}
        self._current_qiskit_circuit = None
        self._device_status_dict = {"state": "OFFLINE", "message": "Simulated device disconnected."}
        print(f"QHAL.SimulatedQPU_Driver[{self.device_id}]: Disconnected.")

    def get_device_name(self) -> str:
        return self.config.get("model_name", f"SimulatedQPU-{self.num_qubits}q [{self.device_id}]")

    def get_device_status(self) -> Dict[str, Any]:
        return self._device_status_dict

    def list_qubits(self) -> List[AbstractQubit]:
        if not self._is_connected: return []
        return list(self._qubits.values())

    def get_qubit(self, local_qubit_id: Any) -> Optional[AbstractQubit]:
        if not self._is_connected: return None
        return self._qubits.get(local_qubit_id)

    def _get_qiskit_qubit_indices(self, local_ids: List[Any]) -> List[int]:
        indices = []
        for local_id in local_ids:
            try:
                # Assuming local_id is like "q0", "q1", etc.
                indices.append(int(str(local_id).replace("q", "")))
            except ValueError:
                raise QHALResourceError(f"Invalid local qubit ID format for Qiskit mapping: {local_id}")
        return indices

    def execute_gate_commands(self, commands: List[GateCommand]) -> Dict[str, Any]:
        if not self._is_connected: raise QHALConnectionError("Device not connected.")
        if not self._qiskit_qc_class or not self._current_qiskit_circuit:
            # Placeholder for non-Qiskit simulation: log commands
            print(f"QHAL.SimulatedQPU_Driver[{self.device_id}] (No Qiskit): Executing {len(commands)} gate commands (logging only).")
            for cmd in commands: print(f"  {cmd.gate_type.name} on {cmd.target_qubit_ids} with params {cmd.parameters}")
            return {"status": "SIMULATED_LOGGED", "job_id": f"sim_job_{uuid.uuid4().hex[:8]}"}

        # Using Qiskit
        q_circuit = self._current_qiskit_circuit # Continue building on the same circuit until measurement/reset

        for cmd in commands:
            q_indices = self._get_qiskit_qubit_indices(cmd.target_qubit_ids)
            params = cmd.parameters if cmd.parameters is not None else {}

            # Map GateType to Qiskit circuit methods
            # This mapping needs to be comprehensive
            if cmd.gate_type == GateType.I: q_circuit.id(q_indices[0])
            elif cmd.gate_type == GateType.X: q_circuit.x(q_indices[0])
            elif cmd.gate_type == GateType.H: q_circuit.h(q_indices[0])
            elif cmd.gate_type == GateType.RZ: q_circuit.rz(params.get('phi', 0.0), q_indices[0])
            elif cmd.gate_type == GateType.CX: q_circuit.cx(q_indices[0], q_indices[1])
            elif cmd.gate_type == GateType.BARRIER: q_circuit.barrier(q_indices if q_indices else None)
            # Add more gate mappings here...
            elif cmd.gate_type == GateType.MEASURE:
                # Measurement is handled by measure_qubits_blocking or as part of a full circuit run
                pass
            elif cmd.gate_type == GateType.RESET:
                 for q_idx in q_indices: q_circuit.reset(q_idx)
            else:
                print(f"QHAL.SimulatedQPU_Driver[{self.device_id}]: Gate {cmd.gate_type.name} not fully implemented in Qiskit sim. Skipping.")

        # print(f"QHAL.SimulatedQPU_Driver[{self.device_id}]: {len(commands)} commands appended to Qiskit circuit.")
        return {"status": "COMMANDS_APPENDED", "circuit_depth": q_circuit.depth()}


    def measure_qubits_blocking(self, local_qubit_ids: List[Any], measurement_options: Optional[Dict[str, Any]] = None) -> Dict[Any, int]:
        if not self._is_connected: raise QHALConnectionError("Device not connected.")
        if not self._qiskit_qc_class or not self._current_qiskit_circuit or not self._qasm_simulator:
            print(f"QHAL.SimulatedQPU_Driver[{self.device_id}] (No Qiskit): Performing placeholder measurement.")
            return {local_id: random.choice([0,1]) for local_id in local_qubit_ids}

        # Clone current circuit for measurement, as measurement is terminal for this Qiskit circuit object
        circuit_to_measure = self._current_qiskit_circuit.copy()

        qiskit_indices_to_measure = self._get_qiskit_qubit_indices(local_qubit_ids)

        # Ensure classical bits are available for all measurements
        num_measurements = len(qiskit_indices_to_measure)
        if circuit_to_measure.num_clbits < num_measurements:
            # This might happen if circuit was reset or classical bits weren't managed for this specific sequence
            # For simplicity, we assume here that Qiskit's measure will handle it or we add bits if needed.
            # A more robust way: QHALService or sequence planner ensures circuit has adequate classical bits.
            # For now, let's assume measure will map correctly if enough bits.
             print(f"Warning: Circuit has {circuit_to_measure.num_clbits} clbits, measuring {num_measurements} qubits.")


        # Map local_qubit_ids to their corresponding classical bit indices for the result
        measurement_map: Dict[Any, int] = {}
        for i, local_id in enumerate(local_qubit_ids):
            circuit_to_measure.measure(self._get_qiskit_qubit_indices([local_id])[0], i)
            measurement_map[local_id] = i

        shots = (measurement_options or {}).get("shots", 1) # For blocking measure, often 1 shot

        try:
            from qiskit import transpile # type: ignore
            transpiled_circuit = transpile(circuit_to_measure, self._qasm_simulator)
            job = self._qasm_simulator.run(transpiled_circuit, shots=shots)
            counts = job.result().get_counts(transpiled_circuit)

            # For single shot, get the first outcome string
            # Qiskit counts are little-endian strings.
            first_outcome_str = list(counts.keys())[0] if counts else '0'*num_measurements

            results: Dict[Any, int] = {}
            for local_id, clbit_idx in measurement_map.items():
                # Classical bits in Qiskit outcome string are typically reversed (c_N-1 ... c1 c0)
                char_idx_in_str = (num_measurements - 1) - clbit_idx
                if 0 <= char_idx_in_str < len(first_outcome_str):
                    results[local_id] = int(first_outcome_str[char_idx_in_str])
                else:
                    results[local_id] = 0 # Default if something is wrong with indexing

            # Optionally, reset self._current_qiskit_circuit here if measurement implies termination of current sequence
            # self._current_qiskit_circuit = self._qiskit_qc_class(self.num_qubits, self.num_qubits)
            return results
        except Exception as e:
            raise QHALExecutionError(f"Qiskit measurement failed: {e}")


    def reset_qubits(self, local_qubit_ids: List[Any]) -> None:
        if not self._is_connected: raise QHALConnectionError("Device not connected.")
        qiskit_indices = self._get_qiskit_qubit_indices(local_qubit_ids)
        if self._qiskit_qc_class and self._current_qiskit_circuit:
            for idx in qiskit_indices:
                self._current_qiskit_circuit.reset(idx)
        # Also update internal SimulatedQubit state if necessary (though Qiskit circuit handles sim state)
        for local_id in local_qubit_ids:
            qubit = self._qubits.get(local_id)
            if qubit and isinstance(qubit, SimulatedQubitImpl): # Check type
                qubit._simulated_state_value = 0
                qubit.set_status(QubitStatus.IDLE)
        # print(f"QHAL.SimulatedQPU_Driver[{self.device_id}]: Qubits {local_qubit_ids} reset command added to circuit.")

    def update_device_calibration_data(self, calibration_data: Dict[str, Any]) -> None:
        print(f"QHAL.SimulatedQPU_Driver[{self.device_id}]: Received calibration data (simulated update).")
        for local_qid, props_dict in calibration_data.get("qubits", {}).items():
            qubit = self.get_qubit(local_qid)
            if qubit:
                qubit.update_properties(props_dict)
                print(f"  Updated props for {local_qid}")

# --- QHAL Service Class ---
class QHALService:
    """
    Manages multiple QuantumDeviceDrivers and provides a unified interface
    to quantum hardware using global qubit IDs.
    """
    def __init__(self):
        self._drivers: Dict[str, QuantumDeviceDriver] = {}
        self._global_qubit_map: Dict[str, Tuple[str, Any]] = {} # global_id -> (device_id, local_id)
        self._qubit_objects_cache: Dict[str, AbstractQubit] = {} # global_id -> AbstractQubit object
        print("QHALService: Initialized.")

    def register_driver(self, driver_class: Type[QuantumDeviceDriver], device_id: str, device_config: Dict[str, Any]) -> bool:
        if device_id in self._drivers:
            print(f"QHALService: Driver for device '{device_id}' already registered.")
            return False
        try:
            driver = driver_class(device_id, device_config, qhal_service_callback=self._handle_driver_callback)
            driver.connect()
            if driver.is_connected():
                self._drivers[device_id] = driver
                self._update_global_qubit_map_for_driver(driver)
                print(f"QHALService: Driver for '{device_id}' ({driver.get_device_name()}) registered and connected.")
                return True
            else:
                print(f"QHALService: Driver for '{device_id}' failed to connect.")
                return False
        except Exception as e:
            print(f"QHALService: Error registering driver '{device_id}': {e}")
            return False

    def _handle_driver_callback(self, device_id: str, event_type: str, event_data: Dict[str, Any]):
        """Placeholder for handling asynchronous callbacks from drivers (e.g., job completion, errors)."""
        print(f"QHALService: Received callback from {device_id} - Type: {event_type}, Data: {event_data}")
        # This would typically involve updating job statuses, notifying other services (e.g., AES via PTSS).

    def _update_global_qubit_map_for_driver(self, driver: QuantumDeviceDriver):
        device_id = driver.device_id
        for qubit_obj in driver.list_qubits():
            local_id = qubit_obj.get_id()
            global_id = f"{device_id}::{local_id}"

            # Update qubit object's global ID and ensure its properties reflect this
            if isinstance(qubit_obj, SimulatedQubitImpl): # Or a more generic check
                 qubit_obj._global_id = global_id # Directly set if possible
                 qubit_obj.get_properties().global_qubit_id = global_id

            self._global_qubit_map[global_id] = (device_id, local_id)
            self._qubit_objects_cache[global_id] = qubit_obj

    def unregister_driver(self, device_id: str) -> bool:
        driver = self._drivers.pop(device_id, None)
        if driver:
            try:
                driver.disconnect()
            except Exception as e:
                print(f"QHALService: Error disconnecting driver '{device_id}': {e}")

            # Remove qubits associated with this driver from global maps
            qubits_to_remove = [gid for gid, (did, _) in self._global_qubit_map.items() if did == device_id]
            for global_id in qubits_to_remove:
                del self._global_qubit_map[global_id]
                if global_id in self._qubit_objects_cache:
                    del self._qubit_objects_cache[global_id]
            print(f"QHALService: Driver for '{device_id}' unregistered.")
            return True
        print(f"QHALService: No driver found for device ID '{device_id}' to unregister.")
        return False

    def list_available_devices(self) -> List[Dict[str, Any]]:
        return [{"device_id": did, "name": driver.get_device_name(), "status": driver.get_device_status()}
                for did, driver in self._drivers.items()]

    def get_all_global_qubits(self) -> List[AbstractQubit]:
        return list(self._qubit_objects_cache.values())

    def get_qubit_by_global_id(self, global_qubit_id: str) -> Optional[AbstractQubit]:
        return self._qubit_objects_cache.get(global_qubit_id)

    def _get_driver_and_local_ids_for_command(self, global_qubit_ids_for_gate: List[str]) -> Tuple[Optional[QuantumDeviceDriver], List[Any]]:
        """
        Validates that all global IDs map to the same driver and returns the driver and local IDs.
        Raises QHALResourceError if qubits are not found, or belong to different devices for a single command.
        """
        if not global_qubit_ids_for_gate:
            return None, []

        target_device_id: Optional[str] = None
        local_ids_for_gate: List[Any] = []

        for g_qid in global_qubit_ids_for_gate:
            map_entry = self._global_qubit_map.get(g_qid)
            if not map_entry:
                raise QHALResourceError(f"Global qubit ID '{g_qid}' not found.")

            current_device_id, local_id = map_entry
            if target_device_id is None:
                target_device_id = current_device_id
            elif target_device_id != current_device_id:
                raise QHALResourceError("All qubits in a single gate command must belong to the same device.")
            local_ids_for_gate.append(local_id)

        if target_device_id is None: # Should not happen if global_qubit_ids_for_gate is not empty and all map
             raise QHALResourceError("Could not determine target device for gate command.")

        driver = self._drivers.get(target_device_id)
        if not driver:
            raise QHALDriverError(f"Driver for device '{target_device_id}' not found or not active.")
        return driver, local_ids_for_gate


    def execute_circuit_sequence(self, sequence: List[GateCommand]) -> Dict[str, Any]:
        """
        Executes a list of GateCommand objects.
        This version assumes all commands in the sequence target the same device,
        determined by the first command with target qubits.
        A more advanced QHAL might batch commands per device.
        """
        if not sequence:
            return {"status": "NO_COMMANDS", "message": "Empty sequence provided."}

        # Determine target driver from the first command that has target qubits
        target_driver: Optional[QuantumDeviceDriver] = None

        # Group commands by device_id (in case a sequence spans multiple devices, though complex)
        # For now, assume a sequence targets one device, determined by its first qubit-targeting command.

        commands_for_driver: List[GateCommand] = []
        current_driver_id: Optional[str] = None

        for i, command in enumerate(sequence):
            if command.target_qubit_ids: # If command targets qubits
                # All qubits in *this* command must be on the same device
                try:
                    driver_for_command, local_ids = self._get_driver_and_local_ids_for_command(command.target_qubit_ids) # command.target_qubit_ids are global here

                    if driver_for_command is None: # Should be caught by _get_driver...
                        raise QHALDriverError(f"Could not resolve driver for command {i} targeting {command.target_qubit_ids}")

                    if current_driver_id is None:
                        current_driver_id = driver_for_command.device_id
                        target_driver = driver_for_command
                    elif current_driver_id != driver_for_command.device_id:
                        # This simple QHAL executes sequence on one device. If sequence targets multiple, it's an error.
                        raise QHALResourceError("Sequence targets multiple devices. This QHAL version expects single-device sequences.")

                    # Translate global IDs in command to local IDs for this driver
                    cmd_for_driver = GateCommand(
                        gate_type=command.gate_type,
                        target_qubit_ids=local_ids, # Now local IDs
                        parameters=command.parameters,
                        condition=command.condition
                    )
                    commands_for_driver.append(cmd_for_driver)

                except QHALException as e:
                    return {"status": "ERROR", "message": f"Error processing command {i}: {e}"}

            elif command.gate_type == GateType.BARRIER: # Barrier can be device-wide
                 if target_driver: # If a driver is already determined
                    commands_for_driver.append(GateCommand(gate_type=GateType.BARRIER, target_qubit_ids=[], parameters=command.parameters))
                 # Else, if it's the first command and a barrier, it's ambiguous without context.
                 # QOS control logic should ensure sequences are well-formed.
                 # For now, if no target_driver yet, a global barrier isn't directly handled here.
                 # It implies all active drivers should barrier. This needs orchestration.
                 # For simplicity, assume sequence targets a single device.
            else: # Gate that doesn't target specific qubits (e.g. DELAY might be device-wide)
                if target_driver: # Apply to the determined target_driver
                     commands_for_driver.append(command) # Assumes parameters are fine for driver
                else: # Cannot determine driver yet
                    print(f"Warning: Command {command.gate_type} without target qubits encountered before device context established. Ignoring.")


        if not target_driver or not commands_for_driver:
            # This can happen if sequence was only parameterless barriers or empty
            return {"status": "NO_VALID_COMMANDS_FOR_DRIVER", "message": "No executable commands for a specific driver found in sequence."}

        try:
            # print(f"QHALService: Sending {len(commands_for_driver)} commands to driver {target_driver.device_id}")
            return target_driver.execute_gate_commands(commands_for_driver)
        except QHALException as e:
            return {"status": "EXECUTION_FAILED", "driver_id": target_driver.device_id, "message": str(e)}


    def measure_qubits_globally(self, global_qubit_ids: List[str], measurement_options: Optional[Dict[str, Any]] = None) -> Dict[str, int]:
        if not global_qubit_ids: return {}

        # Assume all qubits are on the same device for this call for simplicity,
        # determined by the first qubit. A more complex QHAL would group by device.
        try:
            driver, local_ids = self._get_driver_and_local_ids_for_command(global_qubit_ids)
            if not driver:
                raise QHALResourceError("Could not determine target device for measurement.")

            local_results = driver.measure_qubits_blocking(local_ids, measurement_options)

            # Map local results back to global IDs
            global_results: Dict[str, int] = {}
            for i, g_qid in enumerate(global_qubit_ids):
                # This assumes local_results keys match the order of local_ids from _get_driver_and_local_ids_for_command
                # and that local_ids are in the same order as global_qubit_ids
                # A more robust mapping would use the local_id from self._global_qubit_map
                local_id_for_g_qid = self._global_qubit_map.get(g_qid, (None, None))[1]
                if local_id_for_g_qid is not None:
                     global_results[g_qid] = local_results.get(local_id_for_g_qid, -1) # Default to -1 if local_id somehow missing
                else:
                    global_results[g_qid] = -1 # Should not happen if _get_driver... worked

            return global_results
        except QHALException as e:
            print(f"QHALService: Error measuring qubits {global_qubit_ids}: {e}")
            return {g_qid: -1 for g_qid in global_qubit_ids}


    def reset_qubits_globally(self, global_qubit_ids: List[str]) -> None:
        if not global_qubit_ids: return
        try:
            driver, local_ids = self._get_driver_and_local_ids_for_command(global_qubit_ids)
            if not driver:
                raise QHALResourceError("Could not determine target device for reset.")
            driver.reset_qubits(local_ids)
        except QHALException as e:
            print(f"QHALService: Error resetting qubits {global_qubit_ids}: {e}")

    def get_all_qubit_properties_globally(self) -> Dict[str, QubitProperties]:
        """Returns a dictionary of all global qubit IDs to their properties."""
        all_props = {}
        for gid, q_obj in self._qubit_objects_cache.items():
            all_props[gid] = q_obj.get_properties()
        return all_props

    def update_qubit_properties_globally(self, global_qubit_id: str, property_updates: Dict[str, Any]) -> bool:
        qubit = self.get_qubit_by_global_id(global_qubit_id)
        if qubit:
            try:
                qubit.update_properties(property_updates)
                # Potentially notify the driver if it needs to be aware of property changes made via QHAL
                # driver_id, _ = self._global_qubit_map[global_qubit_id]
                # self._drivers[driver_id].notify_qubit_update(qubit.get_id(), property_updates) # If driver supports this
                return True
            except Exception as e:
                print(f"QHALService: Error updating properties for {global_qubit_id}: {e}")
                return False
        return False

print("CHIMera QOS - QHAL Service Blueprint Definition Complete.")
