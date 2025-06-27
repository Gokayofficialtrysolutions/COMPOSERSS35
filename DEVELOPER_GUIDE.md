# Qoffee Explorer Developer Guide

This guide provides technical details, an architectural overview, and guidance for developers working on or extending the Qoffee Explorer project, now refocused as an **Offline Quantum Combinatorics Explorer**.

## Table of Contents

1.  [Architectural Overview](#1-architectural-overview)
2.  [Backend API (`qoffeeapi`) - Minimal](#2-backend-api-qoffeeapi---minimal)
    *   [Key Modules](#key-modules)
    *   [API Endpoints Summary](#api-endpoints-summary)
3.  [Combinatorial Circuits Engine (`combinatorial_circuits.py`)](#3-combinatorial-circuits-engine-combinatorial_circuitspy)
4.  [Frontend JavaScript (`qoffeefrontend/app.js`)](#4-frontend-javascript-qoffeefrontendappjs)
5.  [CLI Tool (`qoffee_cli.py`)](#5-cli-tool-qoffee_clipy)
6.  [Manual UI Setup in `qoffee.ipynb`](#6-manual-ui-setup-in-qoffeeipynb)
7.  [Conceptual Designs for UI/UX & Educational Content](#7-conceptual-designs-for-uiux--educational-content)
8.  [Security Considerations (Local Focus)](#8-security-considerations-local-focus)
9.  [Alternative Frontend Approaches (Long-Term)](#9-alternative-frontend-approaches-long-term)
10. [Troubleshooting Common Issues](#10-troubleshooting-common-issues)

---

## 1. Architectural Overview

The Qoffee Explorer project runs within a Jupyter Notebook environment, serving as an interactive platform for quantum circuit simulation and education, primarily focused on offline use.

*   **`qoffee.ipynb` (The Main Application UI - Requires Manual Setup):**
    *   The primary user interface, built with `ipywidgets` and custom `appwidgets` (especially `ReactiveHtmlWidget`).
    *   Python code in notebook cells manages UI state (via a global `data` ipywidget), generates quantum circuits using Qiskit, and runs local simulations.
    *   **Crucial Note:** All advanced UI features for the Quantum Combinatorics Explorer require **manual editing** of this notebook. Refer to [MANUAL_QOFFEE_IPYNB_SETUP.md](MANUAL_QOFFEE_IPYNB_SETUP.md) and [UI_SETUP_QUICKSTART.md](UI_SETUP_QUICKSTART.md).

*   **`qoffeeapi/` (Backend Python Package - Minimal):**
    *   Extends the Jupyter server with minimal API endpoints. After refactoring, its primary role is to provide a system health check (`/api/health`).
    *   **No longer handles Home Connect communication or its associated offline features (caching, queuing).**
    *   Contains the core logic for generating combinatorial quantum circuits.

*   **`qoffeefrontend/` (Frontend JavaScript & CSS):**
    *   A Jupyter Notebook extension bundling `app.js` and `app.css`.
    *   `app.js` primarily manages "App Mode" (Jupyter UI hiding), QR code generation for IBMQ Composer export (optional online feature), help display, and a basic global status bar (now mainly for browser online/offline status).
    *   Home Connect related JavaScript functions have been removed.

*   **`appwidgets/` (Custom Jupyter Widgets):**
    *   Provides `ReactiveHtmlWidget` and `JsPyWidget`, fundamental for the notebook's UI structure and Python-JS communication.

*   **`qoffee_cli.py` (Command Line Interface):**
    *   A standalone Python script, now primarily for calling the `/api/health` endpoint. Home Connect management commands have been removed.

*   **Configuration (`.env` file):**
    *   Mainly for the optional `IBMQ_API_KEY` (if users want to try online IBM Quantum features) and `QOFFEE_BASE_URL` for the CLI. Home Connect variables are removed.

*   **Local Data Storage:**
    *   The `.user/oauth-token.json` file is no longer actively used by the core refocused application, as Home Connect features that used it for token/cache/queue storage are removed. If this file exists from previous versions, it's ignored by the current core logic. Future local settings for the explorer might use a new file or a different mechanism if needed.

## 2. Backend API (`qoffeeapi`) - Minimal

With the removal of Home Connect features, the `qoffeeapi` is significantly simplified.

### Key Modules (`qoffeeapi/qoffeeapi/`):

*   **`__init__.py`:** Registers the `/api/health` endpoint.
*   **`api_orchestrator.py`:** Contains the `OrchestratorHealthCheckHandler`. Most other handlers have been removed.
*   **`combinatorial_circuits.py`:** (See Section 3).
*   **Removed Modules:** `hc_connector.py`, `oauth2.py`, `api_auth.py`. `utils.py` is minimal.

### API Endpoints Summary

*   **System Health:**
    *   `GET /api/health`: Provides a health check focusing on IBMQ key configuration and local Qiskit Aer availability. (Refer to `qoffeeapi/README.md` for response details).
*   **Removed Endpoints:** All Home Connect related endpoints (`/auth/*`, `/machine/*`, `/machines`, `/drink`, `/api/hc/*`) have been removed.

## 3. Combinatorial Circuits Engine (`combinatorial_circuits.py`)

Located in `qoffeeapi/qoffeeapi/combinatorial_circuits.py`. This is now a central piece of the application.

*   **Purpose:** Provides Python functions to generate Qiskit `QuantumCircuit` objects for various combinatorial concepts (Binomial, Permutations, Combinations, W-states).
*   **Generators:** Details of functions like `generate_binomial_distribution_circuit`, `generate_permutation_circuit_example`, `generate_combination_superposition_circuit`, `generate_custom_permutation_circuit`, `generate_w_state_n2_gates`, `generate_w_state_n3_library` are in the module itself.
*   **Registry (`combinatorial_circ_reg`):** A list of pre-defined circuit examples for easy loading via the UI (once manually set up).
*   **Extending:**
    1.  Add new generator functions to this file.
    2.  Add entries to `combinatorial_circ_reg`.
    3.  Update `MANUAL_QOFFEE_IPYNB_SETUP.md` with instructions for adding UI elements and educational content in `qoffee.ipynb` for new circuits.

## 4. Frontend JavaScript (`qoffeefrontend/app.js`)

*   **Refocused Role:** Manages app mode, help/QR code overlays (QR code for IBMQ export is an optional online feature), and a basic global status bar (primarily for browser online/offline indication now).
*   **Removed Functionality:** Home Connect related functions (`activateCoffeeMachine`, `requestDrink`, `refreshAuth`) and Home Connect queue status polling have been removed.
*   Locally bundled libraries (`lz-string.min.js`, `qrcode.min.js`) are still used for the IBMQ export QR code feature.

## 5. CLI Tool (`qoffee_cli.py`)

*   **Refocused Role:** Primarily serves to call the `/api/health` endpoint.
*   **Removed Commands:** All Home Connect specific commands (queue status, retry, delete, list machines, reset offline data) have been removed.
*   XSRF token handling is no longer relevant as only GET requests are made.

## 6. Manual UI Setup in `qoffee.ipynb`

This remains the most critical step for end-user functionality.
**Refer to [MANUAL_QOFFEE_IPYNB_SETUP.md](MANUAL_QOFFEE_IPYNB_SETUP.md) and the [UI_SETUP_QUICKSTART.md](UI_SETUP_QUICKSTART.md) for all instructions.**
The guides now focus solely on setting up the UI for the Quantum Combinatorics Explorer features.

## 7. Conceptual Designs for UI/UX & Educational Content

Detailed designs for interactive exercises, educational content structure, and advanced visualizations (Q-Sphere, etc.) exist to guide the manual UI implementation in `qoffee.ipynb`. These are intended to create a rich, engaging learning experience.

## 8. Security Considerations (Local Focus)

With the removal of external API integrations like Home Connect, security concerns are simplified but still important:

*   **IBMQ API Key (`.env` file):** If used for optional online IBMQ features, the `.env` file containing this key should be protected.
*   **Jupyter Server Security:** Standard practices for securing the Jupyter Notebook/Lab server (tokens/passwords, avoiding public exposure without security) are crucial.
*   **Code Execution from UI (`data-rh-exec` in `qoffee.ipynb`):** Notebooks (and thus their embedded executable code snippets) should only be run from trusted sources.

(The main `README.md` contains a more general security considerations section.)

## 9. Alternative Frontend Approaches (Long-Term)

Conceptual exploration of alternatives (dedicated web app, Voila, Panel/Streamlit) has been done. This remains relevant for future strategic decisions if the ipywidget-based notebook UI proves too restrictive for advanced features.

## 10. Troubleshooting Common Issues

*   **Python Import Errors:** Ensure correct virtual environment and `pip install -r requirements.txt`, then local packages.
*   **`qoffee.ipynb` UI Not Updating:** Restart kernel, run all cells, check browser console for JS errors. `ReactiveHtmlWidget` issues often relate to `data_model` or trait updates.
*   **Combinatorial Circuits Not Loading/Generating:** Double-check manual setup from `MANUAL_QOFFEE_IPYNB_SETUP.md`. Test generator functions directly.
*   **`qoffee_cli.py` Connection Errors:** Ensure Jupyter server is running at the correct URL.
*   **General Debugging:** Use `print()` in Python, `console.log()` in JS, and check Jupyter server logs.

This guide should provide a solid technical foundation for the refocused Qoffee Explorer project.
