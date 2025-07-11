# Manual Setup for CHIMera Explorer Notebook UI

This guide provides the necessary steps to manually update your `chimera.ipynb` Jupyter Notebook to enable the user interface for the **CHIMera Explorer (Offline Quantum Combinatorics Tool)**. This includes UI for parameterized input for combinatorial quantum circuits, display of educational content, and IBMQ-related messages.

**Due to current tooling limitations, these changes cannot be reliably applied programmatically by the automated development agent and require your manual intervention.**

Please apply these changes carefully to the appropriate cells within your `chimera.ipynb` notebook.

## 1. Add Required Python Imports

In a code cell near the top of `chimera.ipynb` (typically where you import `ipywidgets`, `appwidgets`, `qiskit`, etc.), ensure the following imports are present:

```python
# Existing imports ...
import json     # For helper functions if they parse JSON (though not strictly needed by provided funcs)
import time     # For potential use in UI logic (e.g. debouncing, though not in current funcs)
# Ensure the global 'data' widget is defined before functions that use it.

# For Combinatorial Circuits
from qoffeeapi.qoffeeapi.combinatorial_circuits import (
    combinatorial_circ_reg,
    generate_binomial_distribution_circuit,
    generate_permutation_circuit_example,
    generate_combination_superposition_circuit,
    generate_custom_permutation_circuit,
    generate_w_state_n2_gates,      # Added W-state generators
    generate_w_state_n3_library
)
# Ensure other necessary imports like numpy, qiskit, ipywidgets, appwidgets are already there.
# Removed: requests, get_connector (as HC features are removed)
```

## 2. Add New Traits to the `data` Widget

Locate the code cell where the global `data` ipywidget is defined (e.g., `data = Widget()`) and its traits are added using `data.add_traits(...)`. You need to add new traits to this `data` object for the CHIMera Explorer.

**Carefully insert the following lines inside the `data.add_traits(` call.** Ensure correct comma placement.

```python
    # ... (any existing traits like view, heading),
    # ENSURE THE LINE ABOVE THIS BLOCK ENDS WITH A COMMA

    # For IBMQ fallback/status messages & educational content
    ibmq_message = Unicode("").tag(sync=True),
    circuit_info_html = Unicode("").tag(sync=True),

    # Traits for Parameterized Combinatorial Circuits
    combinatorial_N = Int(3).tag(sync=True),
    combinatorial_k = Int(2).tag(sync=True), # For N-choose-k combinations
    combinatorial_p = Float(0.5).tag(sync=True), # For Binomial success probability
    combinatorial_pattern = Unicode("0,2,1,3").tag(sync=True), # For custom permutation list string
    selected_combinatorial_type = Unicode("binomial").tag(sync=True) # To select generator type
    # If this is the ABSOLUTE LAST trait before the closing parenthesis of add_traits, remove the trailing comma.
```
*Removed `network_status_message` and `command_queue_length` as they were HC-specific.*

## 3. Add Python Helper Functions to `chimera.ipynb`

In a suitable code cell (e.g., where other UI helper functions like `load_starting_point` are defined), add the following Python functions. Ensure global variables like `data`, `composer`, `combinatorial_circ_reg`, and `composer_update_handler` are accessible.

