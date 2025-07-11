import unittest
from unittest.mock import MagicMock
import time

# Adjust import path
from ..pecs import SimulatedTemperatureController, SimulatedVacuumGauge, ParameterValue, SubSystemType, PECSParameterError, PECSCommandError

class TestSimulatedTemperatureController(unittest.TestCase):
    def setUp(self):
        self.device_id = "cryo_stage1"
        self.device_name = "MainCryostatStage1"
        self.config = {
            "initial_temp_K": 4.5, "setpoint_K": 4.2, "min_temp_K": 0.010, "max_temp_K": 300,
            "cooling_power_W": 0.5, "heating_power_W": 2.0, "thermal_mass_J_per_K": 1500
        }
        self.mock_pecs_callback = MagicMock()
        self.tc = SimulatedTemperatureController(self.device_id, self.device_name, self.config, self.mock_pecs_callback)
        self.tc.connect()

    def test_initial_state(self):
        self.assertTrue(self.tc.is_connected())
        self.assertEqual(self.tc.get_device_name(), self.device_name)
        status = self.tc.get_device_status_summary()
        self.assertEqual(status["temperature_K"], 4.5)
        self.assertEqual(status["setpoint_K"], 4.2) # Initial setpoint from config
        self.assertFalse(status["ramping"])

    def test_set_setpoint_and_ramp(self):
        self.tc.set_parameter_value("setpoint_temperature_K", 1.0)
        status = self.tc.get_device_status_summary()
        self.assertEqual(status["setpoint_K"], 1.0)
        self.assertTrue(status["ramping"])

        # Simulate time passing for ramp
        time.sleep(0.1) # Allow a very short time for simulation step
        self.tc._update_simulated_state() # Force update
        status_after_ramp_start = self.tc.get_device_status_summary()
        self.assertLess(status_after_ramp_start["temperature_K"], 4.5) # Should be cooling

        # Test stop ramp command
        self.tc.execute_command("stop_ramp")
        self.assertFalse(self.tc.get_device_status_summary()["ramping"])

    def test_set_heater_power(self):
        self.tc.set_parameter_value("heater_power_percent", 50.0)
        status = self.tc.get_parameter_value("heater_power_percent")
        self.assertEqual(status.value, 50.0)
        self.assertTrue(self.tc.get_device_status_summary()["heater_active"])
        self.assertFalse(self.tc.get_device_status_summary()["ramping"]) # Manual heater should stop ramp

        self.tc.set_parameter_value("heater_power_percent", 0.0)
        self.assertFalse(self.tc.get_device_status_summary()["heater_active"])

    def test_parameter_errors(self):
        with self.assertRaises(PECSParameterError):
            self.tc.get_parameter_value("non_existent_param")
        with self.assertRaises(PECSParameterError):
            self.tc.set_parameter_value("current_temperature_K", 10.0) # Read-only
        with self.assertRaises(PECSParameterError):
            self.tc.set_parameter_value("setpoint_temperature_K", 500.0) # Out of range


class TestSimulatedVacuumGauge(unittest.TestCase):
    def setUp(self):
        self.device_id = "vac_chamber1"
        self.device_name = "MainExperimentalChamber"
        self.config = {
            "initial_pressure_mbar": 1e-6, "target_pressure_mbar": 1e-7,
            "min_pressure_mbar": 1e-9, "max_pressure_mbar": 1013.0,
            "pump_down_rate_factor": 0.2, "leak_rate_factor": 0.01
        }
        self.mock_pecs_callback = MagicMock()
        self.vg = SimulatedVacuumGauge(self.device_id, self.device_name, self.config, self.mock_pecs_callback)
        self.vg.connect()

    def test_initial_state_vacuum(self):
        self.assertTrue(self.vg.is_connected())
        status = self.vg.get_device_status_summary()
        self.assertAlmostEqual(float(status["pressure_mbar"]), 1e-6, places=8)
        self.assertFalse(status["pump_on"])

    def test_pump_control_and_pressure_change(self):
        self.vg.execute_command("start_pump")
        self.assertTrue(self.vg.get_device_status_summary()["pump_on"])

        initial_pressure = self.vg.get_parameter_value("current_pressure_mbar").value
        time.sleep(0.1) # Simulate time for pumping
        self.vg._update_simulated_state() # Force update

        pressure_after_pump = self.vg.get_parameter_value("current_pressure_mbar").value
        self.assertLess(pressure_after_pump, initial_pressure)

        self.vg.execute_command("stop_pump")
        self.assertFalse(self.vg.get_device_status_summary()["pump_on"])
        pressure_after_stop = self.vg.get_parameter_value("current_pressure_mbar").value
        time.sleep(0.1) # Simulate time for leaking
        self.vg._update_simulated_state()
        pressure_after_leak = self.vg.get_parameter_value("current_pressure_mbar").value
        self.assertGreater(pressure_after_leak, pressure_after_stop)

if __name__ == '__main__':
    unittest.main()
