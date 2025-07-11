import unittest
from unittest.mock import MagicMock, PropertyMock
import time

# Adjust import path
from ..rms import RMS_Service, ResourceRequest, QuantumResourceCriterion, ResourceType, AllocationGrant, AllocationFailure, ResourceInstance
# Need to mock QHALService and its qubit objects/properties for RMS tests
from ...qhal_service.qhal import AbstractQubit, QubitProperties # Assuming these are importable for type hinting/mocking

class MockQHALQubit(AbstractQubit):
    def __init__(self, local_id, global_id, props=None):
        self._local_id = local_id
        self._global_id = global_id
        self._props = props if props else QubitProperties(qubit_id=local_id, global_qubit_id=global_id)
        self._status = MagicMock() # Mock status if needed by RMS through QHAL

    def get_id(self) -> Any: return self._local_id
    def get_global_id(self) -> str: return self._global_id
    def get_status(self) -> Any: return self._status
    def set_status(self, status: Any) -> None: pass
    def get_properties(self) -> QubitProperties: return self._props
    def update_properties(self, new_properties: Dict[str, Any]) -> None: pass

class TestRMSService_Phase1_QubitFocus(unittest.TestCase):

    def setUp(self):
        self.mock_qhal_service = MagicMock()
        self.num_sim_qubits = 5

        mock_qubits = []
        for i in range(self.num_sim_qubits):
            gid = f"sim_qpu::q{i}"
            props = QubitProperties(qubit_id=f"q{i}", global_qubit_id=gid, t1_time=100e-6, readout_fidelity=0.99)
            mock_qubits.append(MockQHALQubit(local_id=f"q{i}", global_id=gid, props=props))

        self.mock_qhal_service.get_all_global_qubits = MagicMock(return_value=mock_qubits)

        self.mock_sacs_service = MagicMock()
        self.mock_shms_callback = MagicMock()

        self.rms = RMS_Service(
            qhal_service=self.mock_qhal_service,
            sacs_service=self.mock_sacs_service,
            shms_callback=self.mock_shms_callback
        )

    def test_initialize_inventory_from_qhal(self):
        self.assertEqual(len(self.rms._resource_inventory), self.num_sim_qubits)
        for i in range(self.num_sim_qubits):
            gid = f"sim_qpu::q{i}"
            self.assertIn(gid, self.rms._resource_inventory)
            self.assertEqual(self.rms._resource_inventory[gid].type, ResourceType.QUBIT)
            self.assertEqual(self.rms._resource_inventory[gid].current_status, "AVAILABLE")
            self.assertEqual(self.rms._resource_inventory[gid].properties.get('t1_time'), 100e-6)

    def test_request_and_release_qubits_successfully(self):
        req = ResourceRequest(
            job_id="job123", user_id="user_test",
            quantum_criteria=[QuantumResourceCriterion(resource_type=ResourceType.QUBIT, quantity=2)],
            estimated_duration_seconds=60
        )
        allocation_result = self.rms.submit_resource_request(req)

        self.assertIsInstance(allocation_result, AllocationGrant)
        self.assertEqual(allocation_result.status, "SUCCESS")
        self.assertEqual(len(allocation_result.allocated_quantum_resources), 2)

        allocated_gids = [res.global_resource_id for res in allocation_result.allocated_quantum_resources]
        self.assertIn(self.rms._resource_inventory[allocated_gids[0]].current_status, "ALLOCATED")
        self.assertEqual(self.rms._resource_inventory[allocated_gids[0]].allocated_to_grant_id, allocation_result.grant_id)
        self.assertEqual(self.rms._resource_inventory[allocated_gids[0]].allocated_to_job_id, "job123")

        # Test release
        release_ok = self.rms.release_resources_by_grant_id(allocation_result.grant_id, "AES_Service")
        self.assertTrue(release_ok)
        self.assertNotIn(allocation_result.grant_id, self.rms._active_allocations)
        self.assertEqual(self.rms._resource_inventory[allocated_gids[0]].current_status, "AVAILABLE")
        self.assertIsNone(self.rms._resource_inventory[allocated_gids[0]].allocated_to_grant_id)

    def test_request_qubits_insufficient_resources(self):
        req = ResourceRequest(
            job_id="job456", user_id="user_test",
            quantum_criteria=[QuantumResourceCriterion(resource_type=ResourceType.QUBIT, quantity=self.num_sim_qubits + 1)],
            estimated_duration_seconds=60
        )
        allocation_result = self.rms.submit_resource_request(req)
        self.assertIsInstance(allocation_result, AllocationFailure)
        self.assertEqual(allocation_result.reason_code, "INSUFFICIENT_RESOURCES")

    def test_request_qubits_partial_then_full_allocation(self):
        req1 = ResourceRequest(job_id="job789a", user_id="user_a", quantum_criteria=[QuantumResourceCriterion(resource_type=ResourceType.QUBIT, quantity=3)], estimated_duration_seconds=30)
        grant1 = self.rms.submit_resource_request(req1)
        self.assertIsInstance(grant1, AllocationGrant)
        self.assertEqual(len(grant1.allocated_quantum_resources), 3)

        # Try to allocate more than remaining
        req2 = ResourceRequest(job_id="job789b", user_id="user_b", quantum_criteria=[QuantumResourceCriterion(resource_type=ResourceType.QUBIT, quantity=3)], estimated_duration_seconds=30) # Only 2 left
        failure2 = self.rms.submit_resource_request(req2)
        self.assertIsInstance(failure2, AllocationFailure)

        # Release first allocation
        self.rms.release_resources_by_grant_id(grant1.grant_id, "user_a")

        # Try second allocation again
        grant2 = self.rms.submit_resource_request(req2) # Should now succeed for 3 qubits
        self.assertIsInstance(grant2, AllocationGrant)
        self.assertEqual(len(grant2.allocated_quantum_resources), 3)

    def test_get_allocation_details(self):
        req = ResourceRequest(job_id="job_detail", user_id="user_test", quantum_criteria=[QuantumResourceCriterion(resource_type=ResourceType.QUBIT, quantity=1)], estimated_duration_seconds=10)
        grant = self.rms.submit_resource_request(req)
        self.assertIsInstance(grant, AllocationGrant)

        details = self.rms.get_allocation_details(grant.grant_id)
        self.assertIsNotNone(details)
        self.assertEqual(details.job_id, "job_detail")
        self.assertEqual(len(details.allocated_quantum_resources), 1)

        self.assertIsNone(self.rms.get_allocation_details("non_existent_grant"))

    def test_query_available_resources_simple(self):
        # Initially all qubits are available
        query_crit = [QuantumResourceCriterion(resource_type=ResourceType.QUBIT, quantity=1)]
        availability = self.rms.query_available_resources(query_crit)
        self.assertIn(ResourceType.QUBIT, availability)
        self.assertEqual(len(availability[ResourceType.QUBIT]), self.num_sim_qubits)

        # Allocate some
        req = ResourceRequest(job_id="job_query", user_id="user_q", quantum_criteria=[QuantumResourceCriterion(resource_type=ResourceType.QUBIT, quantity=2)], estimated_duration_seconds=10)
        self.rms.submit_resource_request(req)

        availability_after_alloc = self.rms.query_available_resources(query_crit)
        self.assertIn(ResourceType.QUBIT, availability_after_alloc)
        self.assertEqual(len(availability_after_alloc[ResourceType.QUBIT]), self.num_sim_qubits - 2)

if __name__ == '__main__':
    unittest.main()
