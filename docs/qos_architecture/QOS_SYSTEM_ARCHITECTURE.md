# CHIMera Quantum Operating System (QOS) - System Architecture

**Version: 0.1 (Initial Draft)**

## 1. Introduction

The CHIMera Quantum Operating System (QOS) is envisioned as a comprehensive, modular, and scalable software stack designed to manage and orchestrate quantum laboratory environments end-to-end. Its primary goal is to abstract hardware complexities, streamline experimental workflows, facilitate quantum algorithm development, and ensure robust, reliable operation of quantum computing systems.

This document outlines the high-level system architecture, key service components, their interactions, and guiding design principles.

## 2. Architectural Principles

The CHIMera QOS architecture is guided by the following principles:

*   **Modularity & Service-Oriented Architecture (SOA):** The system is decomposed into distinct, loosely-coupled services, each with a well-defined responsibility. This promotes separation of concerns, independent development, and easier maintenance.
*   **Abstraction:** Hardware-specific details are abstracted away by dedicated layers (primarily QHAL and SimS), allowing higher-level services and applications to operate in a hardware-agnostic manner where possible.
*   **Scalability:** The architecture should allow for scaling of individual services and the overall system to accommodate larger and more complex quantum devices and experimental loads.
*   **Extensibility:** New services, hardware drivers, quantum algorithms, and error correction codes should be integrable with minimal disruption to the existing system.
*   **Reliability & Fault Tolerance:** The system must incorporate mechanisms for error detection, fault isolation, and recovery to ensure robust operation. SHMS and EMCS play crucial roles here.
*   **Security:** A dedicated Security & Access Control Service (SACS) will manage authentication, authorization, and secure communication throughout the QOS.
*   **Interoperability:** Standardized interfaces and data formats will be favored to promote interoperability between services and with external tools or platforms.

## 3. Layered Architecture

CHIMera QOS is conceptually organized into several layers:

```
+-----------------------------------------------------+
|          Application / User Layer                   |
| (SDKs, UIs, Workflow Engines, Scientific Tools)     |
+-----------------------------------------------------+
|          Algorithm Execution & Compilation Layer    |
| (AES: Orchestration, QLCS: Language Processing)     |
+-----------------------------------------------------+
|          Error Management & Simulation Layer        |
| (EMCS: QEC & Mitigation, SimS: Sim. Backends)       |
+-----------------------------------------------------+
|          Core Orchestration & Management Layer      |
| (PTSS: Timing, RMS: Resources, SACS: Security,     |
|  SHMS: Health Monitoring)                           |
+-----------------------------------------------------+
|          Physical Control & Abstraction Layer       |
| (PECS: Env. Control, QHAL: Hardware/Sim Interface)  |
+-----------------------------------------------------+
|          Physical Quantum & Classical Hardware      |
| (QPUs, Control Electronics, Cryostats, Servers)     |
+-----------------------------------------------------+
```

*   **Physical Hardware Layer:** The underlying quantum and classical hardware components.
*   **Physical Control & Abstraction Layer:**
    *   **QHAL (Quantum Hardware Abstraction Layer):** Provides a standardized interface to QPUs and quantum simulators. (See `qos_core_services/qhal_service.py`)
    *   **PECS (Physical Environment Control Service):** Manages and monitors the physical environment (cryogenics, vacuum, etc.). (See `qos_core_services/pecs_service.py`)
*   **Core Orchestration & Management Layer:**
    *   **PTSS (Precision Timing & Synchronization Service):** Coordinates the timing of all operations. (See `qos_core_services/ptss_conceptual.py`)
    *   **RMS (Resource Management Service):** Manages allocation of quantum and classical resources. (See `qos_core_services/rms_service.py`)
    *   **SACS (Security & Access Control Service):** Handles authentication, authorization, and other security aspects. (See `qos_core_services/sacs_conceptual.py`)
    *   **SHMS (System Health Monitoring Service):** Monitors the health and performance of all QOS components. (See `qos_core_services/shms_conceptual.py`)
*   **Error Management & Simulation Layer:**
    *   **EMCS (Error Management and Correction Service):** Implements QEC codes and error mitigation strategies. (See `qos_core_services/emcs_service.py`)
    *   **SimS (Simulation Service):** Provides access to various quantum circuit simulators. (See `qos_core_services/sims_service.py`)
