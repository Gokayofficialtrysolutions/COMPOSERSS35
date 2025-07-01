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

*   **`chimera.ipynb` (formerly `qoffee.ipynb`) (The Main Application UI):**
    *   The primary user interface, built with `ipywidgets` and custom `appwidgets` (especially `ReactiveHtmlWidget`).
    *   Python code in notebook cells manages UI state (via a global `data` ipywidget), generates quantum circuits (combinatorial and algorithmic like Deutsch-Jozsa) using Qiskit, and runs local simulations.
    *   Features dynamic measurement probability histograms, generic single-shot result display, and Bloch sphere visualizations.
    *   **Note on Manual Setup:** While AI-driven development modifies this notebook directly, historical setup context is in [MANUAL_QOFFEE_IPYNB_SETUP.md](MANUAL_QOFFEE_IPYNB_SETUP.md) (filename may be outdated if full project rename completes).

*   **`qoffeeapi/` (to be `chimeraapi/`) (Backend Python Package):**
    *   Extends the Jupyter server. Its primary role is providing a system health check API and the core logic for generating quantum circuits, including combinatorial types and introductory algorithms like Deutsch-Jozsa (in `combinatorial_circuits.py`).
    *   Home Connect features are removed.

*   **`qoffeefrontend/` (to be `chimerafrontend/`) (Frontend JavaScript & CSS):**
    *   A Jupyter Notebook extension bundling `app.js` and `app.css`.
    *   `app.js` manages "App Mode", QR code generation, help display, and a basic global status bar. Legacy Home Connect JS functions are removed.

*   **`appwidgets/` (Custom Jupyter Widgets):**
    *   Provides `ReactiveHtmlWidget` and `JsPyWidget`.

*   **`chimera_cli.py` (formerly `qoffee_cli.py`) (Command Line Interface):**
    *   A standalone Python script for system health checks via `/api/health`.

*   **Configuration (`.env` file):**
    *   Mainly for `IBMQ_API_KEY` (optional) and `CHIMERA_BASE_URL` (formerly `QOFFEE_BASE_URL`) for the CLI.

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

Located in `qoffeeapi/qoffeeapi/combinatorial_circuits.py` (path may change if project fully renamed to `chimeraapi`). This is a central piece of the application.

*   **Purpose:** Provides Python functions to generate Qiskit `QuantumCircuit` objects for various combinatorial concepts (Binomial, Permutations, Combinations, W-states) and introductory quantum algorithms like Deutsch-Jozsa.
*   **Generators:** Includes functions like `generate_binomial_distribution_circuit`, `generate_permutation_circuit_example`, `generate_combination_superposition_circuit`, `generate_custom_permutation_circuit`, `generate_w_state_n2_gates`, `generate_w_state_n3_library`, and `generate_deutsch_jozsa_circuit`.
*   **Registry (`combinatorial_circ_reg`):** A list of pre-defined circuit examples (including algorithms) for easy loading via the UI.
*   **Extending:**
    1.  Add new generator functions for circuits or algorithms to this file (or organize into separate algorithm-specific files within the package).
    2.  Add new entries to `combinatorial_circ_reg`.
    3.  Update `chimera.ipynb` to include new UI elements (e.g., cards in welcome view for new examples/algorithms, specific input views if parameters are complex) and ensure the `load_combinatorial_circuit` function (or similar logic) populates `data.circuit_info_html` with relevant educational content.

## 4. Frontend JavaScript (`qoffeefrontend/app.js` - path may change)

*   **Current Role:** Manages app mode, help/QR code overlays, and a basic global status bar.
*   Recent changes focused on Python-side UI logic in `chimera.ipynb`; `app.js` remains largely unaffected by these specific enhancements but is crucial for the overall app shell.

## 5. CLI Tool (`chimera_cli.py` - formerly `qoffee_cli.py`)

*   **Current Role:** Primarily serves to call the `/api/health` endpoint.
*   No changes in this development cycle.

## 6. UI Implementation in `chimera.ipynb` (formerly `qoffee.ipynb`)

The UI is primarily built and managed within this notebook using `ipywidgets` and `appwidgets`. AI-driven development directly modifies this notebook to implement UI changes and integrate backend functionalities. Historical manual setup steps are documented in `MANUAL_QOFFEE_IPYNB_SETUP.md` but may not reflect the latest state if the AI has made subsequent programmatic changes. Key UI aspects for the Quantum Laboratory now include:
*   Dynamic generation of histograms based on circuit qubit count.
*   Generic display of single-shot measurement results.
*   Display of educational content (including for algorithms like Deutsch-Jozsa) and IBMQ status messages.
*   Integration of Bloch sphere visualizations (`plot_bloch_multivector`).
*   Examples of introductory quantum algorithms (e.g., Deutsch-Jozsa) available from the welcome screen.

## 7. Conceptual Designs for UI/UX & Educational Content

The project aims for a rich, engaging learning experience. This includes:
*   Contextual explanations, formulas, and exploration ideas alongside circuits and algorithms (implemented via `data.circuit_info_html`).
*   Visualizations like histograms and Bloch spheres to aid understanding.
*   Future plans (see `PROJECT_ROADMAP.md`) include more interactive exercises and advanced visualizations (e.g., Q-Sphere).

## 8. Security Considerations (Local Focus)

With the removal of external API integrations like Home Connect, security concerns are simplified but still important:

*   **IBMQ API Key (`.env` file):** If used for optional online IBMQ features, the `.env` file containing this key should be protected.
*   **Jupyter Server Security:** Standard practices for securing the Jupyter Notebook/Lab server (tokens/passwords, avoiding public exposure without security) are crucial.
*   **Code Execution from UI (`data-rh-exec` in `chimera.ipynb`):** Notebooks (and thus their embedded executable code snippets) should only be run from trusted sources.

(The main `README.md` contains a more general security considerations section.)

## 9. Alternative Frontend Approaches (Long-Term)

Conceptual exploration of alternatives (dedicated web app, Voila, Panel/Streamlit) has been done. This remains relevant for future strategic decisions if the ipywidget-based notebook UI proves too restrictive for advanced features.

## 10. Troubleshooting Common Issues

*   **Python Import Errors:** Ensure correct virtual environment and `pip install -r requirements.txt`, then local packages (e.g., `qoffeeapi`/`chimeraapi`, `appwidgets`).
*   **`chimera.ipynb` (formerly `qoffee.ipynb`) UI Not Updating:** Restart kernel, run all cells, check browser console for JS errors. `ReactiveHtmlWidget` issues often relate to `data_model` or trait updates. Ensure `data.dynamic_hist_html` is being populated correctly by `composer_update_handler`.
*   **Combinatorial Circuits Not Loading/Generating:** Double-check any manual setup from `MANUAL_QOFFEE_IPYNB_SETUP.md` (if still relevant), or directly test generator functions in `combinatorial_circuits.py`. Ensure `chimera.ipynb` is calling them correctly.
*   **`chimera_cli.py` (formerly `qoffee_cli.py`) Connection Errors:** Ensure Jupyter server is running at the correct URL (check `CHIMERA_BASE_URL`).
*   **General Debugging:** Use `print()` in Python, `console.log()` in JS, and check Jupyter server logs.

This guide should provide a solid technical foundation for the refocused CHIMera Explorer (formerly Qoffee Explorer) project.
