# CHIMera QOS - Resource Management Service (RMS)

This package implements the RMS, responsible for managing the allocation and lifecycle of quantum and classical resources within the CHIMera QOS.

## Current Status (Phase 1 - Qubit Focused)

*   **`rms.py`**: Contains the core RMS implementation based on the refined blueprint (`qos_core_services/rms_service.py`).
    *   **Data Structures**: `ResourceType`, `QuantumResourceCriterion`, `ClassicalResourceCriterion`, `ResourceRequest`, `AllocatedResource`, `AllocationGrant`, `AllocationFailure`, `ResourceInstance`.
    *   **Custom Exceptions**: `RMSException` and its derivatives.
    *   **`RMS_Service`**:
        *   Initializes its quantum resource inventory by querying a `QHALService` instance for available qubits and their properties.
        *   `submit_resource_request`: Handles requests for a specified quantity of qubits. Allocation is currently exclusive-use and first-come-first-served from the available pool. Detailed property matching and policy enforcement are deferred.
        *   `release_resources_by_grant_id` / `release_resources_by_job_id`: Marks allocated qubits as available in the internal inventory.
        *   `get_allocation_details`: Retrieves information about an active allocation.
        *   `query_available_resources`: Reports currently available qubits (simplified query).
        *   Includes SHMS logging callback integration (conceptual).

*   **`tests/`**:
    *   `test_rms_service.py`: Unit tests for the Phase 1 qubit-focused RMS functionalities, including inventory initialization, qubit allocation, release, and status queries. Uses a mocked `QHALService`.

## Next Steps for RMS Implementation

*   **Policy Engine:** Implement a basic policy engine for quotas (user, project), priorities, and fair-share.
*   **Advanced Quantum Resource Matching:** Enhance `submit_resource_request` to match `QuantumResourceCriterion` more precisely (e.g., T1, T2, fidelities, connectivity).
*   **Classical Resource Management:** Add support for managing classical resources (CPU, memory, GPU) including inventory tracking and allocation.
*   **Reservation System:** Implement capabilities for advance resource reservation (`requested_start_time_unix`).
*   **Dynamic Inventory Updates:** Fully implement `update_resource_inventory` and `report_resource_status_change` for real-time updates from QHAL, SHMS, or classical resource managers.
*   **Concurrency & Locking:** Ensure thread-safety for resource inventory and allocation management if RMS will handle concurrent requests.
*   **Integration Tests:** Develop integration tests with (simulated) QHAL, SACS, and AES.
*   **Persistence:** Plan for persisting active allocations and potentially resource state across RMS restarts.
