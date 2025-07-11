import unittest
from unittest.mock import MagicMock, patch

# Adjust import path
from ..pecs import PECS_Service, SimulatedTemperatureController, SimulatedVacuumGauge, SubSystemType, ParameterDefinition, ParameterValue, PECSDeviceError

class TestPECSService(unittest.TestCase):
    def setUp(self):
        self.mock_shms_callback = MagicMock()
        self.pecs_service = PECS_Service(shms_integration_callback=self.mock_shms_callback)

        # Configs for mock devices
        self.tc_config = {"initial_temp_K": 290, "setpoint_K": 4.2}
        self.vg_config = {"initial_pressure_mbar": 1000}

    def test_register_and_unregister_device(self):
        reg_tc_ok = self.pecs_service.register_device(
            SimulatedTemperatureController, "cryo1", "Cryo Stage 1", self.tc_config, SubSystemType.CRYOGENICS
        )
        self.assertTrue(reg_tc_ok)
        self.assertIn("cryo1", self.pecs_service._devices)
        self.assertEqual(len(self.pecs_service._devices_by_subsystem[SubSystemType.CRYOGENICS]), 1)

        # Test registering duplicate
        reg_tc_again_ok = self.pecs_service.register_device(
            SimulatedTemperatureController, "cryo1", "Cryo Stage 1 Duplicate", self.tc_config, SubSystemType.CRYOGENICS
        )
        self.assertFalse(reg_tc_again_ok) # Should fail

        all_devices = self.pecs_service.get_all_devices_summary()
        self.assertEqual(len(all_devices), 1)
        self.assertEqual(all_devices[0]["device_id"], "cryo1")

        unreg_ok = self.pecs_service.unregister_device("cryo1")
        self.assertTrue(unreg_ok)
        self.assertNotIn("cryo1", self.pecs_service._devices)
        self.assertEqual(len(self.pecs_service._devices_by_subsystem[SubSystemType.CRYOGENICS]), 0)

        unreg_fail = self.pecs_service.unregister_device("non_existent_dev")
        self.assertFalse(unreg_fail)

    def test_device_interaction_via_service(self):
        self.pecs_service.register_device(
            SimulatedTemperatureController, "tc1", "Test TC", self.tc_config, SubSystemType.CRYOGENICS
        )

        # List parameters
        params = self.pecs_service.get_device_parameters("tc1")
        self.assertIsInstance(params, list)
        self.assertTrue(any(p.name == "current_temperature_K" for p in params))

        # Read parameter
        temp_val = self.pecs_service.read_device_parameter("tc1", "current_temperature_K")
        self.assertIsInstance(temp_val, ParameterValue)
        self.assertEqual(temp_val.unit, "K")
        self.assertAlmostEqual(temp_val.value, 290, delta=1) # Initial temp

        # Write parameter
        write_ok = self.pecs_service.write_device_parameter("tc1", "setpoint_temperature_K", 10.0)
        self.assertTrue(write_ok)
        setpoint_val = self.pecs_service.read_device_parameter("tc1", "setpoint_temperature_K")
        self.assertAlmostEqual(setpoint_val.value, 10.0)

        # Send command
        cmd_result = self.pecs_service.send_device_command("tc1", "start_ramp_to_setpoint", {"target_K": 5.0})
        self.assertTrue(cmd_result.get("success"))
        self.assertIn("Ramping to 5.0K", cmd_result.get("message",""))

        # Test interaction with non-existent device
        with self.assertRaises(PECSDeviceError):
            self.pecs_service.read_device_parameter("tc_fake", "current_temperature_K")

    def test_get_subsystem_overview(self):
        self.pecs_service.register_device(SimulatedTemperatureController, "tc1", "TC1", self.tc_config, SubSystemType.CRYOGENICS)
        self.pecs_service.register_device(SimulatedVacuumGauge, "vg1", "VG1", self.vg_config, SubSystemType.VACUUM)

        cryo_overview = self.pecs_service.get_subsystem_overview(SubSystemType.CRYOGENICS)
        self.assertEqual(len(cryo_overview), 1)
        self.assertEqual(cryo_overview[0]["device_id"], "tc1")

        vacuum_overview = self.pecs_service.get_subsystem_overview(SubSystemType.VACUUM)
        self.assertEqual(len(vacuum_overview), 1)
        self.assertEqual(vacuum_overview[0]["device_id"], "vg1")

        laser_overview = self.pecs_service.get_subsystem_overview(SubSystemType.LASER_SYSTEM)
        self.assertEqual(len(laser_overview), 0)

    def test_shms_logging_callback(self):
        # Register a device, which should trigger a log via callback
        self.pecs_service.register_device(SimulatedTemperatureController, "log_tc", "LogTC", self.tc_config, SubSystemType.CRYOGENICS)
        self.mock_shms_callback.assert_called()

        # Check if the log message for registration was called
        # Example: find a call where the message contains "registered to PECS"
        found_registration_log = False
        for call_args in self.mock_shms_callback.call_args_list:
            log_entry = call_args[0][0] # First positional argument of the callback
            if "registered to PECS" in log_entry.get("message", ""):
                found_registration_log = True
                self.assertEqual(log_entry.get("source"), "PECS")
                self.assertEqual(log_entry.get("level"), "INFO")
                break
        self.assertTrue(found_registration_log, "SHMS callback for device registration not found or incorrect.")


if __name__ == '__main__':
    unittest.main()
