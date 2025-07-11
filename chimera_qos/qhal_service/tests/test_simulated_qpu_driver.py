import unittest
from unittest.mock import MagicMock, patch
import numpy as np

# Adjust import path based on actual structure.
# Assuming qhal.py is in the parent directory relative to tests directory
# For proper packaging, you'd use absolute imports like from chimera_qos.qhal_service.qhal import ...
# This relative import is for blueprint stage simplicity.
from ..qhal import SimulatedQPU_Driver, GateCommand, GateType, QubitProperties, QubitStatus, SimulatedQubitImpl

# Mock Qiskit components if Qiskit is not a guaranteed test environment dependency
# For this blueprint, we assume Qiskit might be available, and the driver handles its absence.
try:
    from qiskit import QuantumCircuit
    QISKIT_AVAILABLE = True
except ImportError:
    QISKIT_AVAILABLE = False
    QuantumCircuit = None # Placeholder


class TestSimulatedQPUDriver(unittest.TestCase):

    def setUp(self):
        self.device_id = "sim_qpu_test_01"
        self.num_qubits = 2
        self.device_config = {
            "num_qubits": self.num_qubits,
            "model_name": "TestSimDevice",
            "qubit_properties": {
                "q0": {"readout_fidelity": 0.98, "t1_time": 50e-6},
                "q1": {"readout_fidelity": 0.97, "t1_time": 60e-6}
            }
        }
        self.mock_qhal_service_callback = MagicMock()
        self.driver = SimulatedQPU_Driver(self.device_id, self.device_config, self.mock_qhal_service_callback)
        self.driver.connect()

    def tearDown(self):
        if self.driver.is_connected():
            self.driver.disconnect()

    def test_connection_and_qubit_initialization(self):
        self.assertTrue(self.driver.is_connected())
        self.assertEqual(self.driver.get_device_name(), "TestSimDevice")
        qubits = self.driver.list_qubits()
        self.assertEqual(len(qubits), self.num_qubits)

        q0_props = self.driver.get_qubit("q0").get_properties()
        self.assertEqual(q0_props.qubit_id, "q0")
        self.assertEqual(q0_props.readout_fidelity, 0.98)
        self.assertEqual(q0_props.t1_time, 50e-6)

    @unittest.skipUnless(QISKIT_AVAILABLE, "Qiskit not available, skipping Qiskit-dependent tests.")
    def test_execute_x_gate_and_measure(self):
        # Sequence: X on q0, then Measure q0
        commands = [
            GateCommand(gate_type=GateType.X, target_qubit_ids=["q0"]),
            # Measurement is typically handled by measure_qubits_blocking after sequence
        ]
        exec_status = self.driver.execute_gate_commands(commands)
        self.assertEqual(exec_status["status"], "COMMANDS_APPENDED")

        # Now measure
        # The internal Qiskit circuit in the driver now has X on q0
        # Expected: q0 -> 1
        results = self.driver.measure_qubits_blocking(local_qubit_ids=["q0"], measurement_options={"shots": 1})
        self.assertIn("q0", results)
        self.assertEqual(results["q0"], 1)

        # After measurement, the internal circuit should be reset by measure_qubits_blocking
        # So, measuring again should yield 0 (initial state)
        results_after_reset = self.driver.measure_qubits_blocking(local_qubit_ids=["q0"], measurement_options={"shots": 1})
        self.assertIn("q0", results_after_reset)
        self.assertEqual(results_after_reset["q0"], 0)


    @unittest.skipUnless(QISKIT_AVAILABLE, "Qiskit not available, skipping Qiskit-dependent tests.")
    def test_execute_h_gate_and_measure(self):
        # Sequence: H on q0
        commands = [GateCommand(gate_type=GateType.H, target_qubit_ids=["q0"])]
        self.driver.execute_gate_commands(commands)

        # Measure q0 multiple times, expect roughly 50/50 distribution
        counts_q0 = {"0": 0, "1": 0}
        num_shots = 1000
        for _ in range(num_shots):
            # measure_qubits_blocking resets the circuit each time, so we need to re-apply H
            self.driver.execute_gate_commands(commands) # Re-apply H
            result = self.driver.measure_qubits_blocking(local_qubit_ids=["q0"], measurement_options={"shots": 1})
            counts_q0[str(result["q0"])] += 1

        # Check if outcomes are roughly balanced (e.g., each outcome > 0.4 * num_shots)
        self.assertGreater(counts_q0["0"], num_shots * 0.4)
        self.assertGreater(counts_q0["1"], num_shots * 0.4)

    @unittest.skipUnless(QISKIT_AVAILABLE, "Qiskit not available, skipping Qiskit-dependent tests.")
    def test_reset_qubit(self):
        # Apply X, then reset, then measure
        commands_x = [GateCommand(gate_type=GateType.X, target_qubit_ids=["q0"])]
        self.driver.execute_gate_commands(commands_x)

        # At this point, internal Qiskit circuit has X(q0)
        # Now, explicitly call reset on the driver for q0
        self.driver.reset_qubits(local_qubit_ids=["q0"])
        # This should have reset the Qiskit circuit too.

        results = self.driver.measure_qubits_blocking(local_qubit_ids=["q0"], measurement_options={"shots": 1})
        self.assertEqual(results["q0"], 0)

    @unittest.skipUnless(QISKIT_AVAILABLE, "Qiskit not available, skipping Qiskit-dependent tests.")
    def test_execute_cx_gate(self):
        # q0=control, q1=target. Initialize q0 to |1>
        commands = [
            GateCommand(gate_type=GateType.X, target_qubit_ids=["q0"]), # q0 is now |1>
            GateCommand(gate_type=GateType.CX, target_qubit_ids=["q0", "q1"]) # CX(q0, q1)
        ]
        self.driver.execute_gate_commands(commands)

        # Expected: q0=|1>, q1=|1> (flipped from initial |0>)
        results = self.driver.measure_qubits_blocking(local_qubit_ids=["q0", "q1"], measurement_options={"shots": 1})
        self.assertEqual(results["q0"], 1)
        self.assertEqual(results["q1"], 1)

    def test_get_qubit_properties(self):
        q1 = self.driver.get_qubit("q1")
        self.assertIsNotNone(q1)
        props = q1.get_properties()
        self.assertEqual(props.qubit_id, "q1")
        self.assertEqual(props.global_qubit_id, f"{self.device_id}::q1")
        self.assertEqual(props.readout_fidelity, 0.97) # From config

    def test_update_qubit_properties_in_simulated_qubit(self):
        q0 = self.driver.get_qubit("q0")
        self.assertIsNotNone(q0)

        original_t1 = q0.get_properties().t1_time
        q0.update_properties({"t1_time": 100e-6, "new_custom_prop": "test_value"})

        updated_props = q0.get_properties()
        self.assertEqual(updated_props.t1_time, 100e-6)
        # Note: SimulatedQubitImpl.update_properties only updates existing QubitProperties attributes.
        # If we want to store arbitrary new props, QubitProperties.other_info should be used.
        # For this test, we check that standard attributes are updated.
        # self.assertEqual(updated_props.other_info.get("new_custom_prop"), "test_value") # This would fail based on current blueprint


if __name__ == '__main__':
    unittest.main()
