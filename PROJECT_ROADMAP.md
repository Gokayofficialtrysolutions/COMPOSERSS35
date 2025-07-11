# CHIMera Explorer & QOS Initiative: Project Roadmap & Handover Guide

**Note:** This roadmap is being updated to reflect the project's pivot to the "CHIMera Explorer" (a Quantum Combinatorics educational tool) and the long-term "CHIMera QOS" initiative. Sections pertaining to the original "Qoffee-Maker" IoT functionality and its specific UI tasks are now considered legacy and will be substantially revised or removed in a future documentation overhaul. The immediate changes in this version focus on updating names and paths for consistency with the current codebase state.

This document provides a summary of the CHIMera Explorer project status after the recent autonomous development cycle, outlines critical next steps, and presents a potential roadmap for future development.

## 1. Current Project Status (End of Autonomous Development Cycle for CHIMera Explorer v1)

The CHIMera Explorer project has been significantly enhanced to function as a foundational "Quantum Combinatorics Explorer". The backend capabilities for the original IoT project (Home Connect) are now considered legacy.

**Key Implemented Assets & Features (for CHIMera Explorer):**

*   **Backend (`qoffeeapi/` - directory name preserved):**
    *   **Legacy Home Connect Offline Engine:** (Functionality preserved but considered legacy).
    *   **Management APIs:** System health (`/api/health`). Legacy Home Connect APIs (`/api/hc/*`) preserved but not central to CHIMera Explorer.
    *   **Combinatorial Circuit Engine (`qoffeeapi/qoffeeapi/combinatorial_circuits.py`):** Core for CHIMera Explorer. Functions to generate Qiskit circuits for Binomial Distributions, various Permutations, N-choose-k Combinations, and W-states. Includes a registry of pre-defined examples.
    *   **Code Quality:** Reviewed for clarity, comments, and error handling. Internal branding updated to CHIMera.

*   **Frontend JavaScript (`qoffeefrontend/app.js` - in `qoffeefrontend/` directory, name preserved):**
    *   **Offline Support:** Localized JS libraries.
    *   **User Feedback:** Global status bar. Legacy Home Connect feedback mechanisms preserved but not central. Internal branding updated to CHIMera.
    *   **Enhanced IBMQ Export:** UI includes offline notices and QASM display.

*   **CLI Tool (`chimera_cli.py`):**
    *   Command-line access for system health. Legacy Home Connect CLI features preserved but not central.

*   **Comprehensive Documentation (being updated for CHIMera Explorer):**
    *   **`README.md` (Root):** Overall project overview, installation, new features, security.
    *   **`MANUAL_CHIMERA_IPYNB_SETUP.md`:** **Critical guide** for all manual UI changes needed in `chimera.ipynb`.
    *   **`UI_SETUP_QUICKSTART.md`:** Condensed checklist for basic manual UI setup.
    *   **`DEVELOPER_GUIDE.md`:** Technical architecture, API details, backend logic, extending features, troubleshooting.
    *   Sub-project READMEs updated.

**The project is stable on the backend and core JS frontend. The next major advancement depends on UI implementation.**

## 2. Critical Next Step: Manual UI Implementation in `chimera.ipynb`

To make the new features fully accessible and user-friendly, the UI within `chimera.ipynb` must be manually updated.

**Primary Resource:** **[MANUAL_CHIMERA_IPYNB_SETUP.md](MANUAL_CHIMERA_IPYNB_SETUP.md)**

**Suggested Prioritization for Manual UI Tasks (Note: some of this may now be outdated due to project pivot - to be revised):**

1.  **Core Setup (Essential First Steps):**
    *   Add all new required Python imports to `chimera.ipynb`.
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

This roadmap outlines potential future phases to further enhance the "Quantum Combinatorics Explorer." (Content below is largely legacy and needs revision to align with CHIMera Explorer and QOS vision).

**Phase A: Full Notebook UI Integration & Polish (Legacy Context - Needs Revision)**
*   **Objective:** Complete all manual UI setups from `MANUAL_CHIMERA_IPYNB_SETUP.md` to a high standard for `chimera.ipynb`.
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

This roadmap provides a flexible guide. Priorities can be adjusted based on user feedback and development resources. The immediate focus should be on realizing the already-designed UI in `chimera.ipynb` and then progressing the CHIMera QOS initiative.
