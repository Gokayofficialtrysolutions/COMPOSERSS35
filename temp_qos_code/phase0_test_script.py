# temp_qos_code/phase0_test_script.py
# CHIMera QOS - Phase 0 - Basic Test/Usage Script

import time
import sys # For potential path manipulation if modules are in subdirs
import os  # For potential path manipulation

# This script assumes that phase0_qhal.py, phase0_pecs.py, and phase0_ptss_stub.py
# are in the same directory or accessible via PYTHONPATH.
# If they are in a sub-directory (e.g., 'interfaces'), you might need:
# sys.path.append(os.path.join(os.path.dirname(__file__), 'interfaces'))

try:
    from phase0_qhal import (QubitStatus, QubitProperties, GateType, AbstractQubit,
                             QuantumDeviceDriver, SimulatedQubit, SimulatedQPU_Driver, QHALService)
    from phase0_pecs import (SubSystemType, ParameterValue, AbstractEnvironmentDevice,
                             SimulatedTemperatureController, PECS)
    from phase0_ptss_stub import (PTSS_Stub, LogicalOperation, OperationSequence, OperationPriority)
except ImportError as e:
    print(f"ImportError: {e}. Please ensure all phase0_*.py files are in the same directory or PYTHONPATH.")
    print("This script expects to be run from the 'temp_qos_code' directory or have it in path.")
    sys.exit(1)


def run_phase0_demo():
    print("\n--- CHIMera QOS Phase 0 Demo Script ---")

    # 1. Initialize Services
    print("\n[1. Initializing Core Services (Phase 0 stubs/simulators)]")
    qhal_service = QHALService()
    pecs_service = PECS()
    ptss_stub = PTSS_Stub(qhal_service_instance=qhal_service)

    # 2. Configure and Register Simulated Hardware
    print("\n[2. Configuring and Registering Simulated Hardware]")
    qpu_config = {"num_qubits": 2, "model_name": "MySimQPU_2Q"}
    sim_qpu_driver = SimulatedQPU_Driver(device_id="qpu0", device_config=qpu_config)
    qhal_service.register_driver(sim_qpu_driver)

    temp_controller_config = {"name": "Cryo MC Plate", "initial_temp_K": 0.015}
    sim_tc_driver = SimulatedTemperatureController(device_id="tc_mc", device_config=temp_controller_config)
    pecs_service.register_device(sim_tc_driver)

    # 3. Check Initial Status
    print("\n[3. Checking Initial Hardware and Environment Status]")
    qpu_status_dict = sim_qpu_driver.get_status() # Direct driver status
    print("  Simulated QPU Driver Status: " + str(qpu_status_dict))

    tc_status_dict = pecs_service.get_device_status("tc_mc") # Via PECS service
    if tc_status_dict:
        print("  Temperature Controller Status (via PECS):")
        for param, p_val_obj in tc_status_dict.items():
            print("    " + str(param) + ": " + str(p_val_obj.value) + " " + str(p_val_obj.unit) + " (Status: " + str(p_val_obj.status) + ")")
    else:
        print("  Could not get Temperature Controller status via PECS.")

    # 4. Define and Submit a Simple Quantum Circuit (Bell State)
    print("\n[4. Defining and Submitting a Bell State Circuit]")
    q0_global_id = "qpu0::sq0"
    q1_global_id = "qpu0::sq1"

    bell_state_ops = [
        LogicalOperation(op_type=GateType.H, targets=[q0_global_id]),
        LogicalOperation(op_type=GateType.CX, targets=[q0_global_id, q1_global_id]),
        LogicalOperation(op_type=GateType.BARRIER, targets=[q0_global_id, q1_global_id]),
        LogicalOperation(op_type=GateType.MEASURE, targets=[q0_global_id]),
        LogicalOperation(op_type=GateType.MEASURE, targets=[q1_global_id])
    ]

    op_seq = OperationSequence(job_id="job_bell_001", operations=bell_state_ops)
    schedule_id = ptss_stub.submit_operation_sequence(op_seq)
    print("  Submitted sequence to PTSS_Stub. Schedule ID: " + str(schedule_id))
    schedule_status = ptss_stub.get_schedule_status(schedule_id)
    print("  Schedule Status from PTSS_Stub: " + str(schedule_status))


    # 5. Retrieve Measurement Results
    print("\n[5. Retrieving Measurement Results from QHALService]")
    num_shots = 10
    measurement_results = qhal_service.measure_qubits_global(
        global_qubit_ids=[q0_global_id, q1_global_id],
        opts={"shots": num_shots}
    )
    print("  Measurement Results (Driver returns first outcome of " + str(num_shots) + " shots):")
    for qubit_id, outcome in measurement_results.items():
        print("    Global Qubit ID " + str(qubit_id) + ": " + str(outcome))
    print("  Note: For Bell state, expect mostly 00 or 11. SimulatedQPU_Driver.measure_qubits currently gives one outcome. Full counts would require driver modification.")

    # 6. Example: Control an Environment Device via PECS
    print("\n[6. Controlling Environment (Simulated Temperature Controller)]")
    new_setpoint = 0.020
    print("  Setting TC " + sim_tc_driver.device_id + " setpoint to: " + str(new_setpoint) + " K using PECS service")
    success = pecs_service.control_device_parameter(sim_tc_driver.device_id, "setpoint_temperature", new_setpoint)

    if success:
        print("  Setpoint update acknowledged by SimTC via PECS.")
        time.sleep(0.05) # Tiny pause for conceptual ramp (SimTC Phase 0 doesn't ramp actively)
        updated_tc_status = pecs_service.get_device_status(sim_tc_driver.device_id)
        if updated_tc_status:
            print("  Updated Temperature Controller Status (via PECS):")
            for param, p_val_obj in updated_tc_status.items():
                 print("    " + str(param) + ": " + str(p_val_obj.value) + " " + str(p_val_obj.unit) + " (Status: " + str(p_val_obj.status) + ")")
    else:
        print("  Failed to update SimTC setpoint via PECS.")

    # 7. Unregister devices (cleanup)
    # print("\n[7. Unregistering Devices]") # QHALService unregister needs fix from prev consolidation
    # qhal_service.unregister_driver(sim_qpu_driver.device_id)
    # pecs_service.unregister_device(sim_tc_driver.device_id)

    print("\n--- CHIMera QOS Phase 0 Demo Script Complete ---")

if __name__ == "__main__":
    # This is to help locate modules if script is run from parent of temp_qos_code
    # current_dir = os.path.dirname(os.path.abspath(__file__))
    # if current_dir not in sys.path:
    #    sys.path.insert(0, current_dir)
    run_phase0_demo()
```