```python
# Helper functions for Combinatorial Circuits UI

def load_combinatorial_circuit(circuit_id):
    # Ensure all required globals are accessible
    global data, composer, combinatorial_circ_reg, composer_update_handler
    # Ensure generator functions are in scope (imported from combinatorial_circuits)

    print(f"Attempting to load combinatorial circuit: {circuit_id}")
    data.ibmq_message = ""
    data.circuit_info_html = ""
    try:
        circuit_entry = next(filter(lambda x: x['id'] == circuit_id, combinatorial_circ_reg))
    except StopIteration:
        err_msg = f"Error: Circuit '{circuit_id}' not found in registry."
        print(err_msg)
        data.ibmq_message = err_msg # Use ibmq_message for general status/error for this view
        return

    try:
        generator_func = circuit_entry["generator"]
        qc = generator_func(**circuit_entry["args"])

        data.composer_init_circuit = { # Used by composer view logic if any
            "id": circuit_entry["id"], "name": circuit_entry["name"],
            "init_text": circuit_entry.get("description", "")
        }
        data.single_shot_device = 'simulator' # Default for quantum explorer
        data.single_shot_status = 0

        composer.circuit = qc
        if 'composer_update_handler' in globals() and callable(composer_update_handler):
             composer_update_handler({'name': 'circuit', 'old': None, 'new': qc, 'owner': composer, 'type': 'change'})

        data.show_mock_results = False # Reset relevant display flags
        data.show_qasm_results = False

        current_heading = f"Composer: {circuit_entry['name']}"
        data.heading = current_heading

        # Populate educational content dynamically
        title = circuit_entry['name']
        description = circuit_entry.get('description', 'An interesting quantum circuit.')
        args_str = ", ".join([f"{k}={v}" for k,v in circuit_entry['args'].items()])
        specific_details_html = f"<li>Base Parameters: {args_str}</li>" if args_str else ""
        formulas_html = ""
        interpretation_html = "<p>This circuit demonstrates a key quantum mechanical or combinatorial principle.</p>"
        explore_html = "<li>Run with various shot counts to observe statistical outcomes.</li><li>Examine the QASM code.</li>"

        # Customize content based on circuit type (using 'id' or 'name' for hints)
        circuit_id_lower = circuit_entry["id"].lower()
        if "binomial" in circuit_id_lower:
            N_val = circuit_entry["args"]["num_qubits"]
            p_val = circuit_entry["args"]["success_probability_p"]
            title = f"Binomial Distribution (N={N_val}, p={p_val:.2f})"
            description = f"Models {N_val} independent trials, each with success probability p={p_val:.2f} of measuring |1⟩."
            interpretation_html = "<p>Each qubit represents an independent trial. Ry(θ) gates set the success probability 'p'.</p>"
            formulas_html = f"<pre><code>P(k successes) = C(N,k) * p<sup>k</sup> * (1-p)<sup>N-k</sup>\nθ for Ry = 2*arcsin(√p)</code></pre>"
            explore_html = "<li>Vary N and p (using custom generation) to see distribution changes.</li><li>Observe how measurement statistics approach theory with more shots.</li><li>Group histogram results by number of '1's (successes).</li>"
        elif "perm" in circuit_id_lower:
            interpretation_html = "<p>This circuit rearranges (permutes) the computational basis states.</p>"
            if "custom" in circuit_id_lower:
                 pattern_str = str(circuit_entry["args"]["permutation_list"])
                 formulas_html = f"<pre><code>Input state |i⟩ maps to |P[i]⟩\nPattern P: {pattern_str}</code></pre>"
            elif "example" in circuit_id_lower:
                 formulas_html = f"<pre><code>Pattern: {circuit_entry['args']['pattern']}</code></pre><p>Implemented using SWAP gates.</p>"
            explore_html = "<li>Initialize input to a basis state and observe the permuted output (requires modifying circuit before this permutation).</li><li>Try a superposition input.</li>"
        elif "comb" in circuit_id_lower or "w_state" in circuit_id_lower:
            is_w_state = "w_state" in circuit_id_lower
            if is_w_state:
                 N_val = circuit_entry["args"].get("num_qubits", 3 if "n3" in circuit_id_lower else 2 if "n2" in circuit_id_lower else 0) # Infer N for W-states
                 k_val = 1
                 title = f"W-State (N={N_val}, k=1)"
                 description = f"Prepares the {N_val}-qubit W-state, a superposition of states with one |1⟩."
                 interpretation_html = "<p>The W-state is a specific entangled state where exactly one qubit is excited. This example uses " + ("Qiskit's library function." if "library" in circuit_id_lower else "elementary gates.") + "</p>"
                 formulas_html = f"<pre><code>|W<sub>{N_val}</sub>⟩ = (1/√{N_val}) * (|10...0⟩ + ... + |0...01⟩)</code></pre>"
            else: # General combinations
                N_val = circuit_entry["args"]["num_qubits_n"]
                k_val = circuit_entry["args"]["num_to_select_k"]
                title = f"Combinations (N={N_val} choose k={k_val})"
                description = f"Superposition of states selecting {k_val} of {N_val} items."
                interpretation_html = "<p>Prepares an equal superposition of N-qubit states with Hamming weight 'k' (k ones). Uses qc.initialize().</p>"
                formulas_html = f"<pre><code>Target: (1/√M) * Σ |state_with_k_ones⟩\nM = C(N,k) = N! / (k!(N-k)!)</code></pre>"
            explore_html = "<li>Observe that only states with 'k' ones have non-zero probability.</li><li>Change N and k (using custom generation).</li><li>If W-state from library, try decomposing to see gates.</li>"

        data.circuit_info_html = f"""<h4>{title}</h4>
                                     <p><strong>Concept:</strong> {description}</p>
                                     <p><strong>Circuit Details:</strong></p>
                                     <ul>{specific_details_html}</ul>
                                     {interpretation_html}
                                     <div><strong>Key Formulas/Representations:</strong> {formulas_html if formulas_html else '<p>N/A</p>'}</div>
                                     <p><strong>Try Exploring:</strong></p>
                                     <ul>{explore_html}</ul>"""
        data.view = 'composer'
        print(f"Successfully loaded: {circuit_entry['name']}")
    except Exception as e:
        err_msg = f"Error loading circuit '{circuit_id}': {str(e)}"
        print(err_msg)
        data.ibmq_message = err_msg

def generate_and_load_custom_combinatorial_circuit():
    global data, composer, generate_binomial_distribution_circuit, generate_combination_superposition_circuit, generate_custom_permutation_circuit, composer_update_handler
    data.ibmq_message = ""
    data.circuit_info_html = ""
    try:
        gen_type = data.selected_combinatorial_type
        qc = None
        circuit_name = "Custom Combinatorial Circuit"
        description = "User-defined combinatorial circuit."
        interpretation_html = ""
        formulas_html = ""
        explore_html = "<li>Experiment with different parameters.</li><li>Observe measurement outcomes.</li>"

        if gen_type == "binomial":
            n_val = int(data.combinatorial_N)
            p_val = float(data.combinatorial_p)
            if n_val <= 0 or not (0 <= p_val <= 1):
                data.ibmq_message = "Invalid Binomial parameters: N must be > 0, and 0 ≤ p ≤ 1."
                return
            qc = generate_binomial_distribution_circuit(n_val, p_val)
            circuit_name = qc.name
            description = f"Models {n_val} independent trials, each with success probability p={p_val:.2f} of measuring |1⟩."
            interpretation_html = "<p>Each qubit uses an Ry gate to set its measurement probability for |1⟩ to 'p'.</p>"
            formulas_html = f"<pre><code>P(k) = C(N,k)p<sup>k</sup>(1-p)<sup>N-k</sup>\nθ for Ry = 2*arcsin(√p)</code></pre>"
        elif gen_type == "combination":
            n_val = int(data.combinatorial_N)
            k_val = int(data.combinatorial_k)
            if k_val < 0 or k_val > n_val or n_val <= 0:
                data.ibmq_message = "Invalid Combination parameters: N must be > 0, and 0 ≤ k ≤ N."
                return
            qc = generate_combination_superposition_circuit(n_val, k_val)
            circuit_name = qc.name
            description = f"Superposition of states selecting {k_val} of {n_val} items."
            interpretation_html = "<p>Prepares an equal superposition of N-qubit states with Hamming weight 'k'. Uses qc.initialize().</p>"
            formulas_html = f"<pre><code>Target: (1/√M) * Σ |state_with_k_ones⟩\nM = C(N,k) = N! / (k!(N-k)!)</code></pre>"
        elif gen_type == "permutation":
            n_val = int(data.combinatorial_N)
            try:
                pattern_list_str = data.combinatorial_pattern.strip()
                if not pattern_list_str:
                    data.ibmq_message = "Permutation list cannot be empty."
                    return
                pattern_list = [int(x.strip()) for x in pattern_list_str.split(',')]
                if len(pattern_list) != 2**n_val: # Basic validation
                    data.ibmq_message = f"Permutation list length must be {2**n_val} for N={n_val} qubits."
                    return
                if sorted(pattern_list) != list(range(2**n_val)): # Basic validation
                    data.ibmq_message = f"Permutation list must be a valid permutation of indices 0 to {2**n_val - 1}."
                    return
                qc = generate_custom_permutation_circuit(n_val, pattern_list)
                circuit_name = qc.name
                description = f"Custom permutation for N={n_val} qubits."
                interpretation_html = "<p>Rearranges computational basis states according to the provided list.</p>"
                formulas_html = f"<pre><code>Pattern: {pattern_list}</code></pre>"
            except ValueError as ve:
                 data.ibmq_message = f"Invalid permutation pattern format: {ve}. Expected comma-separated integers (e.g., '0,2,1,3')."
                 return
            except Exception as e_perm:
                data.ibmq_message = f"Error generating permutation circuit: {e_perm}."
                return
        else:
            data.ibmq_message = f"Unknown combinatorial type selected: {gen_type}"
            return

        if qc:
            data.composer_init_circuit = {"id": "custom_combinatorial", "name": circuit_name, "init_text": description}
            data.single_shot_device = 'simulator'
            data.single_shot_status = 0
            composer.circuit = qc
            if 'composer_update_handler' in globals() and callable(composer_update_handler):
                composer_update_handler({'name': 'circuit', 'old': None, 'new': qc, 'owner': composer, 'type': 'change'})
            data.show_mock_results = False; data.show_qasm_results = False
            data.heading = f"Composer: {circuit_name}"
            data.circuit_info_html = f"""<h4>{circuit_name}</h4>
                                     <p><strong>Concept:</strong> {description}</p>
                                     {interpretation_html}
                                     <div><strong>Key Formulas/Representations:</strong> {formulas_html if formulas_html else '<p>N/A</p>'}</div>
                                     <p><strong>Try Exploring:</strong></p>
                                     <ul>{explore_html}</ul>"""
            data.view = 'composer'
            print(f"Successfully generated and loaded: {circuit_name}")
        else:
            data.ibmq_message = "Failed to generate the custom circuit (qc remained None)."
    except Exception as e:
        err_msg = f"An unexpected error occurred in generate_and_load_custom_combinatorial_circuit: {str(e)}"
        print(err_msg)
        data.ibmq_message = err_msg
```
*Removed `update_hc_queue_status_from_api`, `update_system_health_from_api`, `refresh_ui_status_indicators` as they are HC-specific or rely on APIs no longer central to the offline explorer.*

