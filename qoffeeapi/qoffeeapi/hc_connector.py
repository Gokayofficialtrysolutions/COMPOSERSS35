import os
from qoffeeapi.oauth2 import PersistentOAuth2Connector
from urllib.parse import urljoin
import time # Moved import time to the top

class HomeconnectConnector(PersistentOAuth2Connector):

    machine = {
        "haId": None,
        "enumber": None
    }
    # Cache and queue attributes
    cached_appliances = None # Stores {"data": [<appliance_dict>], "last_updated": timestamp}
    cached_statuses = {}     # Dict mapping "haId_statusKey" to {"data": {<status_body>}, "last_updated": timestamp, "status": "live/pending_sync/etc."}
    cached_settings = {}     # Dict mapping "haId_settingKey" to {"data": {<setting_body>}, "last_updated": timestamp, "status": "live/pending_sync/etc."}
    command_queue = []       # List of command dicts to execute. Each dict includes:
                             # {"type": str, "endpoint": str, "payload": dict, "ha_id": str,
                             #  "timestamp": float, "retry_count": int (optional)}
                             # Specific command types (set_setting, program_drink) may have additional keys like "setting_key".
    failed_commands_queue = [] # List of command dicts that reached MAX_RETRIES. Includes original command + error info.


    CACHE_TTL = 300 # Time-to-live for cache in seconds (e.g., 5 minutes)
    MAX_RETRIES = 3 # Max retry attempts for a queued command before moving to failed_commands_queue

    def __init__(self, *args, **kwargs):
        self.cached_appliances = None
        self.cached_statuses = {}
        self.cached_settings = {}
        self.command_queue = []
        self.failed_commands_queue = [] # Initialize new queue
        self.MAX_RETRIES = 3 # Define max retries
        super().__init__(*args, **kwargs)
        # The _load_config_from_file in parent's __init__ calls our overridden load_config,
        # which now loads all HC specific data including cache and queue.
        # No need for _load_hc_specific_config_data or _initial_load_done_hc anymore.

    def get_machines(self):
        """
        Fetch all machines associated to the current account from homeconnect.
        Uses cache if offline or within CACHE_TTL.
        """
        current_time = time.time()
        if self.cached_appliances and \
           (not self.is_online or (current_time - self.cached_appliances.get("last_updated", 0)) < self.CACHE_TTL):
            print("Returning cached appliances")
            return self.cached_appliances["data"], "cached", self.cached_appliances.get("last_updated")

        if not self.check_online_status(): # Ensure is_online is fresh
             if self.cached_appliances:
                print("Offline: Returning cached appliances")
                return self.cached_appliances["data"], "cached_offline", self.cached_appliances.get("last_updated")
             else:
                print("Offline: No cached appliances available.")
                return [], "offline_no_cache", None # Or raise error

        status_code, response_body = super().get("/api/homeappliances")

        if status_code >= 300:
            # If network error led to 503 (offline) but we thought we were online,
            # trust the result of get() and re-check online status.
            if status_code == 503 and response_body.get('error') == 'offline':
                self.is_online = False # Update our state
                print("Became offline during get_machines. Attempting to return cache.")
                if self.cached_appliances:
                    return self.cached_appliances["data"], "cached_became_offline", self.cached_appliances.get("last_updated")
                else:
                    raise RuntimeError(f"Could not fetch machines and no cache available: {status_code} {response_body}")
            raise RuntimeError(f"Could not fetch machines: {status_code} {response_body}")

        machines = response_body.get("data", {}).get("homeappliances", [])
        self.cached_appliances = {"data": machines, "last_updated": time.time()}
        self.save_config() # Save updated cache
        return machines, "live", self.cached_appliances.get("last_updated")


    def set_machine(self, haId=None):
        """
        Set the current machine by HA ID or - if HA ID is not given - just use the first one in the account
        """
        machines, source, _ = self.get_machines()
        if not machines and source != "live": # If no machines and it wasn't a live successful call
             raise RuntimeError(f"Cannot set machine: No appliances found (source: {source}). Check connection or cache.")

        try:
            machine_data = next(
                filter(
                    lambda x: (
                        (haId is None) and (x.get("type") == "CoffeeMaker")) or
                        (haId is not None and x.get("haId", "").startswith(haId)),
                    machines
                )
            )
            self.machine = {
                "haId": machine_data["haId"],
                "enumber": machine_data["enumber"]
            }
            self.save_config()
        except StopIteration:
            raise RuntimeError(f"No matching CoffeeMaker found with haId starting with '{haId if haId else 'any'}' from source '{source}'.")


    def save_config(self):
        # Overwrite super function to also save cache and queue
        config_data = {
            "auth": self.tokens,
            "machine": self.machine,
            "cached_appliances": self.cached_appliances,
            "cached_statuses": self.cached_statuses,
            "cached_settings": self.cached_settings,
            "command_queue": self.command_queue,
            "failed_commands_queue": self.failed_commands_queue, # Add to save
        }
        return self._save_config_to_file(config_data)


    def load_config(self, config):
        # Called by _load_config_from_file in PersistentOAuth2Connector
        # Load auth tokens via super
        super().load_config(config) # This handles 'auth'

        # Load HC specific data
        if "machine" in config:
            self.machine = config["machine"]

        self.cached_appliances = config.get("cached_appliances")
        # Ensure nested structure for cached_statuses and cached_settings
        self.cached_statuses = {k: v for k, v in config.get("cached_statuses", {}).items() if isinstance(v, dict)}
        self.cached_settings = {k: v for k, v in config.get("cached_settings", {}).items() if isinstance(v, dict)}
        self.command_queue = config.get("command_queue", [])
        self.failed_commands_queue = config.get("failed_commands_queue", []) # Add to load

        # Ensure basic structure if loaded data is None from an old config file
        if self.cached_appliances is None: self.cached_appliances = None
        if self.command_queue is None: self.command_queue = []
        if self.failed_commands_queue is None: self.failed_commands_queue = []


    def get_ha_status(self, ha_id, status_key):
        """
        Get a specific status for a Home Appliance (haId).
        Uses cache if offline or within CACHE_TTL.
        status_key is like "BSH.Common.Status.OperationState".
        Returns (data, source_type, last_updated_timestamp)
        """
        endpoint = f"/api/homeappliances/{ha_id}/status/{status_key}"
        cache_key = f"{ha_id}_{status_key}"
        current_time = time.time()

        if self.cached_statuses.get(cache_key) and \
           (not self.is_online or \
            (current_time - self.cached_statuses[cache_key].get("last_updated", 0)) < self.CACHE_TTL):
            print(f"Returning cached status for {cache_key}")
            cached_item = self.cached_statuses[cache_key]
            return cached_item["data"], "cached", cached_item.get("last_updated")

        if not self.check_online_status():
            if self.cached_statuses.get(cache_key):
                print(f"Offline: Returning cached status for {cache_key}")
                cached_item = self.cached_statuses[cache_key]
                return cached_item["data"], "cached_offline", cached_item.get("last_updated")
            else:
                print(f"Offline: No cached status for {cache_key}")
                return {"error": "offline_no_cache", "message": f"No cached status for {cache_key} and currently offline."}, "offline_no_cache", None

        status_code, response_body = super().get(endpoint)

        if status_code >= 300:
            if status_code == 503 and response_body.get('error') == 'offline':
                self.is_online = False
                print(f"Became offline during get_ha_status for {cache_key}. Attempting to return cache.")
                if self.cached_statuses.get(cache_key):
                    cached_item = self.cached_statuses[cache_key]
                    return cached_item["data"], "cached_became_offline", cached_item.get("last_updated")
            # For other errors (e.g., 404 if status_key is wrong), don't assume offline, just raise
            raise RuntimeError(f"Could not fetch status {cache_key}: {status_code} {response_body}")

        # Successfully fetched live data
        self.cached_statuses[cache_key] = {"data": response_body, "last_updated": time.time()}
        self.save_config()
        return response_body, "live", self.cached_statuses[cache_key].get("last_updated")

    def get_ha_setting(self, ha_id, setting_key):
        """
        Get a specific setting for a Home Appliance (haId).
        Uses cache if offline or within CACHE_TTL.
        setting_key is like "BSH.Common.Setting.PowerState".
        Returns (data, source_type, last_updated_timestamp)
        """
        endpoint = f"/api/homeappliances/{ha_id}/settings/{setting_key}"
        cache_key = f"{ha_id}_{setting_key}" # Use a distinct prefix or dict for settings vs status if keys overlap
        current_time = time.time()

        if self.cached_settings.get(cache_key) and \
           (not self.is_online or \
            (current_time - self.cached_settings[cache_key].get("last_updated", 0)) < self.CACHE_TTL):
            print(f"Returning cached setting for {cache_key}")
            cached_item = self.cached_settings[cache_key]
            return cached_item["data"], "cached", cached_item.get("last_updated")

        if not self.check_online_status():
            if self.cached_settings.get(cache_key):
                print(f"Offline: Returning cached setting for {cache_key}")
                cached_item = self.cached_settings[cache_key]
                return cached_item["data"], "cached_offline", cached_item.get("last_updated")
            else:
                print(f"Offline: No cached setting for {cache_key}")
                return {"error": "offline_no_cache", "message": f"No cached setting for {cache_key} and currently offline."}, "offline_no_cache", None

        status_code, response_body = super().get(endpoint)

        if status_code >= 300:
            if status_code == 503 and response_body.get('error') == 'offline':
                self.is_online = False
                print(f"Became offline during get_ha_setting for {cache_key}. Attempting to return cache.")
                if self.cached_settings.get(cache_key):
                    cached_item = self.cached_settings[cache_key]
                    return cached_item["data"], "cached_became_offline", cached_item.get("last_updated")
            raise RuntimeError(f"Could not fetch setting {cache_key}: {status_code} {response_body}")

        self.cached_settings[cache_key] = {"data": response_body, "last_updated": time.time()}
        self.save_config()
        return response_body, "live", self.cached_settings[cache_key].get("last_updated")

    def set_ha_setting(self, ha_id, setting_key, setting_value_payload):
        """
        Set a specific setting for a Home Appliance (haId).
        Queues command if offline.
        setting_value_payload is the full JSON body for the PUT request, e.g. {"data": {"key": "...", "value": "..."}}
        Returns (status_code, response_body_or_message)
        """
        endpoint = f"/api/homeappliances/{ha_id}/settings/{setting_key}"

        if not self.check_online_status():
            command = {
                "type": "set_setting",
                "endpoint": endpoint,
                "payload": setting_value_payload,
                "ha_id": ha_id, # Store for potential later use in queue processing logic
                "setting_key": setting_key, # Store for potential later use
                "timestamp": time.time()
            }
            self.command_queue.append(command)
            self.save_config()
            print(f"Offline: Queued set_setting command for {endpoint}")
            # Update local cache optimistically for immediate feedback
            # This assumes the key in setting_value_payload.data.value is what we'd get from a GET
            # This might need adjustment based on actual GET response structure vs PUT payload
            optimistic_cache_data = {"data": {"key": setting_key, "value": setting_value_payload.get("data",{}).get("value")}}
            self.cached_settings[f"{ha_id}_{setting_key}"] = {"data": optimistic_cache_data, "last_updated": time.time(), "status": "pending_sync"}
            self.save_config() # Save optimistic cache update
            return 202, {"message": "Command queued successfully. Local cache updated optimistically.", "status": "queued", "details": command} # 202 Accepted

        status_code, response_body = super().put(endpoint, setting_value_payload)

        if status_code >= 300:
            if status_code == 503 and response_body.get('error') == 'offline':
                self.is_online = False # Update status
                # Automatically queue if we thought we were online but failed due to network
                command = {
                    "type": "set_setting",
                    "endpoint": endpoint,
                    "payload": setting_value_payload,
                    "ha_id": ha_id,
                    "setting_key": setting_key,
                    "timestamp": time.time(),
                    "retry_original_error": response_body
                }
                self.command_queue.append(command)
                self.save_config()
                print(f"Became offline during set_ha_setting for {endpoint}. Command queued.")
                # Optimistic cache update
                optimistic_cache_data = {"data": {"key": setting_key, "value": setting_value_payload.get("data",{}).get("value")}}
                self.cached_settings[f"{ha_id}_{setting_key}"] = {"data": optimistic_cache_data, "last_updated": time.time(), "status": "pending_sync"}
                self.save_config()
                return 202, {"message": "Command queued after failed attempt (became offline).", "status": "queued_after_fail", "details": command}
            # For other errors, just return them
            return status_code, response_body

        # Successful PUT: Update cache with live data if possible (API might not return new state directly)
        # For settings, it's often better to re-fetch or trust the set value if API returns 204 No Content
        # For now, let's assume 204 means success and update cache optimistically if no body
        if status_code == 204 or (status_code < 300 and not response_body): # Common for successful PUTs
             # Optimistically update cache based on what was sent
            self.cached_settings[f"{ha_id}_{setting_key}"] = {
                "data": {"data": {"key": setting_key, "value": setting_value_payload.get("data",{}).get("value")}}, # Structure might need to match GET
                "last_updated": time.time(),
                "status": "live_optimistic" # Indicates it was set live, but value is from payload not GET
            }
        elif status_code < 300 and response_body: # If body is returned, use it
            self.cached_settings[f"{ha_id}_{setting_key}"] = {"data": response_body, "last_updated": time.time(), "status": "live_confirmed"}

        self.save_config()
        return status_code, response_body

    def program_drink(self, ha_id, program_payload):
        """
        Start a program (e.g., make a drink) on a Home Appliance.
        Queues command if offline.
        program_payload is the JSON body for the PUT request, e.g. {"data": {"key": "...", "options": [...]}}
        Returns (status_code, response_body_or_message)
        """
        endpoint = f"/api/homeappliances/{ha_id}/programs/active"

        if not self.check_online_status():
            command = {
                "type": "program_drink",
                "endpoint": endpoint,
                "payload": program_payload,
                "ha_id": ha_id,
                "program_key": program_payload.get("data", {}).get("key"),
                "timestamp": time.time()
            }
            self.command_queue.append(command)
            self.save_config()
            print(f"Offline: Queued program_drink command for {endpoint}")
            # Potentially update OperationState cache optimistically to 'Busy' or 'Running'
            # This is more complex as the actual state change is asynchronous.
            # For now, just queue and don't do optimistic cache for OperationState.
            return 202, {"message": "Command queued successfully.", "status": "queued", "details": command}

        status_code, response_body = super().put(endpoint, program_payload)

        if status_code >= 300:
            if status_code == 503 and response_body.get('error') == 'offline':
                self.is_online = False # Update status
                command = {
                    "type": "program_drink",
                    "endpoint": endpoint,
                    "payload": program_payload,
                    "ha_id": ha_id,
                    "program_key": program_payload.get("data", {}).get("key"),
                    "timestamp": time.time(),
                    "retry_original_error": response_body
                }
                self.command_queue.append(command)
                self.save_config()
                print(f"Became offline during program_drink for {endpoint}. Command queued.")
                return 202, {"message": "Command queued after failed attempt (became offline).", "status": "queued_after_fail", "details": command}
            return status_code, response_body

        # Successful PUT. OperationState usually changes, might be good to clear its cache or re-fetch.
        # For now, a simple approach: clear the OperationState cache for this haId to force re-fetch on next status request.
        # More advanced: parse response headers for a location to poll status.
        operation_state_cache_key = f"{ha_id}_BSH.Common.Status.OperationState"
        if operation_state_cache_key in self.cached_statuses:
            del self.cached_statuses[operation_state_cache_key]
            print(f"Cleared cached OperationState for {ha_id} after program_drink.")
            self.save_config()

        return status_code, response_body

    def process_command_queue(self):
        """
        Process any commands in the command_queue if online.
        Iterates through queued commands, attempts to execute them,
        handles retries for failures, and moves commands to failed_commands_queue
        if they exceed MAX_RETRIES. Updates local caches for successfully
        processed settings commands.
        """
        if not self.check_online_status() or not self.command_queue:
            if not self.is_online and self.command_queue: # Specifically log if queue has items but we are offline
                print("Offline, cannot process command queue at this time.")
            return {"processed_count": 0, "remaining_count": len(self.command_queue), "status": "offline_or_empty"}

        print(f"Processing command queue. {len(self.command_queue)} commands pending.")
        processed_count = 0

        # Take a snapshot of the current command_queue to iterate over.
        # The main self.command_queue is cleared and will be repopulated only with
        # commands that need to be retried or were not processed if connection drops mid-way.
        pending_commands = list(self.command_queue)
        self.command_queue = []

        successful_commands_info = []

        for command_index, command in enumerate(pending_commands):
            # Ensure command has a retry_count, default to 0 if not present (for older queued items)
            command['retry_count'] = command.get('retry_count', 0)

            print(f"Attempting command: {command.get('type')} to {command.get('endpoint')} (Attempt {command['retry_count'] + 1})")

            # Ensure we have fresh online status before each command attempt
            if not self.check_online_status():
                print("Became offline while processing queue. Stopping further processing.")
                # Add this command and any subsequent commands back to the main queue
                self.command_queue.extend(pending_commands[command_index:])
                break

            status_code, response_body = -1, {}
            if command.get("type") == "set_setting" or command.get("type") == "program_drink":
                status_code, response_body = super().put(command["endpoint"], command["payload"])
            else:
                error_msg = f"Unknown command type in queue: {command.get('type')}. Moving to failed queue."
                print(f"ERROR: {error_msg}")
                command["error_reason"] = error_msg
                command["last_failure_timestamp"] = time.time()
                self.failed_commands_queue.append(command)
                # Do not add to new_queue, effectively removing it from active processing
                continue

            if status_code < 300:
                print(f"Command {command.get('type')} to {command.get('endpoint')} successful.")
                processed_count += 1
                successful_commands_info.append({"type": command.get('type'), "endpoint": command.get('endpoint'), "response_status": status_code})
                # If it was a setting, update its cache from live response if possible, or clear to force re-fetch
                if command.get("type") == "set_setting":
                    setting_key = command.get("setting_key")
                    ha_id = command.get("ha_id")
                    cache_key_setting = f"{ha_id}_{setting_key}"
                    if status_code == 204 or not response_body : # No content, use payload for optimistic cache
                         self.cached_settings[cache_key_setting] = {
                            "data": {"data": {"key": setting_key, "value": command["payload"].get("data",{}).get("value")}},
                            "last_updated": time.time(), "status": "live_optimistic_after_queue"
                        }
                    elif response_body: # Has response body
                        self.cached_settings[cache_key_setting] = {"data": response_body, "last_updated": time.time(), "status": "live_confirmed_after_queue"}
                    print(f"Updated cache for {cache_key_setting} after queued command success.")
                elif command.get("type") == "program_drink":
                    ha_id = command.get("ha_id")
                    operation_state_cache_key = f"{ha_id}_BSH.Common.Status.OperationState"
                    if operation_state_cache_key in self.cached_statuses:
                        del self.cached_statuses[operation_state_cache_key]
                        print(f"Cleared cached OperationState for {ha_id} after queued program_drink.")

            elif status_code == 503 and response_body.get('error') == 'offline':
                print("Became offline again while processing a command. Stopping queue processing.")
                self.is_online = False
                new_queue.extend(pending_commands[command_index:]) # Add this and remaining commands back
                break
            else:
                print(f"Command {command.get('type')} to {command.get('endpoint')} failed with {status_code}: {response_body}. Keeping in queue for now.")
                # Implement retry logic or move to a 'failed_permanently' queue later if needed.
                # For now, keep it and it will be retried next time.
                command["retry_count"] = command.get("retry_count", 0) + 1
                command["last_failure_timestamp"] = time.time()
                command["last_failure_status"] = status_code
                command["last_failure_response"] = response_body

                if command["retry_count"] >= self.MAX_RETRIES:
                    print(f"Command {command.get('type')} to {command.get('endpoint')} reached max retries. Moving to failed queue.")
                    self.failed_commands_queue.append(command)
                else:
                    print(f"Command {command.get('type')} to {command.get('endpoint')} failed (attempt {command['retry_count']}/{self.MAX_RETRIES}). Keeping in queue.")
                    new_queue.append(command) # Keep in active queue for next retry

        self.command_queue = new_queue
        self.save_config() # This now saves command_queue and failed_commands_queue

        summary = {
            "processed_count": processed_count,
            "remaining_count": len(self.command_queue),
            "status": "processed_queue",
            "successful_commands": successful_commands_info,
            "still_online": self.is_online
        }
        print(f"Queue processing finished: {summary}")
        return summary

    def get_queue_summary(self):
        """
        Returns a summary of the command queues.
        """
        # Create a serializable summary of failed commands (e.g., omitting full payload)
        failed_summary = []
        for idx, cmd in enumerate(self.failed_commands_queue):
            failed_summary.append({
                "id": idx, # Simple index-based ID for now
                "type": cmd.get("type"),
                "endpoint": cmd.get("endpoint"),
                "program_key": cmd.get("program_key"), # Specific to program_drink
                "setting_key": cmd.get("setting_key"), # Specific to set_setting
                "timestamp": cmd.get("timestamp"),
                "retry_count": cmd.get("retry_count"),
                "last_failure_timestamp": cmd.get("last_failure_timestamp"),
                "last_failure_status": cmd.get("last_failure_status"),
                "error_reason": cmd.get("error_reason") # For unknown type or other processing errors
            })
        return {
            "active_queue_length": len(self.command_queue),
            "failed_queue_length": len(self.failed_commands_queue),
            "failed_commands_summary": failed_summary
        }

    def retry_failed_command(self, command_index: int):
        """
        Moves a command from the failed_commands_queue back to the active command_queue
        and resets its retry_count.
        Args:
            command_index: The index of the command in the failed_commands_queue.
        Returns:
            True if successful, False if index is invalid.
        """
        if 0 <= command_index < len(self.failed_commands_queue):
            command_to_retry = self.failed_commands_queue.pop(command_index)
            command_to_retry["retry_count"] = 0 # Reset retry count
            # Clear previous failure specific info if any, or keep for history
            command_to_retry.pop("last_failure_timestamp", None)
            command_to_retry.pop("last_failure_status", None)
            command_to_retry.pop("last_failure_response", None)
            command_to_retry.pop("error_reason", None)

            self.command_queue.append(command_to_retry)
            self.save_config()
            print(f"Command at failed_queue index {command_index} moved to active queue for retry.")
            # Optionally, trigger queue processing immediately if online
            # self.process_command_queue()
            return True
        else:
            print(f"Invalid command index for retry: {command_index}")
            return False

    def delete_failed_command(self, command_index: int):
        """
        Deletes a command from the failed_commands_queue.
        Args:
            command_index: The index of the command in the failed_commands_queue.
        Returns:
            True if successful, False if index is invalid.
        """
        if 0 <= command_index < len(self.failed_commands_queue):
            deleted_command = self.failed_commands_queue.pop(command_index)
            self.save_config()
            print(f"Command {deleted_command.get('type')} for endpoint {deleted_command.get('endpoint')} deleted from failed queue.")
            return True
        else:
            print(f"Invalid command index for delete: {command_index}")
            return False

    def reset_offline_data(self):
        """
        Resets cached data and command queues. Does NOT clear auth tokens or selected machine.
        """
        print("Resetting offline data: caches and command queues...")
        self.cached_appliances = None
        self.cached_statuses = {}
        self.cached_settings = {}
        self.command_queue = []
        self.failed_commands_queue = []
        self.save_config() # Persist the cleared state (keeps auth and machine)
        print("Offline data reset complete.")
        return {"message": "Offline data (caches and queues) reset successfully."}