*   **Algorithm Execution & Compilation Layer:**
    *   **QLCS (Quantum Language Compilation Service):** Parses, validates, and transpiles quantum programs. (See `qos_core_services/qlcs_service.py`)
    *   **AES (Algorithm Execution Service):** Orchestrates the end-to-end execution of quantum jobs. (See `qos_core_services/aes_service.py`)
*   **Application / User Layer (Future):** This layer will host Software Development Kits (SDKs), graphical user interfaces (UIs), scientific workflow engines, and other tools that allow users and higher-level applications to interact with the QOS.

## 4. Core Services Overview

(Refer to `qos_core_services/README.md` for detailed purposes and conceptual components of each service listed below. This section will eventually provide a more narrative overview of their roles within the overall architecture.)

*   **QHAL (Quantum Hardware Abstraction Layer)**
*   **PECS (Physical Environment Control Service)**
*   **PTSS (Precision Timing & Synchronization Service)**
*   **RMS (Resource Management Service)**
*   **SACS (Security & Access Control Service)**
*   **SHMS (System Health Monitoring Service)**
*   **QLCS (Quantum Language Compilation Service)**
*   **AES (Algorithm Execution Service)**
*   **EMCS (Error Management and Correction Service)**
*   **SimS (Simulation Service)**
*   **(Conceptual/Future) DMS (Data Management Service):** Responsible for storing, managing, and retrieving experimental data, metadata, calibration results, and QOS logs.
*   **(Conceptual/Future) WMS (Workflow Management Service):** Enables definition, execution, and monitoring of complex experimental workflows involving multiple QOS services.

## 5. Key Interaction Scenarios & Data Flows (Initial Draft)

This section outlines high-level interactions for common operational scenarios. Detailed sequence diagrams and API contracts will be developed further.

### 5.1. Job Submission & Execution Lifecycle

A typical flow for submitting and executing a quantum program (e.g., QASM string):

1.  **User/SDK -> AES:** User submits a job request (program string, language dialect, shots, user/project info, execution options) to AES. AES creates an `ExperimentJob` record and returns a `job_id`.
2.  **AES -> SACS (Conceptual):** AES verifies user authorization for the request (e.g., access to project, resource quotas).
3.  **AES -> QLCS:** AES requests qubit requirements from QLCS for the program.
4.  **QLCS:** Parses program, determines `QubitRequirement` (e.g., number of logical qubits).
5.  **AES -> RMS:** AES submits a `ResourceRequest` to RMS based on `QubitRequirement` and job parameters (e.g., estimated duration).
6.  **RMS:**
    *   Validates request against policies.
    *   Finds and reserves available physical qubits (and other resources).
    *   Returns an `AllocationGrant` (with global IDs of allocated qubits) or `AllocationFailure` to AES.
7.  **AES -> QLCS:** If allocation successful, AES provides the program string and the logical-to-physical qubit mapping (from `AllocationGrant`) to QLCS for transpilation.
8.  **QLCS:** Transpiles the program into a `QHALTranspiledSequence` (a list of QHAL-compatible `GateCommand` definitions with global physical qubit IDs).
9.  **AES -> PTSS:** AES constructs an `OperationSequence` (from PTSS data types) based on the `QHALTranspiledSequence`. This sequence is submitted to PTSS for scheduling and execution.
10. **PTSS:**
    *   Validates the operation sequence.
    *   Schedules the operations based on timing constraints and resource availability (already allocated by RMS).
    *   Coordinates with QHAL to execute the gate commands on the target QPU or simulator.
    *   May interact with EMCS for active error correction cycles if logical qubits are used.
11. **QHAL:** Executes commands on the hardware/simulator, returning low-level results/status to PTSS.
12. **PTSS -> AES:** PTSS notifies AES of sequence completion (success or failure) and provides access to measurement results (which might be directly from QHAL or a data service).
13. **AES -> (Optional) EMCS:** If measurement error mitigation is requested, AES submits raw results to EMCS. EMCS returns mitigated results.
14. **AES:** Stores final results, updates `ExperimentJob` status to COMPLETED.
15. **User/SDK -> AES:** User queries job status and retrieves results.
16. **AES -> RMS:** Upon job completion or failure (or timeout), AES instructs RMS to release allocated resources using the `grant_id`.

