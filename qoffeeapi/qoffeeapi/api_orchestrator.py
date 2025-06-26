"""
API handlers that orchestrate interactions with the Home Connect API via the
HomeconnectConnector. These handlers are exposed as Jupyter server extensions
and are responsible for:
- Fetching machine status and settings.
- Controlling machine power and programs (e.g., ordering drinks).
- Managing the selection of the active coffee machine.
- Providing status and management for offline command queues.

They incorporate offline awareness, returning cached data or queueing commands
as appropriate, and structure responses to inform the client about data source
and command status.
"""
from notebook.base.handlers import IPythonHandler
from qoffeeapi.hc_connector import get_connector
# from qoffeeapi.utils import proxy # No longer used in this file
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

# System Health Check
class OrchestratorHealthCheckHandler(IPythonHandler):
    def get(self):
        # No @web.authenticated, this should be a public endpoint for diagnostics
        import datetime
        import os # For IBMQ_API_KEY and file checks

        connector = get_connector() # Initialize/get the connector to check its state

        health_status = {
            "overall_status": "OK", # Will be changed if issues are found
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "services": {
                "home_connect_api": {
                    "status": "UNKNOWN", "message": "",
                    "details": {
                        "api_url_configured": bool(connector.api_base_url),
                        "client_id_configured": bool(connector.client_id),
                        "tokens_exist": bool(connector.tokens and "access_token" in connector.tokens),
                        "can_reach_api": connector.is_online, # Relies on prior checks by connector
                        "token_last_refreshed_at": connector.tokens.get("last_refresh_time") if connector.tokens else None, # Assuming tokens dict might store this
                        "token_expires_at": datetime.datetime.fromtimestamp(connector.tokens.get("expires_at")).isoformat() + "Z" if connector.tokens and connector.tokens.get("expires_at") else None
                    }
                },
                "ibmq": {
                    "status": "UNKNOWN", "message": "",
                    "details": {"api_key_set": bool(os.getenv("IBMQ_API_KEY"))}
                },
                "local_storage": {
                    "status": "UNKNOWN", "message": "",
                    "details": {
                        "config_file_path": connector.path, # .user/oauth-token.json
                        "config_file_exists": os.path.isfile(connector.path if connector.path else ""),
                        "user_dir_writable": os.access(".user/", os.W_OK) if os.path.isdir(".user/") else False
                    }
                }
            },
            "queues": connector.get_queue_summary() if connector else {
                "active_commands": "N/A", "failed_commands": "N/A", "failed_commands_summary": []
            }
        }

        # --- Home Connect API Status Logic ---
        hc_service = health_status["services"]["home_connect_api"]
        if not hc_service["details"]["api_url_configured"] or not hc_service["details"]["client_id_configured"]:
            hc_service["status"] = "UNCONFIGURED"
            hc_service["message"] = "Home Connect API URL or Client ID is not configured."
            health_status["overall_status"] = "ERROR"
        elif not hc_service["details"]["tokens_exist"]:
            hc_service["status"] = "NOT_AUTHENTICATED"
            hc_service["message"] = "Not authenticated with Home Connect. Please login via /auth."
            if health_status["overall_status"] != "ERROR": health_status["overall_status"] = "WARNING"
        elif not hc_service["details"]["can_reach_api"]:
            hc_service["status"] = "OFFLINE"
            hc_service["message"] = "Home Connect API seems unreachable (connector is offline)."
            if health_status["overall_status"] != "ERROR": health_status["overall_status"] = "WARNING"
        else: # Online and tokens exist
            # Basic check: if token_expires_at is available and in the past
            if hc_service["details"]["token_expires_at"]:
                try:
                    # Assuming expires_at is a UNIX timestamp
                    expiry_time = connector.tokens.get("expires_at") # This is usually a future timestamp
                    # Home Connect tokens usually include "expires_in" (seconds from issue).
                    # A true "expires_at" would need to be calculated: issued_at + expires_in.
                    # For simplicity, if 'expires_at' was stored as an absolute timestamp:
                    if expiry_time and expiry_time < time.time():
                         hc_service["status"] = "TOKEN_EXPIRED"
                         hc_service["message"] = "Home Connect access token appears to be expired. Refresh may be needed."
                         if health_status["overall_status"] != "ERROR": health_status["overall_status"] = "WARNING"
                    else:
                        hc_service["status"] = "AUTHENTICATED"
                        hc_service["message"] = "Home Connect API configured, online, and authenticated."
                except Exception: # Error parsing time etc.
                     hc_service["status"] = "AUTHENTICATED" # Assume ok if parsing fails for now
                     hc_service["message"] = "Home Connect API configured, online, and authenticated (expiry check error)."
            else: # No expiry info in token to check easily
                hc_service["status"] = "AUTHENTICATED"
                hc_service["message"] = "Home Connect API configured, online, and authenticated."


        # --- IBMQ Status Logic ---
        ibmq_service = health_status["services"]["ibmq"]
        if not ibmq_service["details"]["api_key_set"]:
            ibmq_service["status"] = "API_KEY_MISSING"
            ibmq_service["message"] = "IBMQ_API_KEY is not set in the environment."
            # This is a warning, not an error, as core coffee functionality doesn't depend on it.
            if health_status["overall_status"] == "OK": health_status["overall_status"] = "WARNING"
        else:
            ibmq_service["status"] = "API_KEY_SET"
            ibmq_service["message"] = "IBMQ_API_KEY is configured."
            # A deeper check (e.g., trying to list providers) could be added but is slow.

        # --- Local Storage Logic ---
        ls_service = health_status["services"]["local_storage"]
        if not ls_service["details"]["user_dir_writable"]:
            ls_service["status"] = "WRITE_ERROR"
            ls_service["message"] = "The '.user/' directory is not writable. Cannot save tokens/cache."
            health_status["overall_status"] = "ERROR"
        elif not ls_service["details"]["config_file_exists"]:
            ls_service["status"] = "OK" # It's okay if it doesn't exist yet (first run)
            ls_service["message"] = "Config file '.user/oauth-token.json' not found (normal for first run or if no auth yet)."
        else:
            ls_service["status"] = "OK"
            ls_service["message"] = "Local storage directory is writable and config file exists (if previously authenticated)."

        # --- Final Overall Status Check ---
        if health_status["queues"]["failed_commands"] > 0:
            if health_status["overall_status"] == "OK": health_status["overall_status"] = "WARNING"
            hc_service["message"] += f" {health_status['queues']['failed_commands']} command(s) in failed queue."


        self.set_header("Content-Type", "application/json")
        self.finish(json.dumps(health_status, indent=2))


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

        identifier_to_set = None
        if body:
            if "haId" in body and body["haId"]:
                identifier_to_set = body["haId"]
                print(f"Attempting to set machine by haId: {identifier_to_set}")
            elif "enumber" in body and body["enumber"]:
                identifier_to_set = body["enumber"]
                print(f"Attempting to set machine by enumber: {identifier_to_set}")
            else: # Body exists but no known identifier
                 print("No haId or enumber provided in body, attempting to set to first available machine.")
        else: # No body
            print("No request body, attempting to set to first available machine.")

        try:
            connector.set_machine(identifier_to_set) # set_machine handles None identifier correctly
            self.finish(connector.machine)
        except RuntimeError as e:
            self.set_status(400) # Or 404 if machine not found based on identifier
            self.finish({"error": str(e)})
        except Exception as e:
            self.set_status(500)
            self.finish({"error": f"An unexpected error occurred while setting machine: {str(e)}"})

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
