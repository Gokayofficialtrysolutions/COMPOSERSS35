# CHIMera QOS - Resource Management Service (RMS) Blueprint
# Version: 0.2 (Consolidated & Refined)

import uuid
import time
from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Union, Callable, Type
from dataclasses import dataclass, field

# --- RMS Custom Exceptions ---

class RMSException(Exception):
    """Base exception for RMS-related errors."""
    pass

class RMSResourceUnavailableError(RMSException):
    """Error when requested resources are not available."""
    pass

class RMSAllocationError(RMSException):
    """Error during the allocation or deallocation process."""
    pass

class RMSPolicyViolationError(RMSException):
    """Error due to a policy violation (e.g., quota exceeded)."""
    pass

class RMSInvalidRequestError(RMSException):
    """Error due to an invalid resource request."""
    pass

# --- RMS Enums & Dataclasses ---

class ResourceType(Enum):
    QUBIT = "qubit" # Represents a single physical or logical qubit
    QPU_DEVICE = "qpu_device" # Represents an entire QPU or a significant partition
    CLASSICAL_COMPUTE_CORE = "classical_compute_core"
    CLASSICAL_MEMORY_GB = "classical_memory_gb"
    GPU_UNIT = "gpu_unit"
    FPGA_RESOURCE = "fpga_resource" # e.g., a specific FPGA board or region
    STORAGE_GB = "storage_gb"
    NETWORK_BANDWIDTH_MBPS = "network_bandwidth_mbps"
    QPU_ACCESS_TIME_SECONDS = "qpu_access_time_seconds" # For time-shared QPUs

@dataclass
class ResourcePropertyFilter:
    """A generic filter for resource properties."""
    property_name: str
    operator: str # e.g., "==", ">=", "<=", "in", "contains"
    value: Any

@dataclass
class QuantumResourceCriterion:
    """Defines criteria for requesting quantum resources."""
    resource_type: ResourceType # Typically QUBIT or QPU_DEVICE
    quantity: int = 1
    # Qualitative criteria
    min_t1_ns: Optional[float] = None
    min_t2_ns: Optional[float] = None # Could be T2* or T2_echo depending on context
    max_single_qubit_error_rate: Optional[Dict[str, float]] = None # e.g., {"x": 0.001, "h": 0.0005}
    max_two_qubit_error_rate: Optional[Dict[str, float]] = None    # e.g., {"cx": 0.01}
    connectivity_graph_type: Optional[str] = None # e.g., "linear_chain_min_length_5", "all_to_all"
    # Specific requests
    specific_global_ids: Optional[List[str]] = None # Request specific global qubit/device IDs
    custom_filters: List[ResourcePropertyFilter] = field(default_factory=list)

@dataclass
class ClassicalResourceCriterion:
    """Defines criteria for requesting classical resources."""
    resource_type: ResourceType
    quantity: Union[int, float] # e.g., 4 cores, 16 GB RAM
    custom_filters: List[ResourcePropertyFilter] = field(default_factory=list) # e.g., {"gpu_model": "A100"}

@dataclass
class ResourceRequest:
    """Represents a user's request for resources for a specific job."""
    request_id: str = field(default_factory=lambda: f"rms-req-{uuid.uuid4().hex[:12]}")
    job_id: str
    user_id: str
    project_id: Optional[str] = None
    priority: int = 5 # Lower is higher priority (e.g., 1-10)

    quantum_criteria: List[QuantumResourceCriterion] = field(default_factory=list)
    classical_criteria: List[ClassicalResourceCriterion] = field(default_factory=list)

    estimated_duration_seconds: int # How long resources are needed
    requested_start_time_unix: Optional[float] = None # For future reservation/scheduling
    # allow_partial_allocation: bool = False # Future enhancement

@dataclass
class AllocatedResource:
    """Information about a single allocated resource."""
    global_resource_id: str # e.g., "qpu1::q2", "compute_nodeA::core3"
    local_resource_id: Optional[Any] = None # ID within its parent device/node, if applicable
    parent_device_id: Optional[str] = None # e.g. QPU ID for a qubit
    resource_type: ResourceType
    allocated_properties: Dict[str, Any] = field(default_factory=dict) # Actual properties

