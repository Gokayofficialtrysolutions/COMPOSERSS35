# Qoffee-Maker Developer Guide

This guide provides technical details, an architectural overview, and guidance for developers working on or extending the Qoffee-Maker project.

## Table of Contents

1.  [Architectural Overview](#1-architectural-overview)
2.  [Backend API (`qoffeeapi`)](#2-backend-api-qoffeeapi)
    *   [Key Modules](#key-modules)
    *   [API Endpoints Summary](#api-endpoints-summary)
    *   [Offline Mechanism (`hc_connector.py`)](#offline-mechanism-hc_connectorpy)
3.  [Combinatorial Circuits (`combinatorial_circuits.py`)](#3-combinatorial-circuits-combinatorial_circuitspy)
4.  [Frontend JavaScript (`qoffeefrontend/app.js`)](#4-frontend-javascript-qoffeefrontendappjs)
5.  [CLI Tool (`qoffee_cli.py`)](#5-cli-tool-qoffee_clipy)
6.  [Manual UI Setup in `qoffee.ipynb`](#6-manual-ui-setup-in-qoffeeipynb)
7.  [Conceptual Designs for Future UI/UX](#7-conceptual-designs-for-future-uiux)
8.  [Security Considerations](#8-security-considerations)
9.  [Alternative Frontend Approaches (Long-Term)](#9-alternative-frontend-approaches-long-term)

---

## 1. Architectural Overview

The Qoffee-Maker project is primarily designed to run within a Jupyter Notebook environment, enhanced by custom Jupyter server extensions and frontend JavaScript.

*   **`qoffee.ipynb` (The Main Application UI - Requires Manual Setup):**
    *   This Jupyter Notebook serves as the primary user interface.
    *   It heavily utilizes `ipywidgets` and custom `appwidgets` (especially `ReactiveHtmlWidget`) to create interactive views.
    *   Python code within the notebook cells orchestrates the UI, manages application state (via a central `data` ipywidget), and interacts with the backend API and Qiskit.
    *   **Crucial Note:** Significant UI enhancements developed conceptually (for offline feedback, combinatorial circuit interaction, educational content) require **manual editing** of this notebook. Refer to [MANUAL_QOFFEE_IPYNB_SETUP.md](MANUAL_QOFFEE_IPYNB_SETUP.md).

*   **`qoffeeapi/` (Backend Python Package):**
    *   A Python package that extends the Jupyter server with custom API endpoints.
    *   Handles all communication with the Home Connect API for coffee machine control.
    *   Implements offline capabilities (caching, command queuing) for Home Connect.
    *   Provides API endpoints for queue status, failed command management, and system health.
    *   Contains the logic for generating combinatorial quantum circuits.

*   **`qoffeefrontend/` (Frontend JavaScript & CSS):**
    *   A Jupyter Notebook extension that bundles JavaScript (`app.js`) and CSS (`app.css`).
    *   `app.js` enhances the notebook experience by:
        *   Providing global JavaScript functions callable from Python (via `JsPyWidget`) for actions like drink requests, activating the machine, and opening QR code overlays.
        *   Managing a global status bar for basic network and queue status feedback.
        *   Handling CDN dependencies locally (lz-string, qrcode.js).

*   **`appwidgets/` (Custom Jupyter Widgets):**
    *   A Python package providing custom ipywidgets like `ReactiveHtmlWidget` (for dynamic HTML rendering based on Python data models) and `JsPyWidget` (for Python-JavaScript communication). These are fundamental to the UI structure in `qoffee.ipynb`.

*   **`qoffee_cli.py` (Command Line Interface):**
    *   A standalone Python script for interacting with some of the `qoffeeapi` backend endpoints from the command line (e.g., checking queue status, managing failed commands, listing machines, system health).

*   **Configuration (`.env` file):**
    *   API keys, client secrets, and other configurations are managed via an `.env` file (copied from `env-template`).

*   **Local Data Storage (`.user/oauth-token.json`):**
    *   Stores Home Connect OAuth tokens, the selected machine, API response caches, and command queues (active and failed).

## 2. Backend API (`qoffeeapi`)

The `qoffeeapi` package is the workhorse for backend operations.

### Key Modules (`qoffeeapi/qoffeeapi/`):

*   **`__init__.py`:** Registers all API endpoint handlers with the Jupyter server.
*   **`oauth2.py`:** Contains `OAuth2Connector` and `PersistentOAuth2Connector` for managing generic OAuth2 flows, including token refresh and persistence. Implements basic online/offline detection.
*   **`hc_connector.py`:** Subclasses `PersistentOAuth2Connector` to implement specific Home Connect API interactions. This is where all caching, command queuing, retry logic, and failed command management for Home Connect operations reside.
*   **`api_auth.py`:** Contains Tornado handlers for the Home Connect OAuth authentication flow (`/auth`, `/auth/callback`, `/auth/refresh`).
*   **`api_orchestrator.py`:** Contains Tornado handlers for most application-specific actions:
    *   Interacting with the coffee machine (status, power, drink).
    *   Managing machine selection.
    *   Managing Home Connect command queues (status, retry, delete).
    *   System health check.
*   **`combinatorial_circuits.py`:** (Discussed in a separate section below).
*   **`utils.py`:** General utility functions (currently minimal).

### API Endpoints Summary

(Refer to `qoffeeapi/README.md` for detailed request/response examples).

*   **Authentication:**
    *   `GET /auth`: Initiates Home Connect login.
    *   `GET /auth/callback`: Handles OAuth callback.
    *   `GET /auth/refresh`: Refreshes Home Connect token.
*   **Machine Details & Control:**
    *   `GET /machine`: Get current selected machine.
    *   `POST /machine`: Set current machine (by `haId` or `enumber`).
    *   `GET /machines`: List all available machines.
    *   `GET /machine/state`: Get current machine's operational state.
    *   `GET /machine/power`: Get current machine's power state.
    *   `POST /machine/power`: Turn current machine on.
    *   `POST /drink`: Order a drink from the current machine.
*   **Offline Queue Management:**
    *   `GET /api/hc/queue-status`: Get summary of active and failed command queues.
    *   `POST /api/hc/retry-failed-command`: Retry a command from the failed queue.
    *   `POST /api/hc/delete-failed-command`: Delete a command from the failed queue.
*   **System Health:**
    *   `GET /api/health`: Get a system health check report (publicly accessible).

### Offline Mechanism (`hc_connector.py`)

*   **Online/Offline Detection:** `OAuth2Connector.check_online_status()` pings the Home Connect API base URL. Status is cached for `ONLINE_CHECK_INTERVAL`.
*   **Caching:**
    *   GET requests for appliances, status, and settings are cached in memory within the `HomeconnectConnector` instance and persisted to `.user/oauth-token.json`.
    *   `CACHE_TTL` (default 5 mins) determines how long cached data is considered fresh when online. If offline, stale cache is served if available.
*   **Command Queuing:**
    *   `set_ha_setting` and `program_drink` methods queue commands if `is_online` is false or if an online request fails due to network issues.
    *   Queued commands (active and failed) are persisted in `.user/oauth-token.json`.
*   **Queue Processing:**
    *   `process_command_queue()` is called on connector initialization (if online) and can be triggered by other events (e.g., after a successful retry of a failed command).
    *   It attempts to send commands from `command_queue`.
    *   **Retries:** Commands that fail (non-offline errors) are retried up to `MAX_RETRIES` (default 3). Retry count is stored with the command.
    *   **Failed Queue:** Commands exceeding `MAX_RETRIES` are moved to `failed_commands_queue`.

## 3. Combinatorial Circuits (`combinatorial_circuits.py`)

Located in `qoffeeapi/qoffeeapi/combinatorial_circuits.py`.

*   **Purpose:** Provides Python functions to generate Qiskit `QuantumCircuit` objects representing various combinatorial concepts.
*   **Generators:**
    *   `generate_binomial_distribution_circuit(num_qubits, success_probability_p)`
    *   `generate_permutation_circuit_example(num_qubits, pattern)`: For simple, named permutations (e.g., SWAPs, bit-reversals for small N).
    *   `generate_combination_superposition_circuit(num_qubits_n, num_to_select_k)`: Uses `qc.initialize()` to prepare the target state.
    *   `generate_custom_permutation_circuit(num_qubits, permutation_list)`: Uses Qiskit's `Permutation` gate or `qc.unitary()`.
*   **Registry (`combinatorial_circ_reg`):**
    *   A list of dictionaries defining pre-configured examples that can be loaded into the UI. Each entry specifies an ID, name, description, generator function, and arguments.
*   **Extending:** To add new circuit types or examples:
    1.  Write a new generator function that returns a `QuantumCircuit`.
    2.  Add an entry to the `combinatorial_circ_reg` list.
    3.  (For UI) Update `MANUAL_QOFFEE_IPYNB_SETUP.md` with instructions on how to add a card for it in `qoffee.ipynb`'s welcome view and how to update `load_combinatorial_circuit` to provide educational content for it.

## 4. Frontend JavaScript (`qoffeefrontend/app.js`)

This file is loaded as a Jupyter Notebook extension.

*   **Key Responsibilities:**
    *   Manages "App Mode" (hiding notebook code cells).
    *   Provides global JavaScript functions callable from Python via `JsPyWidget` for:
        *   Home Connect actions: `window.activateCoffeeMachine()`, `window.requestDrink()`, `window.refreshAuth()`. These now handle 202 (Queued) responses from the backend and show alerts/status bar messages.
        *   QR Code display: `window.openQRCode()`, `window.openQRCodeIBMQ()`. These use locally bundled `qrcode.min.js` and `lz-string.min.js`.
        *   Help display: `window.openHelp()`.
    *   Implements a global status bar (`#qoffee-global-status-bar`):
        *   Displays basic browser online/offline status.
        *   Polls `/api/hc/queue-status` periodically to show counts of active/failed Home Connect commands.
        *   Shows temporary messages for queued actions or errors.
*   **XSRF Token:** For `fetch` requests to backend API endpoints, it attempts to read the `_xsrf` token from cookies.

## 5. CLI Tool (`qoffee_cli.py`)

*   A Python script providing command-line access to certain backend features.
*   Uses `requests` to call the `qoffeeapi` endpoints.
*   **Commands:**
    *   `status`: View Home Connect queue status.
    *   `retry <index>`: Retry a failed Home Connect command.
    *   `delete <index>`: Delete a failed Home Connect command.
    *   `list-machines`: List connected Home Connect coffee machines.
    *   `health`: Get system health check.
*   **Configuration:** Uses `--base-url` argument or `QOFFEE_BASE_URL` environment variable.
*   **XSRF Handling:** Currently requires manual creation of `.qoffee_cli_xsrf_token` file for POST commands (retry, delete) or use of `--ignore-xsrf`.

## 6. Manual UI Setup in `qoffee.ipynb`

This is a critical part for enabling the full user experience of recently developed features.
**Refer to [MANUAL_QOFFEE_IPYNB_SETUP.md](MANUAL_QOFFEE_IPYNB_SETUP.md) for complete, step-by-step instructions.**

This guide covers:
*   Adding new Python imports.
*   Adding new traits to the global `data` ipywidget for status messages, combinatorial parameters, etc.
*   Adding new Python helper functions to `qoffee.ipynb` for:
    *   Fetching and displaying API status (`update_hc_queue_status_from_api`, `update_system_health_from_api`).
    *   Loading pre-defined combinatorial circuits (`load_combinatorial_circuit`).
    *   Generating and loading custom/parameterized combinatorial circuits (`generate_and_load_custom_combinatorial_circuit`).
    *   Populating educational content (`data.circuit_info_html`).
*   Updating HTML templates of `ReactiveHtmlWidget`s for:
    *   The main header (to show network status, queue length).
    *   The welcome view (to add cards for combinatorial circuit examples and the custom generation view).
    *   The composer view (to show IBMQ fallback messages and educational content).
*   Creating a new "Parameter Input View" for combinatorial circuits using `ipywidgets`.
*   Creating a new "Admin/Debug View" (conceptualized, for displaying health/queue status and managing queues).

## 7. Conceptual Designs for Future UI/UX

During development, several UI/UX concepts were designed to enhance the application further, especially the educational aspects. These are documented in agent messages from "Phase 7" and include:

*   **Detailed User Stories:** For offline features, combinatorial circuits, and IBMQ integration.
*   **Advanced Interactive Exercises:** Ideas for making the combinatorial circuits more engaging (e.g., comparing empirical vs. theoretical probabilities for Binomial, verifying permutations on specific input states).
*   **Admin/Debug View Outline:** A more detailed breakdown of what this view in `qoffee.ipynb` could contain.

These designs serve as a starting point for anyone manually implementing or extending the UI in `qoffee.ipynb`.

## 8. Security Considerations

Refer to the "Security Considerations" section in the main [README.md](README.md). Key points include protecting `.env` and `.user/oauth-token.json`, understanding the implications of `verify=False` in API calls, and Jupyter server security.

## 9. Alternative Frontend Approaches (Long-Term)

If the Jupyter Notebook/ipywidget approach becomes too limiting for future UI/UX ambitions, alternative frontend architectures were briefly considered:

*   **Dedicated Web Application:** (e.g., Flask/Django backend + React/Vue frontend). Offers maximum flexibility but requires a full rewrite.
*   **Voila Dashboards:** Simpler to convert from a notebook for an app-like feel, but may share some ipywidget limitations.
*   **Panel/Streamlit:** Python-based app frameworks, good for data-heavy apps, but would require migration from ipywidgets.

This guide should provide a solid technical foundation for understanding and further developing the Qoffee-Maker project.

---

## 10. Troubleshooting Common Issues

Here are some common issues you might encounter and how to address them:

*   **Python Import Errors (e.g., `ModuleNotFoundError: No module named 'qoffeeapi'` or `qiskit`):**
    *   Ensure you have installed all dependencies from `requirements.txt`: `pip install -r requirements.txt`
    *   If you've added local packages like `qoffeeapi` or `appwidgets` and are running the notebook from the project root, ensure they were installed correctly (e.g., `pip install -e .` for editable installs if developing them, or `pip install ./qoffeeapi --user` as per READMEs).
    *   Make sure your Jupyter kernel is using the Python environment where these packages were installed. Restart the kernel after installation.

*   **Home Connect Authentication Failures (`/auth` issues, token errors):**
    *   Double-check your `.env` file for correct `HOMECONNECT_CLIENT_ID`, `HOMECONNECT_CLIENT_SECRET`, `HOMECONNECT_API_URL`, and especially `HOMECONNECT_REDIRECT_URL`. The redirect URL must exactly match what you configured in your Home Connect Developer Portal application.
    *   Ensure the Home Connect Developer account and application are correctly set up as per the main `README.md`.
    *   If tokens seem stale, try `qoffee_cli.py status` and then `window.refreshAuth()` in the notebook's browser console, or click the "Refresh Auth" button if available in the UI.
    *   The `.user/oauth-token.json` file can be deleted to force a fresh authentication flow if tokens are corrupted.

*   **`qoffee.ipynb` UI Not Updating / `data` Widget Traits Not Syncing:**
    *   This is a common challenge with `ipywidgets`.
    *   **Restart Kernel:** Often the first thing to try.
    *   **Run All Cells:** Ensure all cells, especially those defining the `data` widget, helper functions, and UI components, have been executed in the correct order.
    *   **Check Browser Console:** Look for JavaScript errors that might be preventing widget communication.
    *   **`JsPyWidget` Issues:** If Python-to-JS calls (`jspy.execute_js`) or JS-to-Python (less common directly) are failing, check the `JsPyWidget` setup and the JavaScript functions in `qoffeefrontend/app.js`.
    *   **`ReactiveHtmlWidget` Not Updating:** Ensure the `data_model` is correctly passed and the traits referenced in HTML (`${trait_name}`) exist on the `data` model and are being updated by Python code.

*   **Offline Mode Not Behaving as Expected:**
    *   **Check API Logs:** The `print` statements in `hc_connector.py` provide information about cache usage, queueing, and online status checks. View the Jupyter server console output.
    *   **Inspect `.user/oauth-token.json`:** Manually check this file to see if commands are being added to `command_queue` or `failed_commands_queue`, and if cache fields are present.
    *   **Test `is_online`:** The `hc_connector.check_online_status()` method relies on network requests. If your network simulation for "offline" isn't actually blocking these, the app might think it's online.
    *   **Global Status Bar (JS):** The JS status bar uses `navigator.onLine` for its "Network: Online/Offline" message, which might differ from the backend's `hc_connector.is_online` (which checks actual API reachability). The queue counts in the bar come from the API, so they are more reliable indicators of backend state.

*   **Combinatorial Circuits Not Loading/Generating:**
    *   Ensure all manual setup steps in `MANUAL_QOFFEE_IPYNB_SETUP.md` for these circuits were followed precisely (imports, helper functions, `data` traits, UI HTML).
    *   Check for Python errors in the notebook when clicking a circuit card or generating a custom one.
    *   Verify the `combinatorial_circ_reg` in `combinatorial_circuits.py` is correct and the generator functions are working (you can test them directly if needed by running `python -m qoffeeapi.qoffeeapi.combinatorial_circuits` if the `if __name__ == '__main__':` block is set up for it, or by importing and calling them in a separate notebook cell).

*   **`qoffee_cli.py` Issues:**
    *   **Connection Errors:** Ensure the Qoffee-Maker Jupyter server is running and accessible at the specified `--base-url` (default `http://localhost:8887`).
    *   **POST Commands Failing (403 Forbidden/XSRF):** For `retry` and `delete` commands, a valid XSRF token is needed. Follow the instructions from `qoffee_cli.py get_xsrf_token --help` (or the warning message if the token file is missing) to create the `.qoffee_cli_xsrf_token` file. Alternatively, use `--ignore-xsrf` for testing if you understand the risks (not for production).

*   **General Debugging:**
    *   Use `print()` statements liberally in Python code (notebook cells or backend files) to trace execution and variable values.
    *   Use `console.log()` in JavaScript (`app.js` or browser dev tools) for frontend debugging.
    *   Check the Jupyter server console output for backend errors and logs.
```

This content provides a good overview for developers. I will now create the file.
