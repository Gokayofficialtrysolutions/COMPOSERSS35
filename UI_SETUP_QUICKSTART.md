# Qoffee Explorer UI Setup: Quick Start Guide

This guide provides a condensed checklist of the **most critical manual steps** to get a basic version of the new "Quantum Combinatorics Explorer" UI features working in your `qoffee.ipynb` notebook.

**For complete, detailed instructions, ALWAYS refer to [MANUAL_QOFFEE_IPYNB_SETUP.md](MANUAL_QOFFEE_IPYNB_SETUP.md).** This quick start is for rapidly enabling core circuit loading, educational content display, and IBMQ message feedback.

**Goal:** To quickly load and view pre-defined combinatorial circuit examples, see basic educational content, and view IBMQ status/fallback messages.

**Prerequisites:**
*   Latest project code.
*   Python environment with all dependencies from `requirements.txt` installed.
*   `qoffeeapi` and `appwidgets` packages installed locally.
*   `.env` file created from `env-template` (primarily for optional `IBMQ_API_KEY`).

---

**Quick Start Checklist (Perform in `qoffee.ipynb`):**

**Step 1: Essential Python Imports (Top of Notebook)**
   *   Ensure this cell is run. Refer to Section 1 of `MANUAL_QOFFEE_IPYNB_SETUP.md` for the full, updated list of imports.
   *   Key additions for combinatorial circuits:
     ```python
     # For Combinatorial Circuits
     from qoffeeapi.qoffeeapi.combinatorial_circuits import (
         combinatorial_circ_reg,
         generate_binomial_distribution_circuit, # and other specific generators used
         # ... ensure all generators used by combinatorial_circ_reg are imported
     )
     # Removed: requests, json, time, get_connector (as HC features are removed)
     ```

**Step 2: Add Core `data` Widget Traits (In the cell defining `data = Widget()`)**
   *   Refer to Section 2 of `MANUAL_QOFFEE_IPYNB_SETUP.md` for the focused list of traits.
   *   **Minimum traits for this quick start:**
     ```python
     # Inside data.add_traits(...), ensure correct comma placement:
     ibmq_message = Unicode("").tag(sync=True),            # For IBMQ fallback or execution status messages
     circuit_info_html = Unicode("").tag(sync=True),       # For educational content about circuits

     # Following are for the full custom parameter input view, but add selected_combinatorial_type
     # and combinatorial_N for now if you plan to test that view's skeleton soon.
     selected_combinatorial_type = Unicode("binomial").tag(sync=True),
     combinatorial_N = Int(3).tag(sync=True)
     # ... other combinatorial_ traits like _k, _p, _pattern can be added later when building the full input form.
     ```
    *Removed `network_status_message` and `command_queue_length` as they were HC-specific.*

**Step 3: Add Core Python Helper Functions (In a suitable code cell)**
   *   Refer to Section 3 of `MANUAL_QOFFEE_IPYNB_SETUP.md`.
   *   **Crucial function for this quick start:**
     *   `load_combinatorial_circuit(circuit_id)`: To load pre-defined examples and populate `data.circuit_info_html` and `data.heading`. (Ensure `combinatorial_circ_reg` and generator functions are in scope).
   *   **Update `CircuitExecutor.probabilities_ibmq` method** (Section 4 of `MANUAL_QOFFEE_IPYNB_SETUP.md`) to set `data.ibmq_message`.
   *   **Run the cell containing these function definitions.**
   *   *The API/connector-based status update functions (`update_hc_queue_status_from_api`, etc.) are no longer needed for this refocused project.*

**Step 4: Basic UI Updates for Circuit Loading & Info (HTML in `ReactiveHtmlWidget` definitions)**

   *   **A. Combinatorial Circuit Examples in Welcome View (Section 5 of `MANUAL_QOFFEE_IPYNB_SETUP.md`):**
      *   Locate `view_welcome_content = appwidgets.ReactiveHtmlWidget(...)`.
      *   Add the HTML block for "Explore Quantum Concepts (Examples)", including a few example cards that call `load_combinatorial_circuit`:
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
        <!-- Add 1-2 more example cards from combinatorial_circ_reg -->
        ```

   *   **B. IBMQ Message Display in Composer View (Section 7 of `MANUAL_QOFFEE_IPYNB_SETUP.md`):**
      *   Locate `singleShotComposerCode = """..."""`.
      *   Add the `div` for `${ibmq_message}` inside `<div id="view-composer-singleshot">`.
        ```html
        <div data-rh-if="${ibmq_message}" style="color: #856404; background-color: #fff3cd; ...">${ibmq_message}</div>
        ```

   *   **C. Educational Content Placeholder in Composer View (Section 7 of `MANUAL_QOFFEE_IPYNB_SETUP.md`):**
      *   Locate `view_composer = VBox([...])`.
      *   Define `circuit_info_display = appwidgets.ReactiveHtmlWidget("<div>${circuit_info_html}</div>", data_model=data)`. (A more styled version is in the main manual).
      *   Add `circuit_info_display` to the children of the main content VBox in `view_composer`.

**Step 5: Restart Kernel & Run All Cells**
   *   This is crucial after making code and widget definition changes.

---

This Quick Start will **not** enable:
*   Parameterized input for custom combinatorial circuits (requires the full "Parameter Input View" setup from `MANUAL_QOFFEE_IPYNB_SETUP.md`).
*   The global status bar in the header (as `network_status_message` and related functions were removed due to HC deprecation; basic browser online/offline is still in `app.js` status bar).
*   The Admin/Debug View.

However, it should allow you to load pre-defined combinatorial circuits, see their educational info placeholder, and view IBMQ-related messages. From here, incrementally implement the remaining features detailed in `MANUAL_QOFFEE_IPYNB_SETUP.md`.

Good luck!
