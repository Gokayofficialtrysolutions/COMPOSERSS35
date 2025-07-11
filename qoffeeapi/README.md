# CHIMera Explorer API (`qoffeeapi` package)

**Note:** This documentation is being updated. With the project's pivot to the "CHIMera Explorer" (an offline Quantum Combinatorics tool), many of the Home Connect related API endpoints described below are now considered legacy. The primary active endpoint for CHIMera Explorer is `/api/health`. The `qoffeeapi` directory and package name are preserved due to tool limitations during renaming.

This Python package extends the Jupyter Notebook API to provide backend functionalities for the CHIMera Explorer application. The primary active endpoint is `/api/health`. Legacy Home Connect related endpoints are preserved but not central to the current project focus.

For overall project setup, architecture, and manual UI configuration in `chimera.ipynb`, please refer to the main project [README.md](../README.md) and the [DEVELOPER_GUIDE.md](../DEVELOPER_GUIDE.md).

## Installation

Install the `qoffeeapi` package (directory and package name preserved) using:
```
pip install ./qoffeeapi --user
```

## Usage (CHIMera Explorer Focus)

The primary active endpoint for CHIMera Explorer is:
*   `GET /api/health`: Provides a health check of the CHIMera Explorer system, including status of IBMQ configuration and local Qiskit Aer availability.

### Legacy Home Connect API Endpoints (Preserved)

The package also exposes the following legacy Home Connect related endpoints. All endpoints prefixed with 🔑 require Home Connect authentication. For a sample implementation on how to call these endpoints, see [qoffeefrontend/app.js](../qoffeefrontend/app.js).

#### Authentication

- `GET /auth` : redirect user to login page of HomeConnect OAuth Service
- `GET /auth/callback` : used by HomeConnect OAuth Service on successful login. Should not be called by user
- `GET /auth/refresh` : refresh the current access token using the stored refresh token. Access tokens must be refreshed every 24h.

For easier development, OAuth tokens, selected machine details, API response caches, and offline command queues are stored in a JSON file at `.user/oauth-token.json`. This file is loaded at startup if it exists and is updated by the application.

**Note on Offline Capabilities:** Many of the endpoints below now feature offline support. GET requests may return cached data if the application is offline, and POST requests for actions (like power on, order drink) will be queued if offline and processed when connectivity is restored. API responses are structured to indicate if data is live/cached or if a command was queued. Refer to the main project README for more details on offline behavior.

### Machine Details

- `🔑 GET /machine` : Returns `haId` and `enumber` of the currently selected coffee machine.
- `🔑 POST /machine` : Sets the current coffee machine using its `haId` (preferred) or `enumber`. If no identifier is provided in the request body (e.g., `{"haId": "..."}`), it attempts to use the first coffee machine associated with the account.
- `🔑 GET /machines` : Gets a list of coffee machines associated with the current account. Returns `{"machines": [...], "source": "live|cached|...", "last_updated": timestamp}`.
- `🔑 GET /machine/state` : Gets the operation state (e.g., `BSH.Common.Status.OperationState`) of the current coffee machine. Response includes data source and timestamp.
- `🔑 GET /machine/power` : Gets the power state (e.g., `BSH.Common.Setting.PowerState`) of the current coffee machine. Response includes data source and timestamp.
- `🔑 POST /machine/power` : Sets the power state of the current coffee machine to `On`. Returns status of the operation (live or queued).

### Drink

- `🔑 POST /drink` : Orders a drink from the current coffee machine (i.e., activates a program with options). Returns status of the operation (live or queued).
  Example request body: `{"key": "<program_identifier>", "options": {"<option_identifier>": <value>, ... }}`.
  Available programs and options can be found in [./options.md](options.md) or dynamically from the machine.

### Offline Queue Management (New)

These endpoints help manage the offline command queue for Home Connect operations:

- `🔑 GET /api/hc/queue-status`: Returns a summary of the active command queue and the failed command queue.
  Example response: `{"active_queue_length": 1, "failed_queue_length": 0, "failed_commands_summary": []}`
- `🔑 POST /api/hc/retry-failed-command`: Moves a command from the failed queue back to the active queue for another attempt.
  Example request body: `{"command_index": 0}` (where 0 is the index from the `failed_commands_summary` list).
- `🔑 POST /api/hc/delete-failed-command`: Removes a command from the failed queue.
  Example request body: `{"command_index": 0}`

### System Health (Primary endpoint for CHIMera Explorer)

- `GET /api/health`: Provides a health check of the CHIMera Explorer system, including status of IBMQ configuration and local Qiskit Aer availability. This endpoint does not require authentication.
  Example response snippet (for CHIMera Explorer):
  ```json
  {
    "overall_status": "OK",
    "services": {
      "home_connect_api": {"status": "AUTHENTICATED", ...},
      "ibmq": {"status": "API_KEY_SET", ...},
      "local_storage": {"status": "OK", ...}
    },
    "queues": {"active_commands": 0, "failed_commands": 0, ...}
  }
  ```