@dataclass
class AllocationGrant:
    """Represents a successful allocation of resources."""
    grant_id: str = field(default_factory=lambda: f"rms-grant-{uuid.uuid4().hex[:12]}")
    request_id: str
    job_id: str
    status: str = "SUCCESS" # Could be "PARTIAL_SUCCESS"
    allocated_quantum_resources: List[AllocatedResource] = field(default_factory=list)
    allocated_classical_resources: List[AllocatedResource] = field(default_factory=list)
    allocation_time_unix: float = field(default_factory=time.time)
    expected_release_time_unix: float # Calculated from request.estimated_duration
    message: Optional[str] = None

@dataclass
class AllocationFailure:
    """Represents a failed resource allocation attempt."""
    request_id: str
    job_id: str
    status: str = "FAILED"
    reason_code: str # e.g., "INSUFFICIENT_RESOURCES", "POLICY_VIOLATION", "INVALID_REQUEST"
    message: str
    details: Optional[Dict[str, Any]] = None


# --- RMS Abstract Interface ---

class AbstractRMS(ABC):
    @abstractmethod
    def __init__(self, qhal_service: Any, sacs_service: Any, shms_callback: Optional[Callable]):
        pass

    @abstractmethod
    def submit_resource_request(self, request: ResourceRequest) -> Union[AllocationGrant, AllocationFailure]:
        """Submits a request for quantum and/or classical resources."""
        pass

    @abstractmethod
    def release_resources_by_grant_id(self, grant_id: str, releasing_entity_id: str) -> bool:
        """Releases a set of previously allocated resources identified by their grant ID."""
        pass

    @abstractmethod
    def release_resources_by_job_id(self, job_id: str, releasing_entity_id: str) -> bool:
        """Releases all resources associated with a specific job ID."""
        pass

    @abstractmethod
    def get_allocation_details(self, grant_id: str) -> Optional[AllocationGrant]:
        """Queries the details of a specific resource allocation grant."""
        pass

    @abstractmethod
    def query_available_resources(self, criteria: List[Union[QuantumResourceCriterion, ClassicalResourceCriterion]]) -> Dict[ResourceType, List[Dict[str,Any]]]:
        """Queries current availability of resources matching criteria without allocating."""
        pass

    @abstractmethod
    def update_resource_inventory(self, source_service_name: str, resource_updates: List[Dict[str, Any]]):
        """Allows other services (like QHAL, classical managers) to report new or updated resources."""
        pass

    @abstractmethod
    def report_resource_status_change(self, global_resource_id: str, new_status: str, details: Optional[Dict[str,Any]] = None):
        """Allows other services (like SHMS, QHAL) to report a change in a resource's operational status."""
        pass


# --- RMS Service Implementation ---

@dataclass
class ResourceInstance:
    """Internal representation of a manageable resource."""
    global_id: str
    local_id: Optional[Any]
    parent_device_id: Optional[str]
    type: ResourceType
    properties: Dict[str, Any] = field(default_factory=dict)
    current_status: str = "AVAILABLE" # e.g., AVAILABLE, ALLOCATED, MAINTENANCE, ERROR
    allocated_to_grant_id: Optional[str] = None
    allocated_to_job_id: Optional[str] = None
    # last_heartbeat_unix: Optional[float] = None # For dynamic availability