# singleton
_HOMECONNECT_CONNECTOR = None

def get_connector():
    """
    Get the connector object initialized from environment variables
    """
    global _HOMECONNECT_CONNECTOR
    if _HOMECONNECT_CONNECTOR is not None:
        return _HOMECONNECT_CONNECTOR
    # create folder if not exists
    if not os.path.isdir(".user"):
        os.mkdir(".user")
    ### create a singleton from environment
    api_base_url = os.getenv("HOMECONNECT_API_URL")
    _HOMECONNECT_CONNECTOR = HomeconnectConnector(
        api_base_url=api_base_url,
        authorize_url=urljoin(api_base_url, "security/oauth/authorize"),
        token_url=urljoin(api_base_url, "security/oauth/token"),
        client_id=os.getenv("HOMECONNECT_CLIENT_ID"),
        client_secret=os.getenv("HOMECONNECT_CLIENT_SECRET"),
        callback_uri=os.getenv("HOMECONNECT_REDIRECT_URL"),
        scopes=["IdentifyAppliance", "CoffeeMaker"],
        path=".user/oauth-token.json"
    )
    # unset environment variables to hide them in notebooks
    os.environ["HOMECONNECT_CLIENT_ID"] = "<hidden>"
    os.environ["HOMECONNECT_CLIENT_SECRET"] = "<hidden>"

    # Attempt to process command queue on startup if online
    if _HOMECONNECT_CONNECTOR.is_online:
        print("Connector initialized, attempting to process command queue...")
        try:
            _HOMECONNECT_CONNECTOR.process_command_queue()
        except Exception as e:
            print(f"Error processing command queue on startup: {e}")

    return _HOMECONNECT_CONNECTOR
