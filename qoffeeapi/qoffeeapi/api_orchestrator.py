from notebook.base.handlers import IPythonHandler
from qoffeeapi.hc_connector import get_connector
from qoffeeapi.utils import proxy
from tornado import web
import dotenv
dotenv.load_dotenv()

# fetch the current state of the machine from the API
class OrchestratorMachineStateHandler(IPythonHandler):
    @web.authenticated
    def get(self):
        connector = get_connector()
        if not connector.machine or not connector.machine.get("haId"):
            self.set_status(400)
            self.finish({"error": "No machine selected or haId missing."})
            return

        ha_id = connector.machine["haId"]
        status_key = "BSH.Common.Status.OperationState"

        try:
            data, source, last_updated = connector.get_ha_status(ha_id, status_key)

            response_payload = {
                "data": data, # data is already the response body or error dict from connector
                "source": source,
                "last_updated": last_updated,
                "haId": ha_id,
                "status_key": status_key
            }

            if isinstance(data, dict) and "error" in data:
                if source in ["offline_no_cache", "cached_became_offline_no_cache"] or data.get("error") == "offline_no_cache":
                    self.set_status(503) # Service Unavailable
                else:
                    self.set_status(400) # Bad request or other error from cache layer
            # If source is "live", data should be the actual successful response body.
            # RuntimeErrors from connector.get_ha_status cover live call failures.

            self.finish(response_payload)

        except RuntimeError as e: # This catches actual errors from live calls or critical internal issues
            self.set_status(500)
            self.finish({"error": str(e), "source": "runtime_error", "haId": ha_id, "status_key": status_key})
        except Exception as e: # Catch any other unexpected errors
            self.set_status(500)
            self.finish({"error": f"An unexpected error occurred: {str(e)}", "source": "unexpected_error"})

# Get summary of Home Connect command queues
class OrchestratorHCQueueStatusHandler(IPythonHandler):
    @web.authenticated
    def get(self):
        connector = get_connector()
        try:
            summary = connector.get_queue_summary()
            self.finish(summary)
        except Exception as e:
            self.set_status(500)
            self.finish({"error": f"An unexpected error occurred while fetching queue status: {str(e)}"})

# Retry a failed Home Connect command
class OrchestratorHCRetryFailedCommandHandler(IPythonHandler):
    @web.authenticated
    def post(self):
        connector = get_connector()
        try:
            body = self.get_json_body()
            if body is None or "command_index" not in body:
                self.set_status(400)
                self.finish({"error": "Missing 'command_index' in request body."})
                return

            command_index = int(body["command_index"])
            success = connector.retry_failed_command(command_index)

            if success:
                # Also trigger a queue process attempt
                if connector.is_online:
                    connector.process_command_queue()
                self.finish({"message": f"Command at index {command_index} moved to active queue for retry.", "new_queue_status": connector.get_queue_summary()})
            else:
                self.set_status(404) # Or 400 if index format is bad vs index not found
                self.finish({"error": f"Command at index {command_index} not found or could not be retried.", "new_queue_status": connector.get_queue_summary()})
        except ValueError:
            self.set_status(400)
            self.finish({"error": "'command_index' must be an integer."})
        except Exception as e:
            self.set_status(500)
            self.finish({"error": f"An unexpected error occurred: {str(e)}"})

# Delete a failed Home Connect command
class OrchestratorHCDeleteFailedCommandHandler(IPythonHandler):
    @web.authenticated
    def post(self):
        connector = get_connector()
        try:
            body = self.get_json_body()
            if body is None or "command_index" not in body:
                self.set_status(400)
                self.finish({"error": "Missing 'command_index' in request body."})
                return

            command_index = int(body["command_index"])
            success = connector.delete_failed_command(command_index)

            if success:
                self.finish({"message": f"Command at index {command_index} deleted from failed queue.", "new_queue_status": connector.get_queue_summary()})
            else:
                self.set_status(404) # Or 400
                self.finish({"error": f"Command at index {command_index} not found or could not be deleted.", "new_queue_status": connector.get_queue_summary()})
        except ValueError:
            self.set_status(400)
            self.finish({"error": "'command_index' must be an integer."})
        except Exception as e:
            self.set_status(500)
            self.finish({"error": f"An unexpected error occurred: {str(e)}"})


