# CHIMera QOS - Algorithm Execution Service (AES) Blueprint
# Version: 0.2 (Refined from phase1_qlcs_aes.py)

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Union, Callable
from dataclasses import dataclass, field
import uuid
import time

# Assuming QHALTranspiledSequence, QubitRequirement from qlcs_service
# Assuming OperationSequence, LogicalOperation from a common types or ptss_service
# Assuming GateType from qhal_service
try:
    from .qlcs_service import AbstractQLCS, QHALTranspiledSequence, QubitRequirement, QLCSError
    from .rms_service import AbstractRMS, ResourceRequest, AllocationGrant, AllocationFailure, QuantumResourceCriterion, ResourceType as RMSRresourceType
    # Need to resolve potential naming conflict if PTSS defines its own ResourceType
    from .ptss_service import AbstractPTSS, OperationSequence, LogicalOperation, OperationPriority # Assuming PTSS defines these
    from .qhal_service import GateType # For constructing LogicalOperation
except ImportError: # Fallback for standalone blueprint definition
    print("AES_Blueprint: Could not import from sibling QOS service blueprints. Using placeholder types.")
    AbstractQLCS = ABC; AbstractRMS = ABC; AbstractPTSS = ABC;
    class QLCSError(Exception): pass
    @dataclass
    class QubitRequirement: num_qubits: int
    @dataclass
    class QHALTranspiledSequence: target_qubit_global_ids_per_gate: List[List[str]]; gate_info_sequence: List[Tuple[Any, Any]]; measured_qubit_global_ids: List[str]; num_classical_bits_declared: int
    @dataclass
    class ResourceRequest: job_id: str; user_id: str; quantum_criteria: List[Any]; estimated_duration_seconds: int; request_id: str = ""
    @dataclass
    class QuantumResourceCriterion: resource_type: Any; quantity: int
    @dataclass
    class AllocationGrant: grant_id: str; allocated_quantum_resources: List[Any]
    @dataclass
    class AllocationFailure: message: str
    class RMSRresourceType(Enum): QUBIT = "qubit"
    @dataclass
    class OperationSequence: job_id:str; operations:List[Any]; priority:Any; sequence_id:str = ""
    @dataclass
    class LogicalOperation: op_type:Any; targets:List[Any]; params:Optional[Dict[str,Any]]=None
    class OperationPriority(Enum): MEDIUM = 1
    class GateType(Enum): MEASURE = "MEASURE"


# --- AES Custom Exceptions ---
class AESException(Exception): """Base exception for AES errors."""
class AESJobSubmissionError(AESException): """Error during job submission validation."""
class AESOrchestrationError(AESException): """Error during the orchestration of a job."""
class AESResultError(AESException): """Error related to job results."""

# --- AES Data Structures ---
class JobStatus(Enum):
    RECEIVED = "RECEIVED"
    VALIDATING = "VALIDATING"
    COMPILING_REQ_QUBITS = "COMPILING_REQ_QUBITS" # QLCS getting requirements
    ALLOCATING_RESOURCES = "ALLOCATING_RESOURCES" # RMS allocating
    COMPILING_TRANSPILING = "COMPILING_TRANSPILING" # QLCS transpiling to QHAL sequence
    SUBMITTING_TO_PTSS = "SUBMITTING_TO_PTSS" # PTSS scheduling
    QUEUED_IN_PTSS = "QUEUED_IN_PTSS"
    EXECUTING_ON_QPU = "EXECUTING_ON_QPU" # PTSS/QHAL running
    FETCHING_RESULTS = "FETCHING_RESULTS"
    COMPLETED_SUCCESS = "COMPLETED_SUCCESS"
    FAILED_VALIDATION = "FAILED_VALIDATION"
    FAILED_QLCS_REQ = "FAILED_QLCS_REQ"
    FAILED_RMS_ALLOCATION = "FAILED_RMS_ALLOCATION"
    FAILED_QLCS_TRANSPILE = "FAILED_QLCS_TRANSPILE"
    FAILED_PTSS_SUBMISSION = "FAILED_PTSS_SUBMISSION"
    FAILED_QPU_EXECUTION = "FAILED_QPU_EXECUTION"
    FAILED_RESULT_PROCESSING = "FAILED_RESULT_PROCESSING"
    FAILED_RESOURCE_RELEASE = "FAILED_RESOURCE_RELEASE"
    FAILED_INTERNAL_ERROR = "FAILED_INTERNAL_ERROR"
    CANCELLED = "CANCELLED"

