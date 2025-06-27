# Qoffee-Maker: Project Roadmap & Handover Guide

This document provides a summary of the current Qoffee-Maker project status after the recent autonomous development cycle, outlines the critical next steps for manual UI implementation, and presents a potential roadmap for future development.

## 1. Current Project Status (End of Autonomous Development Cycle)

The Qoffee-Maker project has been significantly enhanced to function as a foundational "Quantum Combinatorics Explorer" with robust backend capabilities and offline support for its original Home Connect features.

**Key Implemented Assets & Features:**

*   **Backend (`qoffeeapi/`):**
    *   **Home Connect Offline Engine:** Full support for data caching, command queuing, automated retries, and a failed-command queue for Home Connect operations. All state persisted in `.user/oauth-token.json`.
    *   **Management APIs:** Endpoints for Home Connect queue status/management (`/api/hc/*`) and system health (`/api/health`).
    *   **Combinatorial Circuit Engine (`combinatorial_circuits.py`):** Functions to generate Qiskit circuits for Binomial Distributions, various Permutations (pre-defined patterns and custom lists), N-choose-k Combinations (via `qc.initialize`), and example W-states (N=2 gates, N=3 library). Includes a registry of pre-defined examples.
    *   **Code Quality:** Reviewed for clarity, comments, and error handling.

*   **Frontend JavaScript (`qoffeefrontend/app.js`):**
    *   **Offline Support:** Localized JS libraries (lz-string, qrcode.js).
    *   **User Feedback:** `alert()` notifications for queued Home Connect commands. Global status bar for basic network status and polled Home Connect queue/failed command counts.
    *   **Enhanced IBMQ Export:** UI includes offline notices and QASM display.

*   **CLI Tool (`qoffee_cli.py`):**
    *   Command-line access for Home Connect queue status/management, machine listing, system health, and resetting offline data. Human-readable and JSON output.

*   **Comprehensive Documentation:**
    *   **`README.md` (Root):** Overall project overview, installation, new features, security.
    *   **`MANUAL_QOFFEE_IPYNB_SETUP.md`:** **Critical guide** for all manual UI changes needed in `qoffee.ipynb`.
    *   **`UI_SETUP_QUICKSTART.md`:** Condensed checklist for basic manual UI setup.
    *   **`DEVELOPER_GUIDE.md`:** Technical architecture, API details, backend logic, extending features, troubleshooting, conceptual UI designs (User Stories, Interactive Exercises, Admin Panel), and future frontend strategies.
    *   Sub-project READMEs updated.

**The project is stable on the backend and core JS frontend. The next major advancement depends on UI implementation.**

## 2. Critical Next Step: Manual UI Implementation in `qoffee.ipynb`

To make the new features fully accessible and user-friendly, the UI within `qoffee.ipynb` must be manually updated.

**Primary Resource:** **[MANUAL_QOFFEE_IPYNB_SETUP.md](MANUAL_QOFFEE_IPYNB_SETUP.md)**

**Suggested Prioritization for Manual UI Tasks:**

1.  **Core Setup (Essential First Steps):**
    *   Add all new required Python imports to `qoffee.ipynb`.
    *   Add all new specified traits to the global `data` ipywidget.
    *   Add all new Python helper functions (e.g., `load_combinatorial_circuit`, `generate_and_load_custom_combinatorial_circuit`, status update functions) to appropriate code cells.
    *   Update `CircuitExecutor.probabilities_ibmq` to set `data.ibmq_message`.
    *   *Verify these by restarting the kernel and running all cells without error.*

2.  **Combinatorial Circuits Feature - Basic UI:**
    *   Modify `view_welcome_content` HTML to add the new section "Explore Quantum Concepts (Examples)" with cards for pre-defined combinatorial circuits (linking to `load_combinatorial_circuit`).
    *   Add the card to `view_welcome_content` for navigating to the "Custom Combinatorial Circuit" input view.

3.  **Parameterized Combinatorial Circuit Input View:**
    *   Create the new `view_combinatorics_input` using `ipywidgets` as detailed in the manual guide (Dropdown for type, IntText/FloatText/Textarea for parameters, Buttons).
    *   Link input widgets to their respective `data` traits.
    *   Implement the Python `on_click` handlers for its buttons.
    *   Add this new view to the main `app` widget using `app.add_widget('combinatorics_input_view', view_combinatorics_input)`.

4.  **Educational Content Display:**
    *   Implement the `circuit_info_display` `ReactiveHtmlWidget` in the Composer view.
    *   Ensure `load_combinatorial_circuit` and `generate_and_load_custom_combinatorial_circuit` correctly populate `data.circuit_info_html`.