**Diagram Placeholder:**
*   A sequence diagram illustrating the Job Submission & Execution Lifecycle described above would be beneficial here.

### 5.2. Resource Allocation & Release Flow

*   Covered within the Job Submission lifecycle. RMS is the central authority.
*   QHAL reports available quantum devices and their qubits to RMS during RMS initialization or via updates.
*   AES requests resources from RMS. RMS returns a grant or failure.
*   AES is responsible for releasing resources via RMS upon job completion/failure.

### 5.3. Error Correction Cycle (Conceptual)

1.  **EMCS/AES:** Determines a logical qubit requires a stabilizer cycle (e.g., periodically, or before/after critical operations).
2.  **EMCS -> QECC Object:** Retrieves stabilizer measurement circuit sequences (as QHAL commands) for the logical qubit's QECC type and physical qubit mapping.
3.  **EMCS -> PTSS:** Submits these stabilizer measurement sequences to PTSS for execution (often with high priority).
4.  **PTSS -> QHAL:** Executes stabilizer measurements.
5.  **QHAL -> PTSS -> EMCS:** Measurement outcomes (syndrome bits) are returned to EMCS.
6.  **EMCS -> QECC Object:** Decodes the syndrome to identify necessary correction operations (if any).
7.  **EMCS -> PTSS:** If correction needed, submits correction QHAL commands to PTSS (often with critical priority).
8.  **PTSS -> QHAL:** Executes correction.
9.  **EMCS:** Logs cycle details, updates logical qubit status and fidelity estimates.

**Diagram Placeholder:**
*   A sequence diagram for the Error Correction Cycle.

### 5.4. System Health Monitoring Flow

1.  **All Services -> SHMS:** Services periodically (or event-driven) push telemetry data (logs, metrics, status changes) to SHMS.
2.  **SHMS:** Aggregates, processes, and stores this data.
3.  **SHMS:** Performs anomaly detection.
4.  **SHMS -> Alerting System / Operators / Other Services:** If anomalies or critical events detected, SHMS triggers alerts or notifications.
5.  **SHMS -> RMS/SACS (Conceptual):** SHMS might inform RMS of unhealthy resources or SACS of security-related health events.

## 6. Inter-Service Communication (Conceptual)

The primary mode of inter-service communication is envisioned to be API-driven, likely using:

*   **gRPC or REST APIs:** For synchronous request/response interactions (e.g., AES calling QLCS, RMS). gRPC is favored for performance and typed interfaces.
*   **Message Queues (e.g., RabbitMQ, Kafka):** For asynchronous events, notifications, and potentially for decoupling long-running tasks (e.g., PTSS job status updates, SHMS log ingestion).
*   **Shared Data Stores (Conceptual):** A dedicated Data Management Service (DMS) might manage persistent storage for job results, calibration data, and extensive logs, with services accessing it via its API.

**Data Formats:**
*   Standardized data formats like JSON or Protocol Buffers (if using gRPC) for API payloads.
*   OpenQASM 2.0/3.0 as a primary quantum language dialect.
*   Defined schemas for QHAL command sequences, resource descriptions, and job metadata.

## 7. Future Considerations & Evolution

*   **Data Management Service (DMS):** Formalize the DMS for robust data persistence and querying.
*   **Workflow Management Service (WMS):** Allow users to define and execute complex multi-step workflows.
*   **Advanced Scheduling & Optimization (PTSS/RMS):** More sophisticated algorithms for resource scheduling, co-scheduling of classical/quantum resources, and optimizing for QPU topology or calibration drifts.
*   **Plugin Architecture for Drivers/Simulators/QECCs:** Facilitate easier integration of new components.
*   **User Interface (UI) and Software Development Kit (SDK):** Develop user-friendly interfaces for interacting with the QOS.

This document serves as a living blueprint and will evolve as the CHIMera QOS project progresses.

## 8. Conceptual API Contracts (Initial Draft)

