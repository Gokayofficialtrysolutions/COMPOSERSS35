# Qoffeeapi

This Python package extends the Jupyter Notebook API to communicate with the HomeConnect API and provide other backend functionalities for the Qoffee-Maker application. The endpoints mentioned below are available on the base URL of the Jupyter Server.

For overall project setup, architecture, and manual UI configuration in `qoffee.ipynb`, please refer to the main project [README.md](../README.md) and the [DEVELOPER_GUIDE.md](../DEVELOPER_GUIDE.md).

## Installation

Install the qoffeeapi using
```
pip install ./qoffeeapi --user
```

## Usage

The package exposes the following endpoints in the Jupyter API. All endpoints prefixed with 🔑 require autentication. For a sample implementation on how to call these endpoints, see [qoffeefrontend/app.js : requestDrink](../qoffeefrontend/app.js). 

### Authentication

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

### System Health

- `GET /api/health`: Provides a health check of the QoffeeMaker system, including status of Home Connect API connectivity, IBMQ configuration, local storage, and command queue summaries. This endpoint does not require authentication.
  Example response snippet:
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