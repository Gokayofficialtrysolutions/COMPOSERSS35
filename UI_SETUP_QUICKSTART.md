# Qoffee-Maker UI Setup: Quick Start Guide

This guide provides a condensed checklist of the **most critical manual steps** to get a basic version of the new UI features working in your `qoffee.ipynb` notebook.

**For complete, detailed instructions, ALWAYS refer to [MANUAL_QOFFEE_IPYNB_SETUP.md](MANUAL_QOFFEE_IPYNB_SETUP.md).** This quick start is for rapidly enabling core visibility and functionality.

**Goal:** To quickly see offline status messages, basic combinatorial circuit examples, and educational content placeholders.

**Prerequisites:**
*   You have the latest project code.
*   All Python dependencies from `requirements.txt` are installed.
*   `qoffeeapi` and `appwidgets` are installed (e.g., `pip install . --user` in their respective directories, or `pip install -e .` if developing).
*   Your `.env` file is configured.

---

**Quick Start Checklist (Perform in `qoffee.ipynb`):**

**Step 1: Essential Python Imports (Top of Notebook)**
   *   Ensure this cell is run. Refer to Section 1 of `MANUAL_QOFFEE_IPYNB_SETUP.md` for the full list of imports needed from `qoffeeapi.hc_connector` and `qoffeeapi.qoffeeapi.combinatorial_circuits`.
   *   Key additions:
     ```python
     import requests, json, time
     from qoffeeapi.hc_connector import get_connector
     from qoffeeapi.qoffeeapi.combinatorial_circuits import combinatorial_circ_reg, generate_binomial_distribution_circuit # ... and other generators
     ```

**Step 2: Add Core `data` Widget Traits (In the cell defining `data = Widget()`)**
   *   Refer to Section 2 of `MANUAL_QOFFEE_IPYNB_SETUP.md`.
   *   **Minimum traits for basic feedback:**
     ```python
     # Inside data.add_traits(...), ensure correct comma placement:
     network_status_message = Unicode("Online").tag(sync=True),
     command_queue_length = Int(0).tag(sync=True),
     ibmq_message = Unicode("").tag(sync=True),
     circuit_info_html = Unicode("").tag(sync=True),
     selected_combinatorial_type = Unicode("binomial").tag(sync=True), # Needed for custom
     combinatorial_N = Int(3).tag(sync=True) # Default for custom
     # Add others like combinatorial_k, _p, _pattern as you implement custom input view
     ```

**Step 3: Add Core Python Helper Functions (In a suitable code cell)**
   *   Refer to Section 3 of `MANUAL_QOFFEE_IPYNB_SETUP.md`.
   *   **Minimum functions for this quick start:**
     *   `refresh_ui_status_indicators()`: To update header status (needs `get_connector`).
     *   `load_combinatorial_circuit(circuit_id)`: To load pre-defined examples. (Ensure `combinatorial_circ_reg` and generator functions are in scope).
     *   Update `CircuitExecutor.probabilities_ibmq` method (Section 4 of manual guide) to set `data.ibmq_message`.
   *   **Run the cell containing these function definitions.**
   *   **(Optional but Recommended):** Call `refresh_ui_status_indicators()` once after its definition to initialize header display.

**Step 4: Basic UI Updates for Status & Circuit Loading (HTML in `ReactiveHtmlWidget` definitions)**

   *   **A. Header Status Display (Section 7 of manual guide):**
      *   Locate `header = appwidgets.ReactiveHtmlWidget(...)`.
      *   Add the `div#status-indicators` HTML snippet inside its template to display `${network_status_message}` and `${command_queue_length}`.
        ```html
        <!-- Inside <div id="header"> -->
        <div id="status-indicators" style="position: absolute; right: 200px; top: 5px; color: white; font-size: 0.75em; text-align: right; line-height: 1.2;">
            <p style="margin: 0; padding: 1px 0;" data-rh-if="${network_status_message}">${network_status_message}</p>
            <p style="margin: 0; padding: 1px 0;" data-rh-if="${command_queue_length} > 0">Queued HC: ${command_queue_length}</p>
        </div>
        ```

   *   **B. Combinatorial Circuit Examples in Welcome View (Section 5 of manual guide):**
      *   Locate `view_welcome_content = appwidgets.ReactiveHtmlWidget(...)`.
      *   Add the HTML block for "Explore Quantum Concepts (Examples)", including a few example cards:
        ```html
        <!-- Example Card -->
        <div class="col-md-3">
            <div class="card" data-rh-exec="load_combinatorial_circuit('binomial_n3_p0.5')">
              <div class="card-body">
                <h5 class="card-title">Binomial (N=3, p=0.5)</h5>
                <p class="card-text">3 qubits, 50% success prob.</p>
                <span class="arrow">→</span>
              </div>
            </div>
        </div>
        <!-- Add 1-2 more different example cards -->
        ```

   *   **C. IBMQ Message Display in Composer View (Section 7 of manual guide):**
      *   Locate `singleShotComposerCode = """..."""`.
      *   Add the `div` for `${ibmq_message}` inside `<div id="view-composer-singleshot">`.
        ```html
        <div data-rh-if="${ibmq_message}" style="color: #856404; ...">${ibmq_message}</div>
        ```

   *   **D. Educational Content Placeholder in Composer View (Section 7 of manual guide):**
      *   Locate `view_composer = VBox([...])`.
      *   Define `circuit_info_display = appwidgets.ReactiveHtmlWidget("<div>${circuit_info_html}</div>", data_model=data)`.
      *   Add `circuit_info_display` to the children of the main content VBox in `view_composer`.

**Step 5: Restart Kernel & Run All Cells**
   *   This is crucial after making code and widget definition changes.

---

This quick start will **not** enable:
*   Parameterized input for custom combinatorial circuits (requires the full "Parameter Input View" setup).
*   Fully detailed educational content (only basic titles/descriptions will show until `load_combinatorial_circuit` is fully fleshed out as per the main guide).
*   The Admin/Debug View.

However, it should give you visible feedback for offline status and allow you to load and run the first few combinatorial circuit examples. From here, you can incrementally implement the remaining features detailed in `MANUAL_QOFFEE_IPYNB_SETUP.md`.

Good luck!