@dataclass
class ExperimentJob:
    job_id: str
    program_string: str # e.g., QASM
    language_dialect: str
    num_shots: int
    user_id: str
    project_id: Optional[str] = None
    status: JobStatus = JobStatus.RECEIVED
    status_message: Optional[str] = None

    creation_time_unix: float = field(default_factory=time.time)
    compilation_time_unix: Optional[float] = None
    allocation_time_unix: Optional[float] = None
    execution_start_time_unix: Optional[float] = None
    execution_end_time_unix: Optional[float] = None
    completion_time_unix: Optional[float] = None

    qubit_requirements: Optional[QubitRequirement] = None
    resource_allocation_grant_id: Optional[str] = None
    allocated_qubit_map: Optional[Dict[int, str]] = None # Logical idx to Global ID

    qhal_transpiled_sequence: Optional[QHALTranspiledSequence] = None
    ptss_schedule_id: Optional[str] = None

    results: Optional[Dict[str, int]] = None # Classical bitstring counts
    raw_result_data: Optional[Any] = None # For more detailed backend results

    # priority: int = 5 # Could be added from request

# --- AES Abstract Interface ---
class AbstractAES(ABC):
    @abstractmethod
    def __init__(self, qlcs: AbstractQLCS, rms: AbstractRMS, ptss: AbstractPTSS,
                 qhal_service: Any, # Any for now, should be AbstractQHALService
                 sacs_service: Any, # Any for now, should be AbstractSACS
                 shms_callback: Optional[Callable]):
        pass

    @abstractmethod
    def submit_experiment_job(self, program_string: str, language_dialect: str,
                              num_shots: int, user_id: str, project_id: Optional[str] = None,
                              execution_options: Optional[Dict[str,Any]] = None) -> str: # Returns Job ID
        """Submits a new quantum experiment job."""
        pass

    @abstractmethod
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves the current status and metadata of a job."""
        pass

    @abstractmethod
    def get_job_results(self, job_id: str) -> Optional[Dict[str, int]]:
        """Retrieves the measurement results (counts) of a completed job."""
        pass

    @abstractmethod
    def cancel_job(self, job_id: str, user_id: str) -> bool:
        """Attempts to cancel a queued or running job."""
        pass

# --- AES Service Implementation ---
class AES_Service(AbstractAES):
    def __init__(self, qlcs: AbstractQLCS, rms: AbstractRMS, ptss: AbstractPTSS,
                 qhal_service: Any, sacs_service: Any, shms_callback: Optional[Callable]):
        self.qlcs = qlcs
        self.rms = rms
        self.ptss = ptss
        self.qhal_service = qhal_service # Used by PTSS, but AES might query it for results or device info
        self.sacs_service = sacs_service # For authZ checks
        self._shms_callback = shms_callback

        self._jobs: Dict[str, ExperimentJob] = {} # job_id -> ExperimentJob
        self._log("INFO", "AES_Service initialized.")

    def _log(self, level: str, message: str, data: Optional[Dict[str, Any]] = None):
        if self._shms_callback:
            log_entry = {"timestamp": time.time(), "source": "AES", "level": level, "message": message, "data": data or {}}
            self._shms_callback(log_entry)
        else: print(f"AES_LOG [{level}]: {message}" + (f" Data: {data}" if data else ""))

    def _update_job_status(self, job_id: str, new_status: JobStatus, status_message: Optional[str] = None, error: Optional[Exception] = None):
        job = self._jobs.get(job_id)
        if not job:
            self._log("ERROR", f"Attempted to update status for unknown job_id '{job_id}'.")
            return

        job.status = new_status
        job.status_message = status_message if status_message else (str(error) if error else None)

        log_level = "ERROR" if "FAILED" in new_status.name or error else "INFO"
        self._log(log_level, f"Job '{job_id}' status updated to {new_status.name}.",
                  {"user_id": job.user_id, "message": job.status_message})

        if new_status in [JobStatus.COMPLETED_SUCCESS, JobStatus.FAILED_VALIDATION, JobStatus.FAILED_QLCS_REQ,
                          JobStatus.FAILED_RMS_ALLOCATION, JobStatus.FAILED_QLCS_TRANSPILE,
                          JobStatus.FAILED_PTSS_SUBMISSION, JobStatus.FAILED_QPU_EXECUTION,
                          JobStatus.FAILED_RESULT_PROCESSING, JobStatus.FAILED_RESOURCE_RELEASE,
                          JobStatus.FAILED_INTERNAL_ERROR, JobStatus.CANCELLED]:
            job.completion_time_unix = time.time()
            # Ensure resources are released if allocated and job failed/completed/cancelled
            if job.resource_allocation_grant_id:
                released = self.rms.release_resources_by_grant_id(job.resource_allocation_grant_id, "AES_Service")
                if released:
                    self._log("INFO", f"Resources for grant '{job.resource_allocation_grant_id}' (Job: {job_id}) released by AES.", {"job_status": new_status.name})
                    job.resource_allocation_grant_id = None
                    job.allocated_qubit_map = None
                else:
                    self._log("CRITICAL", f"Failed to release resources for grant '{job.resource_allocation_grant_id}' (Job: {job_id}) after job {new_status.name}. Manual intervention may be required.")
                    if job.status != JobStatus.FAILED_RESOURCE_RELEASE: # Avoid status loop
                         self._update_job_status(job_id, JobStatus.FAILED_RESOURCE_RELEASE, "Critical: Failed to release allocated resources post-job.")


    def _orchestrate_job_execution(self, job_id: str):
        job = self._jobs.get(job_id)
        if not job: self._log("ERROR", f"Orchestration called for unknown job_id '{job_id}'."); return

        try:
            # 1. Get Qubit Requirements
            self._update_job_status(job_id, JobStatus.COMPILING_REQ_QUBITS)
            job.qubit_requirements = self.qlcs.get_qubit_requirements(job.program_string, job.language_dialect)
            if not job.qubit_requirements or job.qubit_requirements.num_qubits <= 0:
                raise AESOrchestrationError(f"Invalid qubit requirement: {job.qubit_requirements.num_qubits if job.qubit_requirements else 'None'} qubits.")

            # 2. Allocate Resources via RMS
            self._update_job_status(job_id, JobStatus.ALLOCATING_RESOURCES)
            resource_req = ResourceRequest(
                job_id=job_id, user_id=job.user_id, project_id=job.project_id,
                quantum_criteria=[QuantumResourceCriterion(resource_type=RMSRresourceType.QUBIT, quantity=job.qubit_requirements.num_qubits)],
                estimated_duration_seconds=300 # Placeholder duration, could be estimated by QLCS or user
            )
            allocation_result = self.rms.submit_resource_request(resource_req)

            if isinstance(allocation_result, AllocationFailure):
                raise AESOrchestrationError(f"RMS allocation failed: {allocation_result.message}")

            grant: AllocationGrant = allocation_result
            job.resource_allocation_grant_id = grant.grant_id
            job.allocation_time_unix = grant.allocation_time_unix

            # Create qubit mapping: logical index -> global QHAL ID
            if len(grant.allocated_quantum_resources) < job.qubit_requirements.num_qubits:
                raise AESOrchestrationError(f"RMS allocated insufficient qubits: {len(grant.allocated_quantum_resources)} vs {job.qubit_requirements.num_qubits} requested.")

            job.allocated_qubit_map = {
                i: grant.allocated_quantum_resources[i].global_resource_id
                for i in range(job.qubit_requirements.num_qubits)
            }
            self._log("INFO", f"RMS allocated qubits for job {job_id}: {job.allocated_qubit_map}")

            # 3. Transpile to QHAL Sequence via QLCS
            self._update_job_status(job_id, JobStatus.COMPILING_TRANSPILING)
            job.qhal_transpiled_sequence = self.qlcs.transpile_to_qhal_sequence(
                job.program_string, job.allocated_qubit_map, job.language_dialect
            )
            job.compilation_time_unix = time.time()

            # 4. Construct PTSS OperationSequence
            if not job.qhal_transpiled_sequence: raise AESOrchestrationError("QLCS returned empty QHAL sequence.")

            ptss_ops = [
                LogicalOperation(
                    op_type=gate_info[0], # GateType enum
                    targets=target_gids,  # List of global qubit IDs
                    params=gate_info[1]   # Optional params dict
                ) for target_gids, gate_info in zip(
                    job.qhal_transpiled_sequence.target_qubit_global_ids_per_gate,
                    job.qhal_transpiled_sequence.gate_info_sequence
                )
            ]
            ptss_op_seq = OperationSequence(job_id=job_id, operations=ptss_ops, priority=OperationPriority.MEDIUM) # TODO: Map job priority

            # 5. Submit to PTSS
            self._update_job_status(job_id, JobStatus.SUBMITTING_TO_PTSS)
            job.ptss_schedule_id = self.ptss.submit_operation_sequence(ptss_op_seq)
            if not job.ptss_schedule_id:
                raise AESOrchestrationError("PTSS failed to accept the operation sequence.")

            # 6. Monitor PTSS (Simplified: assume blocking or quick poll for Phase 1)
            # In a real system, this would be asynchronous with callbacks or polling.
            self._update_job_status(job_id, JobStatus.QUEUED_IN_PTSS) # Or EXECUTING_ON_QPU if PTSS indicates immediate

            # --- This part is highly simplified for Phase 1 ---
            # Assume PTSS executes and QHAL handles measurements internally for now if sequence includes them
            # For a real system, AES would wait for PTSS completion signal.
            # This is a conceptual placeholder for PTSS interaction.
            time.sleep(0.01) # Simulate some QPU time
            ptss_final_status = self.ptss.get_schedule_status(job.ptss_schedule_id) # Simplified

            if not ptss_final_status or str(ptss_final_status.status).upper().startswith("FAIL"):
                 raise AESOrchestrationError(f"PTSS/QHAL execution failed: {ptss_final_status.message if ptss_final_status else 'Unknown PTSS error'}")
            job.execution_start_time_unix = ptss_final_status.start_time if ptss_final_status else time.time() - 0.005
            job.execution_end_time_unix = ptss_final_status.end_time if ptss_final_status else time.time()
            self._update_job_status(job_id, JobStatus.EXECUTING_ON_QPU) # Should be before results really
            # --- End simplified PTSS interaction ---

            # 7. Fetch/Process Results
            self._update_job_status(job_id, JobStatus.FETCHING_RESULTS)
            if job.qhal_transpiled_sequence.measured_qubit_global_ids:
                # This is a simplification. Results should ideally come via PTSS or a data service.
                # QHAL measure_qubits_globally might not be suitable for post-sequence full results.
                # It implies re-running or that QHAL stores last measurement.
                # For Phase 1, we assume PTSS has orchestrated QHAL measurements and results are available via QHALService (conceptual).
                # A better model: PTSS returns measurement results.

                # Placeholder: Simulate counts based on QHAL's last state or a mock result.
                # For a real system, QHAL would have executed measures as part of the sequence.
                # The results would be stored by some component (QHAL/DataService) and retrieved via PTSS/Job ID.

                # Let's assume the `ptss_final_status` (if detailed) would contain results or pointer to them.
                # For now, create dummy results if measured qubits exist.
                dummy_counts: Dict[str, int] = {}
                if job.qhal_transpiled_sequence.num_classical_bits_declared > 0:
                    # Create a dummy bitstring based on number of classical bits
                    num_clbits = job.qhal_transpiled_sequence.num_classical_bits_declared
                    example_outcome = '0' * num_clbits
                    dummy_counts[example_outcome] = job.num_shots
                job.results = dummy_counts if dummy_counts else {"simulation_placeholder": job.num_shots}
                self._log("INFO", f"Job {job_id} results (simulated placeholder): {job.results}")
            else:
                job.results = {"no_measurements_in_program": 0}

            self._update_job_status(job_id, JobStatus.COMPLETED_SUCCESS)

        except QLCSError as e:
            self._update_job_status(job_id, JobStatus.FAILED_QLCS_TRANSPILE, error=e)
        except RMSException as e:
            self._update_job_status(job_id, JobStatus.FAILED_RMS_ALLOCATION, error=e)
        except AESOrchestrationError as e: # Catch specific orchestration step failures
            # Status might have been set more specifically within the error origin
            if job and job.status == JobStatus.RECEIVED: # If error occurred before specific status updates
                 self._update_job_status(job_id, JobStatus.FAILED_VALIDATION, error=e) # Default early failure
            # else status already set by _update_job_status if error was more specific
        except Exception as e: # Catch-all for other unexpected errors
            self._log("ERROR", f"Unexpected internal error orchestrating job {job_id}: {e}")
            self._update_job_status(job_id, JobStatus.FAILED_INTERNAL_ERROR, error=e)
        # finally: # Resource release is now handled by _update_job_status on terminal states.
            # This was moved to ensure resources are released even if _orchestrate_job_execution itself fails early.

    def submit_experiment_job(self, program_string: str, language_dialect: str,
                              num_shots: int, user_id: str, project_id: Optional[str] = None,
                              execution_options: Optional[Dict[str,Any]] = None) -> str:
        job_id = f"aes-job-{uuid.uuid4().hex[:12]}"
        self._log("INFO", f"Received job submission for user '{user_id}'. Job ID: {job_id}",
                  {"language": language_dialect, "shots": num_shots, "project": project_id})

        if not program_string or num_shots <= 0:
            self._log("ERROR", "Invalid job submission: program empty or num_shots non-positive.", {"job_id": job_id})
            raise AESJobSubmissionError("Program string must not be empty and num_shots must be positive.")

        # Basic authorization check (conceptual)
        # if not self.sacs_service.is_authorized(user_id, "submit_job", {"project": project_id}):
        #     self._log("WARNING", f"User '{user_id}' not authorized to submit job to project '{project_id}'.", {"job_id": job_id})
        #     raise AESJobSubmissionError(f"User '{user_id}' not authorized for project '{project_id}'.")

        job = ExperimentJob(
            job_id=job_id, program_string=program_string, language_dialect=language_dialect,
            num_shots=num_shots, user_id=user_id, project_id=project_id
        )
        self._jobs[job_id] = job

        # Offload actual orchestration to allow submit_experiment to return quickly.
        # In a real system, this would be a task queue (e.g., Celery) or a new thread/async task.
        # For this blueprint, we'll call it directly for simplicity of flow.
        self._orchestrate_job_execution(job_id) # In reality, this would be async.

        return job_id

    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        job = self._jobs.get(job_id)
        if not job: return None
        return {
            "job_id": job.job_id, "user_id": job.user_id, "project_id": job.project_id,
            "status": job.status.name, "status_message": job.status_message,
            "language": job.language_dialect, "num_shots": job.num_shots,
            "creation_time_unix": job.creation_time_unix,
            "compilation_time_unix": job.compilation_time_unix,
            "allocation_time_unix": job.allocation_time_unix,
            "execution_start_time_unix": job.execution_start_time_unix,
            "execution_end_time_unix": job.execution_end_time_unix,
            "completion_time_unix": job.completion_time_unix,
            "num_required_qubits": job.qubit_requirements.num_qubits if job.qubit_requirements else None,
            "allocated_qubits": list(job.allocated_qubit_map.values()) if job.allocated_qubit_map else None
        }

    def get_job_results(self, job_id: str) -> Optional[Dict[str, int]]:
        job = self._jobs.get(job_id)
        if not job:
            raise AESResultError(f"Job ID '{job_id}' not found.")
        if job.status == JobStatus.COMPLETED_SUCCESS:
            return job.results
        elif "FAILED" in job.status.name:
            raise AESResultError(f"Job '{job_id}' failed: {job.status_message or job.status.name}")
        else: # Job still running or in intermediate state
            return None

    def cancel_job(self, job_id: str, user_id: str) -> bool:
        job = self._jobs.get(job_id)
        if not job:
            self._log("WARNING", f"Attempt to cancel non-existent job '{job_id}' by user '{user_id}'.")
            return False

        # Authorization check (conceptual)
        # if job.user_id != user_id and not self.sacs_service.is_admin(user_id):
        #     self._log("WARNING", f"User '{user_id}' unauthorized to cancel job '{job_id}' (owner: {job.user_id}).")
        #     return False

        if job.status in [JobStatus.COMPLETED_SUCCESS] or "FAILED" in job.status.name or job.status == JobStatus.CANCELLED:
            self._log("INFO", f"Job '{job_id}' already in terminal state '{job.status.name}'. Cannot cancel.", {"user_id": user_id})
            return False # Or True, indicating it's effectively "cancelled" from user perspective

        # Attempt to cancel with PTSS if submitted
        if job.ptss_schedule_id:
            try:
                cancel_success = self.ptss.cancel_operation_sequence(job.ptss_schedule_id)
                if not cancel_success:
                    self._log("WARNING", f"PTSS reported failure to cancel schedule '{job.ptss_schedule_id}' for job '{job_id}'. Job may continue.", {"user_id": user_id})
                    # Depending on policy, might still mark as CANCELLED from AES perspective if best-effort
            except Exception as e:
                self._log("ERROR", f"Error cancelling PTSS schedule '{job.ptss_schedule_id}' for job '{job_id}': {e}", {"user_id": user_id})
                # Continue to mark as CANCELLED in AES, PTSS might still be running.

        self._update_job_status(job_id, JobStatus.CANCELLED, status_message=f"Cancelled by user '{user_id}'.")
        # Resource release is handled by _update_job_status on terminal states.
        return True

print("CHIMera QOS - AES Service Blueprint Definition Complete.")
