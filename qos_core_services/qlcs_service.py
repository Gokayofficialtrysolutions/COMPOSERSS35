# CHIMera QOS - Quantum Language Compilation Service (QLCS) Blueprint
# Version: 0.2 (Refined from phase1_qlcs_aes.py)

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import uuid

# Assuming GateType is defined (e.g., in a common types or from qhal_service.py)
# For blueprint purposes, we'll define it here if not found, but in implementation, it would be imported.
try:
    from .qhal_service import GateType # Attempt relative import if part of a package
except ImportError:
    try:
        from qhal_service import GateType # Attempt direct import if qhal_service is top-level accessible
    except ImportError:
        from enum import Enum
        class GateType(Enum): # Fallback definition
            I="IDENTITY"; X="PAULI_X"; Y="PAULI_Y"; Z="PAULI_Z"; H="HADAMARD"; S="S"; SDG="S_DAG"; T="T"; TDG="T_DAG"; SX="SQRT_X"; SXDG="SQRT_X_DAG"
            RZ="RZ_ANGLE"; RX="RX_ANGLE"; RY="RY_ANGLE"; U="U_UNIVERSAL"; P="PHASE_ANGLE"
            CX="CONTROLLED_X"; CY="CONTROLLED_Y"; CZ="CONTROLLED_Z"; SWAP="SWAP"
            CRX="CONTROLLED_RX"; CRY="CONTROLLED_RY"; CRZ="CONTROLLED_RZ"; CU="CONTROLLED_U"; CP="CONTROLLED_PHASE"
            CCX="TOFFOLI"; CSWAP="FREDKIN"
            MEASURE = "MEASURE"; RESET = "RESET"; BARRIER = "BARRIER"; DELAY = "DELAY_PULSE"


# --- QLCS Custom Exceptions ---
class QLCSError(Exception): """Base exception for QLCS errors."""
class QLCSParsingError(QLCSError): """Error during QASM parsing."""
class QLCSTranspilationError(QLCSError): """Error during transpilation to QHAL sequence."""
class QLCSUnsupportedFeatureError(QLCSTranspilationError): """Feature in input language not supported."""

# --- QLCS Data Structures ---
@dataclass
class QubitRequirement:
    """Specifies the number of logical qubits required by a program."""
    num_qubits: int
    # Could add: required_classical_registers: Dict[str, int] # name -> size

@dataclass
class QHALTranspiledSequence:
    """
    Represents a quantum program transpiled into a sequence executable by QHAL.
    This structure is an intermediate representation before it becomes a PTSS OperationSequence.
    """
    # For each gate in gate_info_sequence, this list contains the global QHAL IDs of qubits it acts upon.
    # e.g., [["dev1::q0"], ["dev1::q0", "dev1::q1"]] for H(q0) then CX(q0,q1)
    target_qubit_global_ids_per_gate: List[List[str]]

    # Sequence of (GateType, parameters_dict_for_QHAL_GateCommand)
    # Parameters dict matches GateCommand.parameters from QHAL.
    gate_info_sequence: List[Tuple[GateType, Optional[Dict[str, Any]]]]

    # List of global QHAL IDs of qubits that are measured in this sequence.
    measured_qubit_global_ids: List[str]

    # Total number of classical bits declared/used by the original program.
    # QHAL's measure operations might implicitly use these or require specific mapping.
    num_classical_bits_declared: int


# --- QLCS Abstract Interface ---
class AbstractQLCS(ABC):
    @abstractmethod
    def get_qubit_requirements(self, program_string: str, language_dialect: str = "OpenQASM2.0") -> QubitRequirement:
        """
        Parses the program string to determine resource requirements, primarily number of logical qubits.
        """
        pass

    @abstractmethod
    def transpile_to_qhal_sequence(self, program_string: str,
                                   qubit_mapping: Dict[int, str],
                                   language_dialect: str = "OpenQASM2.0") -> QHALTranspiledSequence:
        """
        Transpiles a program string (e.g., QASM) into a QHAL-executable sequence.
        Args:
            program_string: The quantum program as a string.
            qubit_mapping: A dictionary mapping logical qubit indices (from program_string)
                           to global QHAL qubit IDs. E.g., {0: "qpu1::q5", 1: "qpu1::q2"}
            language_dialect: Specifies the input language and version.
        Returns:
            A QHALTranspiledSequence object.
        Raises:
            QLCSParsingError, QLCSTranspilationError, QLCSUnsupportedFeatureError
        """
        pass