class RMS_Service(AbstractRMS):
    def __init__(self, qhal_service: Any, sacs_service: Any, shms_callback: Optional[Callable]):
        self.qhal_service = qhal_service # Expected to have methods like get_all_qubit_properties_globally()
        self.sacs_service = sacs_service # Expected for authZ checks
        self._shms_callback = shms_callback

        self._resource_inventory: Dict[str, ResourceInstance] = {} # global_id -> ResourceInstance
        self._active_allocations: Dict[str, AllocationGrant] = {} # grant_id -> AllocationGrant
        self._allocation_policies: Dict[str, Any] = {"default_user_quota": {"QUBIT": 10, "QPU_ACCESS_TIME_SECONDS": 3600}}

        self._initialize_inventory()
        self._log("INFO", "RMS_Service initialized.", {"initial_inventory_size": len(self._resource_inventory)})

    def _log(self, level: str, message: str, data: Optional[Dict[str, Any]] = None):
        if self._shms_callback:
            log_entry = {"timestamp": time.time(), "source": "RMS", "level": level, "message": message, "data": data or {}}
            self._shms_callback(log_entry)
        else: print(f"RMS_LOG [{level}]: {message}" + (f" Data: {data}" if data else ""))

    def _initialize_inventory(self):
        """Populates initial inventory, e.g., by querying QHAL."""
        if self.qhal_service and hasattr(self.qhal_service, 'get_all_qubit_properties_globally'):
            try:
                all_qubit_props = self.qhal_service.get_all_qubit_properties_globally()
                for global_qid, props_dataclass in all_qubit_props.items():
                    # Assuming props_dataclass is QubitProperties from QHAL
                    self._resource_inventory[global_qid] = ResourceInstance(
                        global_id=global_qid,
                        local_id=props_dataclass.qubit_id,
                        parent_device_id=global_qid.split("::")[0] if "::" in global_qid else None,
                        type=ResourceType.QUBIT,
                        properties=props_dataclass.__dict__ # Convert dataclass to dict
                    )
                self._log("INFO", f"Initialized qubit inventory from QHAL with {len(all_qubit_props)} qubits.")
            except Exception as e:
                self._log("ERROR", f"Failed to initialize qubit inventory from QHAL: {e}")
        # Placeholder for classical resource initialization
        # self._resource_inventory["cpu_cluster_0"] = ResourceInstance(global_id="cpu_cluster_0", local_id=None, parent_device_id=None, type=ResourceType.CLASSICAL_COMPUTE_CORE, properties={"total_cores": 128, "available_cores": 128})

    def submit_resource_request(self, request: ResourceRequest) -> Union[AllocationGrant, AllocationFailure]:
        self._log("INFO", f"Received resource request {request.request_id} for job {request.job_id} by user {request.user_id}.")

        # 1. Validate Request (Basic)
        if not request.job_id or not request.user_id or request.estimated_duration_seconds <= 0:
            msg = "Invalid request: Missing job_id, user_id, or invalid duration."
            self._log("WARNING", msg, {"request_id": request.request_id})
            return AllocationFailure(request.request_id, request.job_id, reason_code="INVALID_REQUEST", message=msg)

        # 2. Authorization Check (Conceptual - via SACS)
        # if not self.sacs_service.is_authorized(request.user_id, "request_resources", {"project": request.project_id}):
        #     msg = f"User {request.user_id} not authorized to request resources."
        #     self._log("WARNING", msg, {"request_id": request.request_id, "user_id": request.user_id})
        #     return AllocationFailure(request.request_id, request.job_id, reason_code="AUTHORIZATION_FAILURE", message=msg)

        # 3. Policy Check (Conceptual - e.g., user quotas)
        # current_user_allocations = sum(g.quantum_criteria[0].quantity for g in self._active_allocations.values() if g.job_id.startswith(request.user_id + "_") and g.quantum_criteria and g.quantum_criteria[0].resource_type == ResourceType.QUBIT) # Simplified
        # requested_qubits = sum(qc.quantity for qc in request.quantum_criteria if qc.resource_type == ResourceType.QUBIT)
        # user_qubit_quota = self._allocation_policies.get("default_user_quota", {}).get("QUBIT", 5)
        # if (current_user_allocations + requested_qubits) > user_qubit_quota:
        #     msg = f"User {request.user_id} qubit quota ({user_qubit_quota}) exceeded."
        #     self._log("WARNING", msg, {"request_id": request.request_id, "user_id": request.user_id})
        #     return AllocationFailure(request.request_id, request.job_id, reason_code="POLICY_VIOLATION_QUOTA", message=msg)

        # 4. Find Matching & Available Resources (Simplified: finds first available N qubits)
        allocated_quantum_resources: List[AllocatedResource] = []
        temp_marked_for_allocation: List[str] = [] # Global IDs

        for qc_criterion in request.quantum_criteria:
            if qc_criterion.resource_type == ResourceType.QUBIT:
                found_qubits_for_criterion = 0
                for res_id, res_instance in self._resource_inventory.items():
                    if res_instance.type == ResourceType.QUBIT and \
                       res_instance.current_status == "AVAILABLE" and \
                       res_id not in temp_marked_for_allocation:
                        # TODO: Add detailed property matching against qc_criterion here
                        allocated_quantum_resources.append(AllocatedResource(
                            global_resource_id=res_id,
                            local_resource_id=res_instance.local_id,
                            parent_device_id=res_instance.parent_device_id,
                            resource_type=ResourceType.QUBIT,
                            allocated_properties=res_instance.properties.copy()
                        ))
                        temp_marked_for_allocation.append(res_id)
                        found_qubits_for_criterion += 1
                        if found_qubits_for_criterion >= qc_criterion.quantity:
                            break
                if found_qubits_for_criterion < qc_criterion.quantity:
                    msg = f"Insufficient available qubits matching criteria for request {request.request_id}."
                    self._log("WARNING", msg)
                    return AllocationFailure(request.request_id, request.job_id, reason_code="INSUFFICIENT_RESOURCES", message=msg)

        # TODO: Implement classical resource allocation similarly

        # 5. If successful, finalize allocation
        for g_qid in temp_marked_for_allocation:
            self._resource_inventory[g_qid].current_status = "ALLOCATED"
            self._resource_inventory[g_qid].allocated_to_job_id = request.job_id
            # grant_id will be set when AllocationGrant is created

        grant = AllocationGrant(
            request_id=request.request_id,
            job_id=request.job_id,
            allocated_quantum_resources=allocated_quantum_resources,
            # allocated_classical_resources=...
            expected_release_time_unix=time.time() + request.estimated_duration_seconds
        )
        # Link back allocated resources to this grant_id
        for res_info in allocated_quantum_resources:
            self._resource_inventory[res_info.global_resource_id].allocated_to_grant_id = grant.grant_id

        self._active_allocations[grant.grant_id] = grant
        self._log("INFO", f"Resources successfully allocated for grant {grant.grant_id} (Job: {request.job_id}).")
        return grant

    def release_resources_by_grant_id(self, grant_id: str, releasing_entity_id: str) -> bool:
        grant = self._active_allocations.pop(grant_id, None)
        if not grant:
            self._log("WARNING", f"Attempt to release non-existent or already released grant ID: {grant_id} by {releasing_entity_id}")
            return False

        released_count = 0
        for res_info in grant.allocated_quantum_resources + grant.allocated_classical_resources:
            if res_info.global_resource_id in self._resource_inventory:
                instance = self._resource_inventory[res_info.global_resource_id]
                if instance.allocated_to_grant_id == grant_id:
                    instance.current_status = "AVAILABLE"
                    instance.allocated_to_grant_id = None
                    instance.allocated_to_job_id = None
                    released_count +=1
                else:
                    self._log("ERROR", f"Mismatch: Resource {res_info.global_resource_id} in grant {grant_id} not marked as allocated to it.", {"current_grant": instance.allocated_to_grant_id})
            else:
                 self._log("ERROR", f"Resource {res_info.global_resource_id} from grant {grant_id} not found in inventory during release.")

        self._log("INFO", f"Released {released_count} resources for grant {grant_id} by {releasing_entity_id}.")
        return True

    def release_resources_by_job_id(self, job_id: str, releasing_entity_id: str) -> bool:
        grants_for_job = [gid for gid, grant in self._active_allocations.items() if grant.job_id == job_id]
        if not grants_for_job:
            self._log("INFO", f"No active allocations found for job ID: {job_id} to be released by {releasing_entity_id}.")
            return True # No error if nothing to release

        all_released_successfully = True
        for grant_id in grants_for_job:
            if not self.release_resources_by_grant_id(grant_id, releasing_entity_id):
                all_released_successfully = False # Log individual failures within the above call

        if all_released_successfully:
             self._log("INFO", f"All resources for job {job_id} released successfully by {releasing_entity_id}.")
        else:
             self._log("WARNING", f"Some resources for job {job_id} could not be released by {releasing_entity_id}.")
        return all_released_successfully

    def get_allocation_details(self, grant_id: str) -> Optional[AllocationGrant]:
        return self._active_allocations.get(grant_id)

    def query_available_resources(self, criteria: List[Union[QuantumResourceCriterion, ClassicalResourceCriterion]]) -> Dict[ResourceType, List[Dict[str,Any]]]:
        # This is a simplified query. A real one would deeply filter properties.
        availability: Dict[ResourceType, List[Dict[str,Any]]] = {rt: [] for rt in ResourceType}
        for res_id, res_instance in self._resource_inventory.items():
            if res_instance.current_status == "AVAILABLE":
                # Basic type matching for now
                for crit in criteria:
                    if res_instance.type == crit.resource_type:
                        # TODO: Implement detailed matching of criteria (T1, fidelity, etc.)
                        availability[res_instance.type].append(res_instance.properties)
                        break
        return availability

    def update_resource_inventory(self, source_service_name: str, resource_updates: List[Dict[str, Any]]):
        """
        Generic way to add/update resources. `resource_updates` is a list of dicts,
        each dict conforming to ResourceInstance structure or a subset for updates.
        """
        self._log("INFO", f"Received inventory update from {source_service_name}.", {"num_updates": len(resource_updates)})
        for update_data in resource_updates:
            gid = update_data.get("global_id")
            if not gid:
                self._log("WARNING", "Inventory update skipped: missing global_id.", {"update_data": update_data})
                continue

            if gid in self._resource_inventory: # Update existing
                instance = self._resource_inventory[gid]
                for key, value in update_data.items():
                    if hasattr(instance, key): setattr(instance, key, value)
                    elif key in instance.properties: instance.properties[key] = value
                    else: instance.properties[key] = value # Add new property
                self._log("INFO", f"Updated resource in inventory: {gid}")
            else: # Add new
                try:
                    # Ensure essential fields are present for new resource
                    if not all(k in update_data for k in ["type"]): # local_id, parent_device_id might be optional
                        self._log("WARNING", f"Skipping new resource {gid}: missing essential fields (type).")
                        continue

                    # Convert type string to Enum if necessary
                    res_type_val = update_data["type"]
                    if isinstance(res_type_val, str):
                        try: res_type = ResourceType[res_type_val.upper()]
                        except KeyError: res_type = ResourceType(res_type_val) # if value matches enum's value
                    elif isinstance(res_type_val, ResourceType):
                        res_type = res_type_val
                    else:
                        self._log("WARNING", f"Invalid resource type for new resource {gid}: {res_type_val}")
                        continue

                    self._resource_inventory[gid] = ResourceInstance(
                        global_id=gid,
                        local_id=update_data.get("local_id"),
                        parent_device_id=update_data.get("parent_device_id"),
                        type=res_type,
                        properties=update_data.get("properties", {}),
                        current_status=update_data.get("current_status", "AVAILABLE")
                    )
                    self._log("INFO", f"Added new resource to inventory: {gid}")
                except Exception as e:
                    self._log("ERROR", f"Failed to add new resource {gid} from update: {e}", {"update_data": update_data})

    def report_resource_status_change(self, global_resource_id: str, new_status_str: str, details: Optional[Dict[str,Any]] = None):
        if global_resource_id in self._resource_inventory:
            instance = self._resource_inventory[global_resource_id]
            old_status = instance.current_status
            instance.current_status = new_status_str
            # If resource becomes unavailable/error while allocated, special handling needed (e.g. notify job owner via AES/PTSS)
            if instance.allocated_to_grant_id and new_status_str in ["ERROR", "MAINTENANCE", "UNAVAILABLE"]:
                self._log("CRITICAL", f"Allocated resource {global_resource_id} changed status to {new_status_str}!",
                          {"grant_id": instance.allocated_to_grant_id, "job_id": instance.allocated_to_job_id, "details": details})
                # TODO: Trigger further actions - e.g. re-allocation attempt, job failure notification
            else:
                self._log("INFO", f"Status of resource {global_resource_id} changed from {old_status} to {new_status_str}.", {"details": details})
        else:
            self._log("WARNING", f"Status report for unknown resource ID: {global_resource_id}")

print("CHIMera QOS - RMS Service Blueprint Definition Complete.")