This section outlines conceptual API contracts for key inter-service communications. These are high-level and would be further refined into specific gRPC/REST definitions or message schemas.

### 8.1. AES <-> QLCS

*   **Communication Pattern:** Synchronous Request/Response (e.g., gRPC or REST).

*   **Method: `QLCS.GetQubitRequirements`**
    *   **Request:**
        *   `program_string: str` (e.g., OpenQASM 2.0 content)
        *   `language_dialect: str` (e.g., "OpenQASM2.0")
    *   **Response:**
        *   `num_logical_qubits: int`
        *   `required_classical_registers: Dict[str, int]` (name -> size)
        *   `status: str` ("SUCCESS" or "ERROR")
        *   `error_message: Optional[str]`
    *   **Purpose:** AES asks QLCS to parse a program and return the number of logical qubits and classical registers it declares/needs.

*   **Method: `QLCS.TranspileToQHALSequence`**
    *   **Request:**
        *   `program_string: str`
        *   `language_dialect: str`
        *   `qubit_mapping: Dict[int, str]` (Logical qubit index from program -> Global QHAL Qubit ID)
        *   `transpilation_options: Optional[Dict[str, Any]]` (e.g., optimization level, target basis gates if QLCS handles this level of detail)
    *   **Response (`QHALTranspiledSequence` conceptual structure):**
        *   `target_qubit_global_ids_per_gate: List[List[str]]`
        *   `gate_info_sequence: List[Tuple[str, Optional[Dict[str, Any]]]]` (GateType.name, parameters)
        *   `measured_qubit_global_ids: List[str]`
        *   `num_classical_bits_declared: int`
        *   `status: str` ("SUCCESS" or "ERROR")
        *   `error_message: Optional[str]`
    *   **Purpose:** AES provides the program and physical qubit mapping; QLCS returns a QHAL-compatible sequence.

### 8.2. AES <-> RMS

*   **Communication Pattern:** Synchronous Request/Response.

*   **Method: `RMS.SubmitResourceRequest`**
    *   **Request (`ResourceRequest` conceptual structure):**
        *   `request_id: str`
        *   `job_id: str`
        *   `user_id: str`
        *   `quantum_criteria: List[QuantumResourceCriterion]`
        *   `classical_criteria: List[ClassicalResourceCriterion]`
        *   `estimated_duration_seconds: int`
    *   **Response (Union of `AllocationGrant` or `AllocationFailure` conceptual structures):**
        *   If success (`AllocationGrant`): `grant_id`, `status`, `allocated_quantum_resources: List[AllocatedResource]`, etc.
        *   If failure (`AllocationFailure`): `status`, `reason_code`, `message`.
    *   **Purpose:** AES requests necessary quantum/classical resources for a job.

*   **Method: `RMS.ReleaseResourcesByGrantID`**
    *   **Request:**
        *   `grant_id: str`
        *   `releasing_entity_id: str` (e.g., "AES" or specific job_id)
    *   **Response:**
        *   `success: bool`
        *   `message: Optional[str]`
    *   **Purpose:** AES informs RMS that resources associated with a grant are no longer needed.

### 8.3. AES <-> PTSS

*   **Communication Pattern:** Primarily synchronous for submission, but PTSS operations are long-running, so status polling or callbacks would be needed.

*   **Method: `PTSS.SubmitOperationSequence`**
    *   **Request (`OperationSequence` conceptual structure from PTSS):**
        *   `sequence_id: Optional[str]` (PTSS might generate if not provided)
        *   `job_id: str` (Linking to AES job)
        *   `operations: List[LogicalOperation]` (QHAL commands with global IDs, timing constraints)
        *   `priority: OperationPriority`
    *   **Response:**
        *   `ptss_schedule_id: str` (ID assigned by PTSS for this sequence execution)
        *   `submission_status: str` ("ACCEPTED", "REJECTED_INVALID", "REJECTED_BUSY")
        *   `message: Optional[str]`
    *   **Purpose:** AES submits a hardware-agnostic sequence of operations (derived from QLCS output) to PTSS for timed execution.