# get power state and turn on machine from the API
class OrchestratorMachinePowerHandler(IPythonHandler):
    @web.authenticated
    def get(self):
        connector = get_connector()
        if not connector.machine or not connector.machine.get("haId"):
            self.set_status(400)
            self.finish({"error": "No machine selected or haId missing."})
            return

        ha_id = connector.machine["haId"]
        setting_key = "BSH.Common.Setting.PowerState"

        try:
            data, source, last_updated = connector.get_ha_setting(ha_id, setting_key)

            response_payload = {
                "data": data, # data is already the response body or error dict from connector
                "source": source,
                "last_updated": last_updated,
                "haId": ha_id,
                "setting_key": setting_key
            }

            if isinstance(data, dict) and "error" in data:
                if source in ["offline_no_cache", "cached_became_offline_no_cache"] or data.get("error") == "offline_no_cache":
                    self.set_status(503) # Service Unavailable
                else:
                    self.set_status(400) # Bad request or other error from cache layer

            self.finish(response_payload)

        except RuntimeError as e: # This catches actual errors from live calls or critical internal issues
            self.set_status(500)
            self.finish({"error": str(e), "source": "runtime_error", "haId": ha_id, "setting_key": setting_key})
        except Exception as e:
            self.set_status(500)
            self.finish({"error": f"An unexpected error occurred: {str(e)}", "source": "unexpected_error"})

    @web.authenticated
    def post(self): # This is to turn the machine ON
        connector = get_connector()
        if not connector.machine or not connector.machine.get("haId"):
            self.set_status(400)
            self.finish({"error": "No machine selected or haId missing."})
            return

        ha_id = connector.machine["haId"]
        setting_key = "BSH.Common.Setting.PowerState"
        payload = {
            "data": {
                "key": setting_key,
                "value": "BSH.Common.EnumType.PowerState.On"
            }
        }

        try:
            status_code, response_body = connector.set_ha_setting(ha_id, setting_key, payload)

            self.set_status(status_code)
            self.finish(response_body) # response_body will indicate queued or live status

        except RuntimeError as e: # Should not happen if set_ha_setting handles errors gracefully
            self.set_status(500)
            self.finish({"error": str(e), "source": "runtime_error", "haId": ha_id, "setting_key": setting_key})
        except Exception as e:
            self.set_status(500)
            self.finish({"error": f"An unexpected error occurred: {str(e)}", "source": "unexpected_error"})

# get/set the the machine using enumber
class OrchestratorMachineHandler(IPythonHandler):
    @web.authenticated
    def get(self):
        connector = get_connector()
        self.finish(connector.machine)

    @web.authenticated
    def post(self):
        body = self.get_json_body()
        connector = get_connector()
        enumber = None if (body is None or "enumber" not in body) else body["enumber"]
        connector.set_machine(enumber)
        self.finish(connector.machine)

# get all machines associated to the current account
class OrchestratorAllMachinesHandler(IPythonHandler):
    @web.authenticated
    def get(self):
        connector = get_connector()
        try:
            machines_data, source, last_updated = connector.get_machines()
            response_payload = {
                "machines": machines_data, # This is the list of appliance dicts
                "source": source,
                "last_updated": last_updated
            }
            if source == "offline_no_cache":
                self.set_status(503) # Service Unavailable

            self.finish(response_payload)
        except RuntimeError as e:
            self.set_status(500)
            self.finish({"error": str(e), "source": "runtime_error"})
        except Exception as e:
            self.set_status(500)
            self.finish({"error": f"An unexpected error occurred: {str(e)}", "source": "unexpected_error"})


# send a request to the coffee machine to create a drink
class OrchestratorDrinkRequestHandler(IPythonHandler):
    @web.authenticated
    def post(self):
        connector = get_connector()
        body = self.get_json_body()
        drinkKey = body['key']
        # merge drink options with options from request
        drinkOptions = body['options']
        # convert to required format
        drinkOptionsList = list(map(lambda x: {
            'key': x,
            'value': drinkOptions[x]
        }, drinkOptions.keys()))

        # send put request
        program_payload = {
            "data": {
                "key": drinkKey,
                "options": drinkOptionsList
            }
        }

        ha_id = connector.machine["haId"]
        if not ha_id:
            self.set_status(400)
            self.finish({"error": "No machine selected or haId missing."})
            return

        try:
            status_code, response_body = connector.program_drink(ha_id, program_payload)
            self.set_status(status_code)
            self.finish(response_body) # response_body will indicate queued or live status

        except RuntimeError as e: # Should not happen
            self.set_status(500)
            self.finish({"error": str(e), "source": "runtime_error", "haId": ha_id})
        except Exception as e:
            self.set_status(500)
            self.finish({"error": f"An unexpected error occurred: {str(e)}", "source": "unexpected_error"})