5.  **Offline & Status UI Feedback:**
    *   Modify the `header` widget's HTML to display `data.network_status_message` and `data.command_queue_length`.
    *   Ensure a mechanism exists to call `refresh_ui_status_indicators()` or `update_system_health_from_api()` (e.g., a new button, or piggybacking on existing view load functions) to update these header traits.
    *   Modify the "Single Shot" area in the Composer view to display `data.ibmq_message`.

6.  **(Optional but Recommended) Admin/Debug View:**
    *   Implement the conceptualized "Admin/Debug View" using `ipywidgets` for in-notebook health/queue status display and basic queue management.

**Testing:** After these UI changes, perform thorough testing using the scenarios outlined in `DEVELOPER_GUIDE.md` (or previous agent messages).

## 3. Future Development Roadmap

This roadmap outlines potential future phases to further enhance the "Quantum Combinatorics Explorer."

**Phase A: Full Notebook UI Integration & Polish**
*   **Objective:** Complete all manual UI setups from `MANUAL_QOFFEE_IPYNB_SETUP.md` to a high standard.
*   **Key Features:**
    *   Fully functional parameterized input for all combinatorial circuits.
    *   Seamless display of educational content.
    *   Clear and dynamic offline/queued/error status indicators throughout the UI.
    *   Functional Admin/Debug panel within the notebook.
    *   Implementation of the "Advanced Interactive Exercises" designed in Phase 11.

**Phase B: Advanced Quantum Concepts & Circuit Library Expansion**
*   **Objective:** Broaden the scope of quantum and combinatorial concepts covered.
*   **Key Features:**
    *   **More Permutation Algorithms:** Implement generators for specific mathematical permutations (e.g., general bit-reversal for any N, perfect shuffle for any N, QFT circuit).
    *   **Advanced Combination/State Preparation:** Gate-based constructions for more W-states or Dicke states (N>3); circuits based on generating functions.
    *   **Other Discrete Math/Quantum Concepts:** Introduction to quantum representations of small graphs, simple quantum random walks.
    *   **Introductory Quantum Algorithms:** Basic Grover's search for specific combinatorial items, simple Phase Estimation examples tied to combinatorial problems.
    *   Expand `combinatorial_circ_reg` and corresponding educational content.

**Phase C: Richer Visualizations & Enhanced Interactivity**
*   **Objective:** Improve the tools for understanding quantum states and circuit behavior.
*   **Key Features (requires manual UI work in notebook):**
    *   **Advanced Statevector Visualizations:** Integrate `plot_state_qsphere`, `plot_state_city`, `array_to_latex` (via `HTMLMath` widget) for detailed state analysis.
    *   **Interactive Bloch Spheres:** Allow users to select individual qubits (for N <= ~4) and view their (reduced) state on a Bloch sphere.
    *   **Circuit Evolution (Conceptual):** Explore ways to visualize step-by-step state changes as gates are applied (for very small circuits).
    *   **Enhanced Measurement Statistics:** Implement dynamic grouping of histogram results by Hamming weight or other user-defined criteria. Comparative plots (theory vs. simulation).

**Phase D: Deeper Educational Content & User Experience**
*   **Objective:** Transform the tool into a more comprehensive learning platform.
*   **Key Features:**
    *   **Guided Tutorials:** Create step-by-step tutorial paths within the notebook for specific concepts.
    *   **Interactive Challenges/Quizzes:** Embed small exercises with feedback.
    *   **Contextual Help & Glossary:** In-UI tooltips for gates/concepts; a searchable glossary.

**Phase E: Performance, Scalability & Optional Cloud Integration**
*   **Objective:** Optimize local simulation and explore optional cloud execution.
*   **Key Features:**
    *   Optimize Python circuit generation for speed, especially for larger N (up to ~10-12 qubits).
    *   (If performance becomes an issue for complex client-side viz) Explore WebAssembly for parts of JS.
    *   **Optional IBM Quantum Integration (Advanced):**
        *   Robust asynchronous job submission to real IBMQ devices.
        *   Fetching and displaying job status and results.
        *   Displaying basic backend calibration/noise data alongside simulations.

**Phase F: Long-Term Architectural Strategy**
*   **Objective:** Evaluate if the Jupyter Notebook UI meets long-term goals or if a transition to a different frontend architecture is warranted.
*   **Actions:**
    *   Revisit pros/cons of Voila, Panel/Streamlit, or a dedicated web application (e.g., Flask/React) based on experience from prior phases.
    *   If a move is decided, plan migration for a subset of features.

This roadmap provides a flexible guide. Priorities can be adjusted based on user feedback and development resources. The immediate focus should be on realizing the already-designed UI in `qoffee.ipynb`.