*   **Method: `PTSS.GetScheduleStatus`** (Polled by AES or used in callback)
    *   **Request:**
        *   `ptss_schedule_id: str`
    *   **Response (`ScheduleStatus` conceptual structure from PTSS):**
        *   `schedule_id: str`
        *   `status: str` ("QUEUED", "EXECUTING", "COMPLETED_SUCCESS", "COMPLETED_PARTIAL", "FAILED_QHAL", "FAILED_TIMING", "CANCELLED")
        *   `message: Optional[str]`
        *   `execution_start_time_unix: Optional[float]`
        *   `execution_end_time_unix: Optional[float]`
        *   `results_reference: Optional[Any]` (e.g., ID or path to where detailed results/measurements are stored if PTSS manages this, or indicates QHAL holds them)
    *   **Purpose:** AES queries PTSS for the status of an ongoing/completed operation sequence.

*   **Method: `PTSS.CancelOperationSequence`**
    *   **Request:**
        *   `ptss_schedule_id: str`
    *   **Response:**
        *   `cancellation_acknowledged: bool`
        *   `final_status: str` (e.g., "CANCELLED", "COMPLETED_BEFORE_CANCEL")
    *   **Purpose:** AES attempts to cancel an operation sequence.

### 8.4. PTSS <-> QHAL (Internal to QOS Core, orchestrated by PTSS)

*   **Communication Pattern:** Synchronous calls from PTSS to a specific QHAL driver instance.

*   **Method: `QuantumDeviceDriver.execute_gate_commands` (from QHAL blueprint)**
    *   **Request (by PTSS):**
        *   `commands: List[GateCommand]` (QHAL `GateCommand` with local qubit IDs for that driver)
    *   **Response (to PTSS):**
        *   `status: str` ("SUCCESS", "ERROR_DEVICE", "ERROR_COMMAND_FORMAT")
        *   `execution_metadata: Optional[Dict[str,Any]]` (e.g., actual timings, error codes from hardware)
        *   `job_id_on_device: Optional[str]` (If the hardware itself uses job IDs)
    *   **Purpose:** PTSS instructs a QHAL driver to execute a precisely timed block of gate commands.

*   **Method: `QuantumDeviceDriver.measure_qubits_blocking` (from QHAL blueprint, might be part of execute_gate_commands or separate for results retrieval)**
    *   **Request (by PTSS):**
        *   `local_qubit_ids: List[Any]`
        *   `measurement_options: Optional[Dict[str, Any]]` (e.g., shots, classical register mapping)
    *   **Response (to PTSS):**
        *   `measurement_outcomes: Dict[Any, int]` (Local qubit ID -> 0/1 for single shot, or Dict[str, int] for counts over multiple shots if QHAL aggregates)
        *   `status: str`
    *   **Purpose:** PTSS instructs QHAL driver to perform measurements. *Note: For shot-based experiments, measurement is typically part of a larger sequence submitted via `execute_gate_commands`. This method might be more for specific calibration/state-check measurements.*

### 8.5. AES <-> EMCS (Optional Error Mitigation)

*   **Communication Pattern:** Synchronous Request/Response.

*   **Method: `EMCS.SubmitMitigationTask`**
    *   **Request (`MitigationTask` conceptual structure from EMCS, minus results/status):**
        *   `job_id: str` (Original AES job ID)
        *   `raw_measurement_counts: Dict[str, int]`
        *   `measured_qubit_global_ids: List[str]`
        *   `strategy_requested: ErrorMitigationStrategy`
        *   `strategy_parameters: Optional[Dict[str, Any]]`
    *   **Response:**
        *   `mitigation_task_id: str`
        *   `submission_status: str` ("ACCEPTED", "REJECTED")
        *   `message: Optional[str]`
    *   **Purpose:** AES submits raw measurement counts to EMCS for post-processing error mitigation.

*   **Method: `EMCS.GetMitigationTaskStatus` / `EMCS.GetMitigationTaskResult`** (Similar to PTSS status/result polling)
    *   **Request:** `mitigation_task_id: str`
    *   **Response (`MitigationTask` conceptual structure from EMCS, including status and mitigated_counts):**
        *   Full `MitigationTask` object.
    *   **Purpose:** AES checks status and retrieves mitigated results from EMCS.

This initial draft provides a basis for more detailed API specifications (e.g., using Protobuf/gRPC or OpenAPI).
