# Manual Setup for Qoffee-Maker Notebook UI Enhancements

This guide provides the necessary steps to manually update your `qoffee.ipynb` Jupyter Notebook to enable the full user interface for advanced features developed for the Qoffee-Maker project. These include UI feedback for offline operations, parameterized input for combinatorial quantum circuits, and display of educational content.

**Due to current tooling limitations, these changes cannot be reliably applied programmatically by the automated development agent and require your manual intervention.**

Please apply these changes carefully to the appropriate cells within your `qoffee.ipynb` notebook.

## 1. Add Required Python Imports

In a code cell near the top of `qoffee.ipynb` (typically where you import `ipywidgets`, `appwidgets`, `qiskit`, etc.), ensure the following imports are present:

```python
# Existing imports ...
import requests # For new helper functions to call local APIs
import json     # For new helper functions
import time     # For formatting timestamps or managing UI states
# Ensure the global 'data' widget is defined before functions that use it.

# For Combinatorial Circuits & Status APIs
from qoffeeapi.hc_connector import get_connector
from qoffeeapi.qoffeeapi.combinatorial_circuits import (
    combinatorial_circ_reg,
    generate_binomial_distribution_circuit,
    generate_permutation_circuit_example,
    generate_combination_superposition_circuit,
    generate_custom_permutation_circuit
)
# Ensure other necessary imports like numpy, qiskit, ipywidgets, appwidgets are already there.
```

## 2. Add New Traits to the `data` Widget

Locate the code cell where the global `data` ipywidget is defined (e.g., `data = Widget()`) and its traits are added using `data.add_traits(...)`. You need to add several new traits to this `data` object.

**Carefully insert the following lines inside the `data.add_traits(` call.** Make sure the trait *before* this new block ends with a comma, and the *last trait in this new block* does NOT have a trailing comma if it's immediately followed by the closing parenthesis `)` of `add_traits`.

```python
    # ... (any existing traits like view, heading),
    # ENSURE THE LINE ABOVE THIS BLOCK ENDS WITH A COMMA (if it's not the start of add_traits)

    # For Offline Status & General Messages
    network_status_message = Unicode("Online").tag(sync=True), # General network/health status
    command_queue_length = Int(0).tag(sync=True),         # Number of active Home Connect commands
    ibmq_message = Unicode("").tag(sync=True),            # For IBMQ fallback or execution status messages
    circuit_info_html = Unicode("").tag(sync=True),       # For educational content about circuits

    # Traits for Parameterized Combinatorial Circuits
    combinatorial_N = Int(3).tag(sync=True),              # N qubits/items
    combinatorial_k = Int(2).tag(sync=True),              # k items to choose for Combinations
    combinatorial_p = Float(0.5).tag(sync=True),          # Success probability for Binomial
    combinatorial_pattern = Unicode("0,2,1,3").tag(sync=True), # For custom permutation list, e.g., "0,2,1,3"
    selected_combinatorial_type = Unicode("binomial").tag(sync=True) # To select generator
    # If this is the ABSOLUTE LAST trait before the closing parenthesis of add_traits, remove the trailing comma.
    # Otherwise, if more original traits follow, ensure this last line has a comma.
```

## 3. Add Python Helper Functions to `qoffee.ipynb`

