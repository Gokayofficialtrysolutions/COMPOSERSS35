# CHIMera QOS - Physical Environment Control Service (PECS)

This package implements the PECS, responsible for monitoring and controlling the physical environment parameters crucial for quantum device operation.

## Current Status

*   **`pecs.py`**: Contains the core PECS implementation based on the refined blueprint (`qos_core_services/pecs_service.py`).
    *   **Abstract Interfaces**: `AbstractEnvironmentDevice`.
    *   **Data Structures**: `SubSystemType`, `ParameterDefinition`, `ParameterValue`.
    *   **Custom Exceptions**: `PECSException` and its derivatives.
    *   **Simulated Devices**:
        *   `SimulatedTemperatureController`: Simulates a cryostat temperature controller with ramping and basic thermal modeling.
        *   `SimulatedVacuumGauge`: Simulates a vacuum gauge with pump-down/leak logic.
    *   **`PECS_Service`**: Main service class for device registration, parameter access, command execution, and subsystem management. Includes SHMS logging callback integration.

*   **`tests/`**:
    *   `test_simulated_devices.py`: Unit tests for `SimulatedTemperatureController` and `SimulatedVacuumGauge`.
    *   `test_pecs_service.py`: Unit tests for core `PECS_Service` functionalities like device registration/unregistration and interaction.

## Next Steps for PECS Implementation

*   Expand the library of simulated devices (e.g., `SimulatedMagnetController`, `SimulatedLaserSystem`).
*   Implement more sophisticated simulation logic within devices (e.g., more accurate thermal models, inter-dependent parameters).
*   Define and implement more complex device commands.
*   Refine the `_internal_device_callback` mechanism and event types for devices to report asynchronous events or alerts to PECS/SHMS.
*   Develop more comprehensive unit and integration tests.
*   Consider how PECS will discover or be configured with real hardware drivers in later phases (e.g., plugin architecture, configuration files).
*   Implement subsystem-wide commands in `PECS_Service` (e.g., "safe_mode_all_cryogenics").