# --- QLCS Service Implementation (Qiskit-based for OpenQASM 2.0) ---
class QLCSService(AbstractQLCS):
    def __init__(self, shms_callback: Optional[Callable] = None):
        self._shms_callback = shms_callback
        self._qiskit_available = False
        self._QKCircuit_class: Optional[Type[QuantumCircuit]] = None
        self._qasm2_loads_func: Optional[Callable] = None

        try:
            from qiskit import QuantumCircuit as QKCircuit_import # type: ignore
            from qiskit.qasm2 import loads as qasm2_loads_import # type: ignore
            self._QKCircuit_class = QKCircuit_import
            self._qasm2_loads_func = qasm2_loads_import
            self._qiskit_available = True
            self._log("INFO", "QLCS initialized with Qiskit components.")
        except ImportError:
            self._log("ERROR", "QLCS FATAL: Qiskit not found. QLCS will not function for OpenQASM 2.0 transpilation.")
            # Depending on requirements, could raise an error here or allow QLCS to exist but fail operations.

        # Extended mapping from Qiskit op names to QHAL GateType
        self._gate_name_to_enum_map: Dict[str, GateType] = {
            "id": GateType.I, "x": GateType.X, "y": GateType.Y, "z": GateType.Z,
            "h": GateType.H, "s": GateType.S, "sdg": GateType.SDG, "t": GateType.T,
            "tdg": GateType.TDG, "sx": GateType.SX, "sxdg": GateType.SXDG,
            "rz": GateType.RZ, "rx": GateType.RX, "ry": GateType.RY,
            "u": GateType.U, "u3": GateType.U, # u3 is often the full U gate
            "u2": GateType.U, # u2(phi,lam) = U(pi/2, phi, lam)
            "u1": GateType.P, # u1(lam) = P(lam) = U(0,0,lam)
            "p": GateType.P,
            "cx": GateType.CX, "CX": GateType.CX, # Qiskit sometimes uses CX
            "cy": GateType.CY, "cz": GateType.CZ, "swap": GateType.SWAP,
            "ccx": GateType.CCX, "cswap": GateType.CSWAP,
            "crx": GateType.CRX, "cry": GateType.CRY, "crz": GateType.CRZ,
            "cu": GateType.CU, "cp": GateType.CP, "cu1": GateType.CP, "cu3": GateType.CU,
            "measure": GateType.MEASURE, "reset": GateType.RESET, "barrier": GateType.BARRIER,
            "delay": GateType.DELAY
        }

    def _log(self, level: str, message: str, data: Optional[Dict[str, Any]] = None):
        if self._shms_callback:
            log_entry = {"timestamp": time.time(), "source": "QLCS", "level": level, "message": message, "data": data or {}}
            self._shms_callback(log_entry)
        else: print(f"QLCS_LOG [{level}]: {message}" + (f" Data: {data}" if data else ""))

    def get_qubit_requirements(self, program_string: str, language_dialect: str = "OpenQASM2.0") -> QubitRequirement:
        if language_dialect.upper() != "OPENQASM2.0":
            raise QLCSUnsupportedFeatureError(f"Language dialect '{language_dialect}' not supported by this QLCS.")
        if not self._qiskit_available or not self._qasm2_loads_func:
            raise QLCSError("QLCS Internal Error: Qiskit components not loaded, cannot parse QASM.")
        try:
            circuit: QuantumCircuit = self._qasm2_loads_func(program_string)
            return QubitRequirement(num_qubits=circuit.num_qubits)
        except Exception as e:
            self._log("ERROR", f"QASM parsing failed for qubit requirement check: {e}", {"qasm_preview": program_string[:100]})
            raise QLCSParsingError(f"Invalid QASM 2.0 for qubit requirement check: {e}")

    def transpile_qasm_to_qhal_sequence(self, program_string: str,
                                   qubit_mapping: Dict[int, str],
                                   language_dialect: str = "OpenQASM2.0") -> QHALTranspiledSequence:
        if language_dialect.upper() != "OPENQASM2.0":
            raise QLCSUnsupportedFeatureError(f"Language dialect '{language_dialect}' not supported by this QLCS.")
        if not self._qiskit_available or not self._qasm2_loads_func or not self._QKCircuit_class:
            raise QLCSError("QLCS Internal Error: Qiskit components not loaded, cannot transpile QASM.")

        try:
            qiskit_circuit: QuantumCircuit = self._qasm2_loads_func(program_string)
        except Exception as e:
            self._log("ERROR", f"QASM parsing failed during transpilation: {e}", {"qasm_preview": program_string[:100]})
            raise QLCSParsingError(f"Invalid QASM 2.0 for transpilation: {e}")

        self._log("INFO", f"Transpiling QASM circuit with {qiskit_circuit.num_qubits} logical qubits. Mapping: {qubit_mapping}")

        qhal_targets_per_gate: List[List[str]] = []
        qhal_gate_info_sequence: List[Tuple[GateType, Optional[Dict[str, Any]]]] = []
        measured_qubit_global_ids_set: set[str] = set()

        if qiskit_circuit.num_qubits > len(qubit_mapping):
             raise QLCSTranspilationError(f"Insufficient qubit mapping: circuit needs {qiskit_circuit.num_qubits}, but mapping provides {len(qubit_mapping)}.")

        for instruction_obj, qargs, cargs in qiskit_circuit.data:
            op_name = instruction_obj.name.lower()
            qiskit_params = instruction_obj.params

            target_gate_type = self._gate_name_to_enum_map.get(op_name)
            if target_gate_type is None:
                raise QLCSUnsupportedFeatureError(f"Unsupported gate '{op_name}' in input QASM for QLCS Phase 1.")

            current_gate_target_global_ids: List[str] = []
            for qarg_qubit_obj in qargs:
                try:
                    logical_qubit_index = qiskit_circuit.qubits.index(qarg_qubit_obj)
                except ValueError:
                    raise QLCSTranspilationError(f"Qubit '{qarg_qubit_obj}' from instruction not found in circuit's qubit register.")

                global_id = qubit_mapping.get(logical_qubit_index)
                if global_id is None:
                    raise QLCSTranspilationError(f"No global QHAL ID provided in mapping for logical qubit index {logical_qubit_index}.")
                current_gate_target_global_ids.append(global_id)

            qhal_targets_per_gate.append(current_gate_target_global_ids)

            qhal_params: Optional[Dict[str, Any]] = None
            # Parameter mapping (this needs to be robust for all Qiskit gates to QHAL GateCommand params)
            # Example parameter mapping:
            if target_gate_type in [GateType.RZ, GateType.P, GateType.U1]:
                qhal_params = {'phi': float(qiskit_params[0])} # U1/P(lambda) -> RZ(lambda)
            elif target_gate_type in [GateType.RX, GateType.RY]:
                qhal_params = {'theta': float(qiskit_params[0])}
            elif target_gate_type == GateType.U2: # U2(phi,lam) = U(pi/2, phi, lam)
                 qhal_params = {'theta': np.pi/2, 'phi': float(qiskit_params[0]), 'lambda': float(qiskit_params[1])}
                 target_gate_type = GateType.U # Remap to U
            elif target_gate_type == GateType.U or target_gate_type == GateType.U3 : # U3 is U
                qhal_params = {'theta': float(qiskit_params[0]), 'phi': float(qiskit_params[1]), 'lambda': float(qiskit_params[2])}
            elif target_gate_type == GateType.DELAY:
                qhal_params = {'duration': float(qiskit_params[0]), 'unit': str(instruction_obj.unit)}
            # For gates like CX, CZ, SWAP, CCX, CSWAP, MEASURE, RESET, BARRIER, I, X, Y, Z, H, S, SDG, T, TDG, SX, SXDG
            # params are often None or implicit unless conditional.

            # Handle conditional gates if present (OpenQASM 2.0 `if (reg==val) op;`)
            if instruction_obj.condition:
                # condition is a tuple (ClassicalRegister, int) or (Clbit, int)
                # This needs to be mapped to QHAL's GateCommand.condition format.
                # For now, assume condition is (classical_reg_id, required_value)
                # This part is complex and needs careful mapping of Qiskit's condition object.
                # Placeholder:
                # qhal_params = qhal_params or {}
                # qhal_params["condition_register"] = instruction_obj.condition[0].name # Example
                # qhal_params["condition_value"] = int(instruction_obj.condition[1])
                self._log("WARNING", f"Conditional gate '{op_name}' encountered. QLCS Phase 1 conditional logic is conceptual.")


            qhal_gate_info_sequence.append((target_gate_type, qhal_params))

            if target_gate_type == GateType.MEASURE:
                # Qiskit measure(q,c) maps qarg[0] to carg[0]
                # We need to track which global qubits are measured.
                # Classical bit assignment is handled by QHAL/PTSS based on sequence.
                measured_qubit_global_ids_set.update(current_gate_target_global_ids)

        self._log("INFO", f"Transpilation successful. QHAL sequence length: {len(qhal_gate_info_sequence)}.")
        return QHALTranspiledSequence(
            target_qubit_global_ids_per_gate=qhal_targets_per_gate,
            gate_info_sequence=qhal_gate_info_sequence,
            measured_qubit_global_ids=list(measured_qubit_global_ids_set),
            num_classical_bits_declared=qiskit_circuit.num_clbits
        )

print("CHIMera QOS - QLCS Service Blueprint Definition Complete.")