In a suitable code cell (e.g., where other UI helper functions like `load_starting_point` or `get_single_shot_result` are defined), add the following new Python functions. Ensure global variables like `data`, `composer`, `combinatorial_circ_reg`, and `composer_update_handler` are accessible to them (e.g., by declaring `global data, composer` if they are defined in a different cell's scope and not passed as arguments).

```python
# Assumes QOFFEE_API_BASE_URL is defined, e.g., "http://localhost:8887"
# Or replace with dynamic discovery if possible in your notebook environment.
QOFFEE_API_BASE_URL = "http://localhost:8887"

def _get_api_url(api_path):
    from urllib.parse import urljoin
    return urljoin(QOFFEE_API_BASE_URL, api_path)

def update_hc_queue_status_from_api():
    global data
    try:
        api_url = _get_api_url("/api/hc/queue-status")
        response = requests.get(api_url, timeout=5)
        response.raise_for_status()
        status_data = response.json()
        data.command_queue_length = status_data.get("active_queue_length", 0)
        print(f"HC Queue Status Updated via API: Active={data.command_queue_length}, Failed={status_data.get('failed_queue_length', 0)}")
    except Exception as e:
        print(f"Error fetching HC queue status via API: {e}")
        data.command_queue_length = -1

def update_system_health_from_api():
    global data
    try:
        api_url = _get_api_url("/api/health")
        response = requests.get(api_url, timeout=5)
        response.raise_for_status()
        health_data = response.json()

        overall_status = health_data.get("overall_status", "UNKNOWN")
        hc_status = health_data.get("services", {}).get("home_connect_api", {}).get("status", "UNKNOWN")
        hc_msg = health_data.get("services", {}).get("home_connect_api", {}).get("message", "")

        data.network_status_message = f"Health: {overall_status} (HC: {hc_status})"
        if hc_msg and overall_status != "OK":
             data.network_status_message += f" - {hc_msg[:100]}"

        q_data = health_data.get("queues", {})
        data.command_queue_length = q_data.get("active_commands", data.command_queue_length)

        print(f"System Health Updated via API: Overall={overall_status}")
    except Exception as e:
        print(f"Error fetching system health via API: {e}")
        data.network_status_message = "Health: Error fetching status"

def refresh_ui_status_indicators():
    # This function uses the hc_connector directly for potentially more immediate status
    global data
    try:
        connector = get_connector()
        if connector.is_online:
            data.network_status_message = "Online (Connector)"
        else:
            data.network_status_message = "Offline (Connector)"

        queue_summary = connector.get_queue_summary()
        data.command_queue_length = queue_summary.get("active_queue_length", 0)
    except Exception as e:
        print(f"Error refreshing direct UI status indicators: {e}")
        data.network_status_message = "Status Unknown (Connector Error)"
        data.command_queue_length = 0

def load_combinatorial_circuit(circuit_id):
    global data, composer, combinatorial_circ_reg, composer_update_handler, generate_binomial_distribution_circuit, generate_permutation_circuit_example, generate_combination_superposition_circuit, generate_custom_permutation_circuit
    print(f"Attempting to load combinatorial circuit: {circuit_id}")
    data.ibmq_message = ""
    data.circuit_info_html = ""
    try:
        circuit_entry = next(filter(lambda x: x['id'] == circuit_id, combinatorial_circ_reg))
    except StopIteration:
        err_msg = f"Error: Circuit '{circuit_id}' not found."
        print(err_msg)
        data.ibmq_message = err_msg
        return

    try:
        qc = circuit_entry["generator"](**circuit_entry["args"])

        data.composer_init_circuit = {
            "id": circuit_entry["id"], "name": circuit_entry["name"],
            "init_text": circuit_entry.get("description", "")
        }
        data.single_shot_device = 'simulator'
        data.single_shot_status = 0

        composer.circuit = qc
        if 'composer_update_handler' in globals(): # Check if function is defined
             composer_update_handler({'name': 'circuit', 'old': None, 'new': qc, 'owner': composer, 'type': 'change'})

        data.show_mock_results = False
        data.show_qasm_results = False

        current_heading = f"Composer: {circuit_entry['name']}"
        data.heading = current_heading

        title = circuit_entry['name']
        description = circuit_entry.get('description', '')
        args_str = ", ".join([f"{k}={v}" for k,v in circuit_entry['args'].items()])
        specific_details_html = f"<li>Parameters: {args_str}</li>"
        formulas_html = ""
        interpretation_html = ""
        explore_html = ""

        if "binomial" in circuit_entry["id"]:
            N_val = circuit_entry["args"]["num_qubits"]
            p_val = circuit_entry["args"]["success_probability_p"]
            title = f"Binomial Distribution (N={N_val}, p={p_val:.2f})"
            interpretation_html = "<p>Each qubit represents an independent trial. Ry(θ) gates set the success probability 'p' for measuring |1⟩.</p>"
            formulas_html = f"<pre><code>P(k successes) = C(N,k) * p<sup>k</sup> * (1-p)<sup>N-k</sup>\nθ for Ry = 2*arcsin(√p)</code></pre>"
            explore_html = "<li>Vary N and p (using custom generation) to see distribution changes.</li><li>Observe how measurement statistics approach theory with more shots.</li>"
        elif "perm" in circuit_entry["id"]:
            interpretation_html = "<p>This circuit rearranges (permutes) the computational basis states.</p>"
            if "custom" in circuit_entry["id"]:
                 pattern_str = str(circuit_entry["args"]["permutation_list"])
                 formulas_html = f"<pre><code>Input state |i⟩ maps to |P[i]⟩\nPattern P: {pattern_str}</code></pre>"
            else:
                 formulas_html = f"<pre><code>Pattern: {circuit_entry['args']['pattern']}</code></pre><p>Implemented using SWAP gates.</p>"
            explore_html = "<li>Initialize input to a basis state and observe the permuted output.</li><li>Try a superposition input.</li>"
        elif "comb" in circuit_entry["id"]:
            N_val = circuit_entry["args"]["num_qubits_n"]
            k_val = circuit_entry["args"]["num_to_select_k"]
            title = f"Combinations (N={N_val} choose k={k_val})"
            interpretation_html = "<p>Prepares an equal superposition of N-qubit states with Hamming weight 'k' (k ones). Uses qc.initialize().</p>"
            formulas_html = f"<pre><code>Target: (1/√M) * Σ |state_with_k_ones⟩\nM = C(N,k) = N! / (k!(N-k)!)</code></pre>" # C(N,k) is math.comb(N,k)
            explore_html = "<li>Observe that only states with 'k' ones have non-zero probability.</li><li>Change N and k (using custom generation).</li>"

        data.circuit_info_html = f"""<h4>{title}</h4>
                                     <p><strong>Concept:</strong> {description}</p>
                                     <p><strong>Circuit Details:</strong></p>
                                     <ul>{specific_details_html}</ul>
                                     {interpretation_html}
                                     <div><strong>Key Formulas/Representations:</strong> {formulas_html if formulas_html else '<p>N/A</p>'}</div>
                                     <p><strong>Try Exploring:</strong></p>
                                     <ul>{explore_html if explore_html else '<li>Run with many shots.</li>'}</ul>"""
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
        circuit_name = "Custom Combinatorial"
        description = "Custom generated circuit."
        interpretation_html = ""
        formulas_html = ""
        explore_html = "<li>Experiment with different parameters.</li><li>Observe measurement outcomes.</li>"

        if gen_type == "binomial":
            n_val = int(data.combinatorial_N)
            p_val = float(data.combinatorial_p)
            if n_val <= 0 or not (0 <= p_val <= 1):
                data.ibmq_message = "Invalid Binomial params (N > 0, 0 <= p <= 1)."
                return
            qc = generate_binomial_distribution_circuit(n_val, p_val)
            circuit_name = qc.name
            description = f"Models {n_val} independent trials, each with success probability p={p_val:.2f}."
            interpretation_html = "<p>Each qubit uses an Ry gate to set its measurement probability for |1⟩ to 'p'.</p>"
            formulas_html = f"<pre><code>P(k) = C(N,k)p<sup>k</sup>(1-p)<sup>N-k</sup>\nθ for Ry = 2*arcsin(√p)</code></pre>"
        elif gen_type == "combination":
            n_val = int(data.combinatorial_N)
            k_val = int(data.combinatorial_k)
            if k_val < 0 or k_val > n_val or n_val <= 0:
                data.ibmq_message = "Invalid Combination params (N > 0, 0 <= k <= N)."
                return
            qc = generate_combination_superposition_circuit(n_val, k_val)
            circuit_name = qc.name
            description = f"Superposition of states selecting {k_val} of {n_val} items."
            interpretation_html = "<p>Prepares an equal superposition of N-qubit states with Hamming weight 'k'. Uses qc.initialize().</p>"
            formulas_html = f"<pre><code>Target: (1/√M) * Σ |state_with_k_ones⟩\nM = C(N,k) = N! / (k!(N-k)!)</code></pre>"
        elif gen_type == "permutation":
            n_val = int(data.combinatorial_N)
            try:
                pattern_list_str = data.combinatorial_pattern.split(',')
                pattern_list = [int(x.strip()) for x in pattern_list_str]
                qc = generate_custom_permutation_circuit(n_val, pattern_list)
                circuit_name = qc.name
                description = f"Custom permutation for N={n_val} qubits."
                interpretation_html = "<p>Rearranges computational basis states according to the provided list.</p>"
                formulas_html = f"<pre><code>Pattern: {pattern_list}</code></pre>"
            except Exception as e_perm:
                data.ibmq_message = f"Invalid permutation pattern: {e_perm}. Expected e.g., '0,2,1,3' for N=2."
                return
        else:
            data.ibmq_message = f"Unknown combinatorial type: {gen_type}"
            return

        if qc:
            data.composer_init_circuit = {"id": "custom_combinatorial", "name": circuit_name, "init_text": description}
            data.single_shot_device = 'simulator'
            data.single_shot_status = 0
            composer.circuit = qc
            if 'composer_update_handler' in globals(): # Check if function is defined
                composer_update_handler({'name': 'circuit', 'old': None, 'new': qc, 'owner': composer, 'type': 'change'})
            data.show_mock_results = False; data.show_qasm_results = False
            data.heading = f"Composer: {circuit_name}"
            data.circuit_info_html = f"""<h4>{circuit_name}</h4>
                                     <p><strong>Concept:</strong> {description}</p>
                                     {interpretation_html}
                                     <div><strong>Key Formulas/Representations:</strong> {formulas_html if formulas_html else '<p>N/A</p>'}</div>
                                     <p><strong>Try Exploring:</strong></p>
                                     <ul>{explore_html if explore_html else '<li>Run with many shots.</li>'}</ul>"""
            data.view = 'composer'
            print(f"Successfully generated and loaded: {circuit_name}")
        else:
            data.ibmq_message = "Failed to generate the custom circuit (qc is None)."
    except Exception as e:
        err_msg = f"Error generating custom circuit: {str(e)}"
        print(err_msg)
        data.ibmq_message = err_msg
```

## 4. Update `CircuitExecutor.probabilities_ibmq`

Locate this method in `qoffee.ipynb` (it's inside the `CircuitExecutor` class). Ensure it sets `data.ibmq_message` appropriately on success, fallback, or error.

```python
   # Inside class CircuitExecutor:
   def probabilities_ibmq(self, num_shots=1, secs_timeout=30):
       global data
       data.ibmq_message = "" # Clear previous message at the start

       if backend_ibm is None: # Ensure backend_ibm is defined in the notebook scope
           msg = "Real IBM Quantum backend not available/initialized. Using local noisy simulator."
           print(msg)
           data.ibmq_message = msg
           return self.probabilities_mock(num_shots=num_shots)
       try:
           # Optional: Re-check IBMQ account status if needed, though it can be slow.
           # IBMQ.enable_account(os.getenv("IBMQ_API_KEY"))
           # provider = IBMQ.get_provider(hub="ibm-q-community", group="presentations")
           # if not backend_ibm.status().operational: # Example check
           #    raise Exception(f"Backend {backend_ibm.name()} is not operational.")

           print(f"Attempting to run on backend: {backend_ibm.name()}")
           res = self._probabilities_backend(backend_ibm, num_shots=num_shots, result_options={"timeout": secs_timeout, "wait": 2}, transpile_before=True)
           data.ibmq_message = f"Successfully executed on {backend_ibm.name()}." # Or clear if no message on success
           return res
       except Exception as e:
           msg = f"Real device execution failed (Error: {str(e)[:100]}...). Using local noisy simulator."
           print(f"Got error for running on IBM Q: {e}")
           data.ibmq_message = msg
           return self.probabilities_mock(num_shots=num_shots)
```

## 5. Update HTML for `view_welcome_content`

Locate the cell defining `view_welcome_content = appwidgets.ReactiveHtmlWidget("""...""")`.
You need to add two new sections to its HTML string for the Combinatorial Circuits feature.

*   **Add a section for "Explore Quantum Concepts (Examples)":**
    ```html
    <!-- Add this section, e.g., below the "Start with the examples" section -->
    <div class="row mt-4">
        <div class="col-md-12">
            <h4>Explore Quantum Concepts (Examples)</h4>
            <div class="row align-items-stretch">
                <!-- Card for Binomial N=3, p=0.5 -->
                <div class="col-md-3">
                    <div class="card" data-rh-exec="load_combinatorial_circuit('binomial_n3_p0.5')">
                      <div class="card-body">
                        <h5 class="card-title">Binomial (N=3, p=0.5)</h5>
                        <p class="card-text">3 qubits, 50% success prob.</p>
                        <span class="arrow">→</span>
                      </div>
                    </div>
                </div>
                <!-- Card for 2Q Permutation -->
                <div class="col-md-3">
                    <div class="card" data-rh-exec="load_combinatorial_circuit('perm_custom_2q_0213')">
                      <div class="card-body">
                        <h5 class="card-title">2Q Permutation ([0,2,1,3])</h5>
                        <p class="card-text">Maps |01>↔|10>.</p>
                        <span class="arrow">→</span>
                      </div>
                    </div>
                </div>
                 <!-- Card for Combinations N=3, k=2 -->
                <div class="col-md-3">
                    <div class="card" data-rh-exec="load_combinatorial_circuit('comb_n3_k2')">
                      <div class="card-body">
                        <h5 class="card-title">Combinations (N=3, k=2)</h5>
                        <p class="card-text">Superposition of choosing 2 of 3.</p>
                        <span class="arrow">→</span>
                      </div>
                    </div>
                </div>
                <!-- Add more cards here for other examples from combinatorial_circ_reg in combinatorial_circuits.py -->
            </div>
        </div>
    </div>
    ```
*   **Add a Card for "Custom Combinatorial Circuit" (to navigate to the parameter input view):**
    ```html
    <!-- Add this card, perhaps in the "Quantum Concepts" section or near "Start the Qoffee Maker" -->
    <div class="col-md-3">
        <div class="card card-primary" data-rh-exec="lambda: setattr(data, 'view', 'combinatorics_input_view')">
          <div class="card-body">
            <h5 class="card-title">Custom Combinatorial Circuit</h5>
            <p class="card-text">Generate circuits with your parameters.</p>
            <span class="arrow">→</span>
          </div>
        </div>
    </div>
    ```

## 6. Create the Parameter Input View (`view_combinatorics_input`)

In a **new code cell** in `qoffee.ipynb`, define this view using `ipywidgets`. This view will allow users to specify parameters for custom combinatorial circuits.

```python
from ipywidgets import Dropdown, IntText, FloatText, Button, VBox, HBox, Label, Textarea, link
# Ensure appwidgets is imported if using ReactiveHtmlWidget for parts of this view, e.g. for param_message_area.
# import appwidgets

# --- Define Input Widgets ---
combo_type_dropdown = Dropdown(
    options=[
        ("Binomial Distribution", "binomial"),
        ("Combinations (N choose k)", "combination"),
        ("Custom Permutation", "permutation")
    ],
    value=data.selected_combinatorial_type, # Assumes data.selected_combinatorial_type is initialized
    description="Circuit Type:",
    style={'description_width': 'initial'}
)

n_input = IntText(
    value=data.combinatorial_N,
    description="N (qubits):",
    style={'description_width': 'initial'},
    layout={'width': '250px'}
)
k_input = IntText(
    value=data.combinatorial_k,
    description="k (items to choose):",
    style={'description_width': 'initial'},
    layout={'width': '250px'}
)
p_input = FloatText(
    value=data.combinatorial_p,
    step=0.01, min=0, max=1,
    description="p (success probability):",
    style={'description_width': 'initial'},
    layout={'width': '250px'}
)
pattern_input = Textarea(
    value=data.combinatorial_pattern,
    placeholder="e.g., 0,1,3,2 for N=2",
    description="Permutation List (comma-separated):",
    style={'description_width': 'initial'},
    layout={'width': '280px', 'height':'60px'} # Adjusted width
)

generate_button = Button(description="Generate and Load Circuit", button_style='primary', icon='cogs')
back_button_combinatorics = Button(description="Back to Welcome", icon='arrow-left')

# --- Link Widgets to data Traits ---
link((combo_type_dropdown, 'value'), (data, 'selected_combinatorial_type'))
link((n_input, 'value'), (data, 'combinatorial_N'))
link((k_input, 'value'), (data, 'combinatorial_k'))
link((p_input, 'value'), (data, 'combinatorial_p'))
link((pattern_input, 'value'), (data, 'combinatorial_pattern'))

# --- Define Visibility Logic for Parameter Inputs ---
def on_combo_type_change_for_param_view(change):
    is_binomial = data.selected_combinatorial_type == "binomial" # Use data trait directly
    is_combination = data.selected_combinatorial_type == "combination"
    is_permutation = data.selected_combinatorial_type == "permutation"

    k_input.layout.display = 'flex' if is_combination else 'none'
    p_input.layout.display = 'flex' if is_binomial else 'none'
    pattern_input.layout.display = 'flex' if is_permutation else 'none'

    n_input.description = "N (qubits):"
    if is_binomial: n_input.description = "N (trials/qubits):"
    if is_combination: n_input.description = "N (total items/qubits):"
    if is_permutation: n_input.description = "N (qubits for permutation):"

combo_type_dropdown.observe(on_combo_type_change_for_param_view, names='value')
# Call once to set initial visibility
on_combo_type_change_for_param_view({'new': data.selected_combinatorial_type})

# --- Define Button Actions ---
def on_generate_button_clicked_for_param_view(b):
    if 'generate_and_load_custom_combinatorial_circuit' in globals():
        generate_and_load_custom_combinatorial_circuit()

generate_button.on_click(on_generate_button_clicked_for_param_view)

def on_back_button_combinatorics_clicked_for_param_view(b):
    if 'load_welcome' in globals(): # Ensure load_welcome is defined and accessible
        load_welcome()
    data.ibmq_message = "" # Clear any messages

back_button_combinatorics.on_click(on_back_button_combinatorics_clicked_for_param_view)

param_message_area = appwidgets.ReactiveHtmlWidget("""
    <div data-rh-if="${ibmq_message}" style="color: red; margin-top:10px; padding: 5px; border: 1px solid #ffbaba; background-color: #ffebeb; border-radius: 3px;">
        <strong>Error:</strong> ${ibmq_message}
    </div>
""", data_model=data)

# --- Assemble the View ---
# This creates a VBox containing all elements for the custom circuit generation view.
view_combinatorics_input_title = appwidgets.ReactiveHtmlWidget("""<h3>Generate Custom Combinatorial Circuit</h3><hr>""")

input_layout = VBox([
    combo_type_dropdown,
    n_input,
    k_input,
    p_input,
    pattern_input
], layout={'margin_bottom': '10px'})

button_layout = HBox([generate_button, back_button_combinatorics], layout={'margin_top': '10px'})

view_combinatorics_input = VBox([
    view_combinatorics_input_title,
    input_layout,
    button_layout,
    param_message_area
], layout={'padding': '15px', 'border': '1px solid #ddd', 'border_radius': '5px', 'background_color': '#f9f9f9'})

# --- Add this new view to the app ---
# In the cell where app.add_widget is called (e.g., after app.add_widget('composer', view_composer)):
# Make sure 'app' is your AppBox instance.
# app.add_widget('combinatorics_input_view', view_combinatorics_input)
```
**Important:** After defining `view_combinatorics_input`, you must add it to your main `app` object. Find the cell where you have `app.add_widget(...)` calls (e.g., `app.add_widget('welcome', view_welcome)`) and add:
```python
app.add_widget('combinatorics_input_view', view_combinatorics_input)
```

## 7. Update UI Elements for Status and Informational Messages

*   **Header for Network Status & Queue Length:**
    Locate the cell defining `header = appwidgets.ReactiveHtmlWidget("""...""")`. Modify its HTML string to include a status display area. For example, inside the main `<div id="header">`:
    ```html
    <!-- Inside <div id="header">, perhaps before #navigation-container -->
    <div id="status-indicators" style="position: absolute; right: 200px; top: 5px; color: white; font-size: 0.75em; text-align: right; line-height: 1.2;">
        <p style="margin: 0; padding: 1px 0;" data-rh-if="${network_status_message}">${network_status_message}</p>
        <p style="margin: 0; padding: 1px 0;" data-rh-if="${command_queue_length} > 0">Queued HC: ${command_queue_length}</p>
    </div>
    ```
    *To populate these, ensure one of the status update functions (e.g., `refresh_ui_status_indicators()` or `update_system_health_from_api()`) is called, for example, after `load_welcome()` or `load_starting_point()` or via a dedicated refresh button you might add.*

*   **IBMQ Fallback/Status Message in Composer View:**
    Locate the `singleShotComposerCode` multiline string variable (used to define `view_composer_singleshot`). Inside its main `div` (e.g., `<div id="view-composer-singleshot">`), add a placeholder for the message:
    ```html
    <!-- e.g., just above the "Determine your beverage" button -->
    <div data-rh-if="${ibmq_message}" style="color: #856404; background-color: #fff3cd; border: 1px solid #ffeeba; padding: .3rem .75rem; margin-bottom: 10px; border-radius: .25rem; font-size:0.9em;">
        ${ibmq_message}
    </div>
    ```
    *Ensure the `CircuitExecutor.probabilities_ibmq` function in the notebook is updated to set `data.ibmq_message` as per step #4.*

*   **Educational Content Display in Composer View:**
    Locate where `view_composer`'s children are defined. This is typically a `VBox` containing elements like `view_composer_intro`, `composer`, and an `HBox` for histograms/single-shot.
    First, define the widget for displaying the educational content in a cell:
    ```python
    circuit_info_display = appwidgets.ReactiveHtmlWidget("""
        <div data-rh-if="${circuit_info_html}" style="margin-top: 20px; padding: 15px; border: 1px solid #e0e0e0; border-radius: 4px; background-color: #f9f9f9;">
            <h4 style="margin-top:0; margin-bottom:10px; border-bottom: 1px solid #eee; padding-bottom:5px;">About this Circuit:</h4>
            <div>${circuit_info_html}</div>
        </div>
    """, data_model=data)
    ```
    Then, add `circuit_info_display` to the list of children for the main content `VBox` within `view_composer`.
    For example, if your composer view's content is structured like:
    `view_composer_content_elements = [view_composer_intro, composer, HBox_of_hist_and_singleshot]`
    You would change it to:
    `view_composer_content_elements = [view_composer_intro, composer, HBox_of_hist_and_singleshot, circuit_info_display]`
    And then use this updated list when creating the `VBox` for `view_composer`.

## Final Check

After making all these changes:
1.  **Restart the Kernel** of your `qoffee.ipynb` notebook.
2.  **Run All Cells** to ensure all definitions and UI elements are loaded correctly.
3.  Test the new UI elements and functionalities.

This guide should help you enable the advanced UI features in your Qoffee-Maker notebook.