## 4. Update `CircuitExecutor.probabilities_ibmq`

Locate this method in `chimera.ipynb` (it's inside the `CircuitExecutor` class). Ensure it sets `data.ibmq_message` appropriately. This function is now for *optional* online IBMQ execution if the user sets up an API key.

```python
   # Inside class CircuitExecutor:
   def probabilities_ibmq(self, num_shots=1, secs_timeout=30):
       global data
       data.ibmq_message = ""

       # Ensure backend_ibm is globally defined and potentially (re-)initialized if needed
       # This example assumes backend_ibm is set if the user configured an IBMQ_API_KEY and it was valid at startup
       if 'backend_ibm' not in globals() or backend_ibm is None:
           msg = "IBMQ backend not configured/available. Using local noisy simulator for this action."
           if not os.getenv("IBMQ_API_KEY"):
               msg = "IBMQ_API_KEY not set. Using local noisy simulator."
           print(msg)
           data.ibmq_message = msg
           return self.probabilities_mock(num_shots=num_shots) # Fallback to mock
       try:
           print(f"Attempting to run on IBMQ backend: {backend_ibm.name()}")
           res = self._probabilities_backend(backend_ibm, num_shots=num_shots, result_options={"timeout": secs_timeout, "wait": 2}, transpile_before=True)
           data.ibmq_message = f"Successfully executed on {backend_ibm.name()}."
           return res
       except Exception as e:
           msg = f"IBMQ execution failed (Error: {str(e)[:100]}...). Using local noisy simulator."
           print(f"Error running on IBM Q: {e}")
           data.ibmq_message = msg
           return self.probabilities_mock(num_shots=num_shots) # Fallback to mock
```

## 5. Update HTML for `view_welcome_content`

Locate the cell defining `view_welcome_content = appwidgets.ReactiveHtmlWidget("""...""")`.
*   **Remove Home Connect related cards/sections.**
*   **Add "Explore Quantum Concepts (Examples)" section:** (HTML snippet from previous version of this guide is largely correct, ensure it uses `load_combinatorial_circuit`).
*   **Add "Custom Combinatorial Circuit" card:** (HTML snippet from previous version is correct, ensure `data.view` value matches the key used for the new input view, e.g., `combinatorics_input_view`).

## 6. Create the Parameter Input View (`view_combinatorics_input`)

In a **new code cell**, define this view using `ipywidgets` as detailed in Section 6 of the previous version of this guide (dated approx. 2024-03-15 00:44:56 UTC).
*   Ensure `ipywidgets` like `Dropdown`, `IntText`, `FloatText`, `Textarea`, `Button` are used.
*   Link these widgets to the new `data` traits (e.g., `data.selected_combinatorial_type`, `data.combinatorial_N`, etc.).
*   The "Generate" button should call `generate_and_load_custom_combinatorial_circuit()`.
*   Add this new view to the main `app` widget: `app.add_widget('combinatorics_input_view', view_combinatorics_input)`

## 7. Update UI Elements for Status and Informational Messages

*   **Header for Status Messages (Optional):**
    *   The `network_status_message` and `command_queue_length` traits were removed as they were HC-specific. The JS status bar provides basic browser online/offline. If a Python-driven status line in the header is still desired for other messages (e.g., general app status), a new relevant trait could be used. For a purely offline tool, this might be less critical.
*   **IBMQ Message in Composer View:**
    *   Locate `singleShotComposerCode`. Add the `div` for `${ibmq_message}` as instructed in Section 7 of the previous guide version. This will now primarily show messages related to optional IBMQ execution attempts or errors from circuit generation.
*   **Educational Content Display in Composer View:**
    *   Define `circuit_info_display = appwidgets.ReactiveHtmlWidget(...)` using `data.circuit_info_html` and add it to `view_composer`'s children, as detailed in Section 7 of the previous guide version.

## Final Check

1.  **Restart Kernel & Run All Cells.**
2.  Test all UI interactions for the Quantum Combinatorics Explorer.

This refocused guide aligns with the CHIMera Explorer project's new direction as an offline educational tool.
