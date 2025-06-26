# Qoffee-Maker

<img src="css/QoffeeMug.png">

## User Instructions

Find user instructions on the project GitHub pages: http://qoffee-maker.org

## Installation

As an example, we will install the Qoffee Maker Graphical User Interface (GUI) to be accessed under `https://localhost:8887`. It is also possible to choose another URL that you want to access the GUI from.
### Prerequisites

- Home Connect enabled coffee machine
- Android Phone or iPhone
- Computer
- Email address you will use to register with Home Connect


### Install Home Connect
1. Install the Home Connect [iOS App](https://app.adjust.com/gdi5c03?campaign=germany&redirect_macos=https%3A%2F%2Fapps.apple.com%2Fde%2Fapp%2Fhome-connect-app%2Fid901397789&redirect_windows=https%3A%2F%2Fapps.apple.com%2Fde%2Fapp%2Fhome-connect-app%2Fid901397789) or [Android App](https://app.adjust.com/gdi5c03?campaign=germany&redirect_macos=https%3A%2F%2Fplay.google.com%2Fstore%2Fapps%2Fdetails%3Fid%3Dcom.bshg.homeconnect.android.release%26hl%3Dde&redirect_windows=https%3A%2F%2Fplay.google.com%2Fstore%2Fapps%2Fdetails%3Fid%3Dcom.bshg.homeconnect.android.release%26hl%3Dde)

2. In the App Connect mobile app, you need to sign in with a Home Connect User Account.

After starting the app, the welcome screen will show the option to log in to the app or register a new user.

If you have not used the "Home Connect" app before follow these steps on how to create an account:

- Click on the Register link as shown in the picture below.

<p align="center">
<img src="css/HomeConnect_app_home_screen.png" width="300">
</p>

- Use your email address to register new user. Provide a new password as requested on the form:

<p align="center">
<img src="css/HomeConnect_app_user_registration.png" width="300">
</p>

- Then, press "Continue" link on the top-right corner.

- Read "Terms and Condition" rules, and accept it by checking "I have read and accept the terms of use" checkbox, then press "Continue" button.

- Once again, read "Data protection statement" and accept it by checking "I have read and accept the data protection statement" checkbox. Press "Continue" button to proceed.

- Read the statements regarding collecting user data and accept it by clicking "I consent to the collection of mu user data" checkbox. Press "Continue" button to finish procedure.

- Review the provided information and click "Send" button.

- Now, you have to activate the registered account. To confirm the account you must click the link in the activation email that you will receive in your mailbox.

- Now, you confirm your email address, your account will be activated and you can log in to the Home Connect app using your newly registered user.

3. Add your Coffee Machine appliance to the Home Connect App

You can connect your Coffee Machine under _Appliances_ in the App.

4. [Sign up for a Home Connect Developer Account](https://developer.home-connect.com/user/register)

Make sure to set your _Default Home Connect User Account for Testing_ to the Home Connect User Account (mail address) used in the previous step.

Hint: It is not crucial to provide meaningful _Additional Information_.

5. [Register a new Home Connect Appliance](https://developer.home-connect.com/applications/add)

Set an _Application ID_ of your choice. Using localhost, the _Redirect URI_ is set to `http://localhost:8887/auth/callback`. Keep the default settings for the remaining boxes and create the appliance.

### Install the Qoffee Maker GUI
Install the Qoffee Maker GUI by following these steps:

1. **Set up Environment Variables:**
   Copy the `env-template` file to a new file named `.env` in the root of the project:
   ```bash
   cp env-template .env
   ```
   Then, edit the `.env` file and fill in your specific values for the following variables:
    - `HOMECONNECT_API_URL`: Use `https://api.home-connect.com/` for a real device or `https://simulator.home-connect.com/` for the simulator.
    - `HOMECONNECT_CLIENT_ID`: Your Client ID from your registered Home Connect application.
    - `HOMECONNECT_CLIENT_SECRET`: Your Client Secret from your registered Home Connect application.
    - `HOMECONNECT_REDIRECT_URL`: Callback URL for HomeConnect as registered in your application in HomeConnect. On localhost this is `http://localhost:8887/auth/callback` (the port is determined by Jupyter, `/auth/callback` is fixed)
    - `DEVICE_HA_ID`: This is the HomeConnect Appliance ID (HA ID) of your coffee machine. It is useful when you have multiple coffee machines registered in your Home Connect App. Leave it blank if you don't want to set it/don't know about it.
      - To get the HA IDs of your available machines start the QoffeeMaker, authenticate and then, type http://{YOUR_IP_ADRESS}:8887/machines into your browser. You will get an response with all your appliances and HA IDs.
    - `IBMQ_API_KEY`: the API Key for [IBM Quantum](https://quantum-computing.ibm.com/account)

2. Run the container image with the specified environment variables: `docker run --name qoffee --rm -itp 8887:8887 --env-file .env ghcr.io/janlahmann/qoffee-maker`

3. Now you can start using the Qoffee Maker GUI under http://localhost:8887 (the login token is shown in the StdOut of the docker container). After logging in to Jupyter, you have to select _qoffee.ipynb_ and then you have to click the rocket icon to _Activate App Mode_.

Enjoy your Quantum Coffee. ☕️

## New Features & Capabilities

This version of Qoffee-Maker includes significant enhancements for offline operation and new educational features for exploring quantum concepts.

### Offline Capabilities

The Qoffee-Maker can now handle periods of internet disconnection more gracefully, particularly for Home Connect functionalities:

*   **Data Caching:** Information about your Home Connect appliances (list of machines, their status, and settings) is cached locally. If you are offline, the application will attempt to show you the most recently fetched data, indicating that it's cached and when it was last updated.
*   **Command Queuing:** If you try to perform actions like turning on your coffee machine or requesting a drink while offline, these commands will be automatically queued.
*   **Automatic Processing:** When an internet connection is restored, the application will attempt to process any queued commands.
*   **Retry Mechanism:** Queued commands that fail due to temporary issues (other than being offline) will be retried up to 3 times.
*   **Failed Commands:** Commands that persistently fail will be moved to a "failed commands queue."
    *   You can view the status of these queues via the API endpoint: `GET /api/hc/queue-status`.
    *   Failed commands can be managed (retried or deleted) via API endpoints:
        *   `POST /api/hc/retry-failed-command` (Body: `{"command_index": index}`)
        *   `POST /api/hc/delete-failed-command` (Body: `{"command_index": index}`)
    *   (Future UI enhancements may provide easier management of these queues).
*   **IBMQ Execution:** If you attempt to run a circuit on a real IBM Quantum device while offline, the system will automatically fall back to using a local noisy simulator. The "Export to IBM Quantum Composer" feature now bundles necessary libraries to generate QR codes offline, though accessing the IBM Quantum website itself still requires internet.
*   **Status Bar:** A global status bar at the bottom of the UI provides basic feedback on network status and queued/failed command counts.

### Combinatorial Quantum Circuits Feature

Explore fundamental quantum representations of combinatorial concepts:

*   **Binomial Distribution:** Generate circuits where qubit measurement probabilities follow a binomial distribution B(N, p).
    *   Examples: "Binomial (N=3, p=0.5)", "Binomial (N=4, p=0.25)"
*   **Permutations:**
    *   Simple examples like swapping qubit states (e.g., "2-Qubit SWAP(0,1)", "3-Qubit Cycle (0->1->2)").
    *   Generate circuits for custom permutations of basis states (e.g., "2Q Permutation ([0,2,1,3])").
*   **Combinations (N choose k):** Generate circuits that prepare an equal superposition of all basis states representing the selection of 'k' items from 'N'.
    *   Examples: "Combinations (N=3, k=2)", "Combinations (N=4, k=1)"

These features require manual UI setup in `qoffee.ipynb` as detailed below.

## Manual UI Setup for Advanced Features (Required)

Due to limitations in programmatically modifying Jupyter Notebooks reliably with current automated tools, several UI enhancements for offline feedback and the new Combinatorial Circuits feature require manual edits to the `qoffee.ipynb` file.

**Please follow these steps carefully after pulling the latest code changes:**

**1. Add Python Imports:**
   In a code cell near the top of `qoffee.ipynb` (e.g., where `appwidgets` or `qiskit` are imported), add:
   ```python
   from qoffeeapi.qoffeeapi.combinatorial_circuits import combinatorial_circ_reg, generate_binomial_distribution_circuit, generate_permutation_circuit_example, generate_combination_superposition_circuit, generate_custom_permutation_circuit
   import time # For formatting timestamps if needed in UI
   from qoffeeapi.hc_connector import get_connector # To get live connector status
   ```

**2. Add New `data` Widget Traits:**
   Locate the cell defining `data = Widget()` and `data.add_traits(...)`. Add the following new traits inside the `data.add_traits(` call, ensuring commas are correctly placed:
   ```python
   # ... (any existing traits like view, heading), ensure the one above this block has a comma.
   network_status_message = Unicode("Online").tag(sync=True),
   command_queue_length = Int(0).tag(sync=True),
   ibmq_message = Unicode("").tag(sync=True), # For IBMQ fallback/status messages
   circuit_info_html = Unicode("").tag(sync=True), # For educational content

   # Traits for parameterized combinatorial circuits
   combinatorial_N = Int(3).tag(sync=True),
   combinatorial_k = Int(2).tag(sync=True),
   combinatorial_p = Float(0.5).tag(sync=True),
   combinatorial_pattern = Unicode("SWAP_01").tag(sync=True), # Default or example pattern
   selected_combinatorial_type = Unicode("binomial").tag(sync=True)
   # Ensure the last trait in this list does NOT have a trailing comma if it's just before the closing parenthesis ')'
   ```

**3. Add Python Helper Functions:**
   In a suitable code cell (e.g., where `load_starting_point` or `get_single_shot_result` are defined), add the following Python functions:

   ```python
   def refresh_ui_status_indicators():
       global data # Ensure 'data' is accessible if not passed as arg
       try:
           connector = get_connector()
           if connector.is_online:
               data.network_status_message = "Online"
           else:
               # Using time.time() for last check might be complex to wire up here
               # For simplicity, just "Offline". Python side hc_connector prints more details.
               data.network_status_message = "Offline (HC API)"

           queue_summary = connector.get_queue_summary()
           data.command_queue_length = queue_summary.get("active_queue_length", 0)
           # You could add another data trait for failed_queue_length if desired
       except Exception as e:
           print(f"Error refreshing UI status indicators: {e}")
           data.network_status_message = "Status Unknown"
           data.command_queue_length = 0

   # Call it once to initialize, and potentially periodically if a mechanism is set up
   # For now, user might need to re-run this cell or it's called by other actions.
   # refresh_ui_status_indicators() # Call once, or integrate into other app flows.

   def load_combinatorial_circuit(circuit_id):
       global data, composer, combinatorial_circ_reg, composer_update_handler # Ensure access
       print(f"Attempting to load combinatorial circuit: {circuit_id}")
       data.ibmq_message = "" # Clear previous messages
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
           composer_update_handler({'name': 'circuit', 'old': None, 'new': qc, 'owner': composer, 'type': 'change'})

           data.show_mock_results = False
           data.show_qasm_results = False

           data.heading = f"Composer: {circuit_entry['name']}"
           # Populate educational content (example for binomial)
           if "binomial" in circuit_entry["id"]:
               N = circuit_entry["args"]["num_qubits"]
               p = circuit_entry["args"]["success_probability_p"]
               data.circuit_info_html = f"""<h4>Binomial Distribution (N={N}, p={p:.2f})</h4>
                                         <p>Models {N} trials, success prob. p={p:.2f}.</p>
                                         <p>P(k) = C(N,k) p<sup>k</sup> (1-p)<sup>N-k</sup></p>"""
           elif "perm" in circuit_entry["id"]:
                data.circuit_info_html = f"""<h4>Permutation Circuit: {circuit_entry['name']}</h4>
                                         <p>{circuit_entry.get('description', '')}</p>"""
           elif "comb" in circuit_entry["id"]:
                N = circuit_entry["args"]["num_qubits_n"]
                k = circuit_entry["args"]["num_to_select_k"]
                data.circuit_info_html = f"""<h4>Combinations (N={N} choose k={k})</h4>
                                         <p>Superposition of states selecting {k} of {N} items.</p>
                                         <p>Total states: C(N,k) = N! / (k!(N-k)!)</p>"""

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

           if gen_type == "binomial":
               n_val = int(data.combinatorial_N)
               p_val = float(data.combinatorial_p)
               if n_val <= 0 or not (0 <= p_val <= 1):
                   data.ibmq_message = "Invalid Binomial params (N > 0, 0 <= p <= 1)."
                   return
               qc = generate_binomial_distribution_circuit(n_val, p_val)
               circuit_name = qc.name
               data.circuit_info_html = f"<h4>Binomial Distribution (N={n_val}, p={p_val:.2f})</h4><p>See description for pre-defined binomial circuits.</p>"
           elif gen_type == "combination":
               n_val = int(data.combinatorial_N)
               k_val = int(data.combinatorial_k)
               if k_val < 0 or k_val > n_val or n_val <= 0:
                   data.ibmq_message = "Invalid Combination params (N > 0, 0 <= k <= N)."
                   return
               qc = generate_combination_superposition_circuit(n_val, k_val)
               circuit_name = qc.name
               data.circuit_info_html = f"<h4>Combinations (N={n_val} choose k={k_val})</h4><p>See description for pre-defined combination circuits.</p>"
           elif gen_type == "permutation":
               n_val = int(data.combinatorial_N)
               # Basic validation, assumes pattern is a comma-separated list of ints for custom perm
               try:
                   pattern_list = [int(x.strip()) for x in data.combinatorial_pattern.split(',')]
                   qc = generate_custom_permutation_circuit(n_val, pattern_list)
                   circuit_name = qc.name
                   data.circuit_info_html = f"<h4>Custom Permutation N={n_val}</h4><p>Pattern: {data.combinatorial_pattern}</p>"
               except Exception as e_perm:
                   data.ibmq_message = f"Invalid permutation pattern: {e_perm}. Expected e.g., '0,2,1,3' for N=2."
                   return
           else:
               data.ibmq_message = f"Unknown combinatorial type: {gen_type}"
               return

           if qc:
               data.composer_init_circuit = {"id": "custom_combinatorial", "name": circuit_name, "init_text": "Custom generated circuit."}
               data.single_shot_device = 'simulator'
               data.single_shot_status = 0
               composer.circuit = qc
               composer_update_handler({'name': 'circuit', 'old': None, 'new': qc, 'owner': composer, 'type': 'change'})
               data.show_mock_results = False; data.show_qasm_results = False
               data.heading = f"Composer: {circuit_name}"
               data.view = 'composer'
               print(f"Successfully generated and loaded: {circuit_name}")
           else:
               data.ibmq_message = "Failed to generate the custom circuit."
       except Exception as e:
           err_msg = f"Error generating custom circuit: {str(e)}"
           print(err_msg)
           data.ibmq_message = err_msg
   ```

**4. Update `view_welcome_content` HTML:**
   Locate the cell defining `view_welcome_content = appwidgets.ReactiveHtmlWidget("""...""")`.
   You need to add two new sections to its HTML string.
   *   **Section for Combinatorial Circuit Examples:**
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
                 <!-- Add more cards here for other examples from combinatorial_circ_reg -->
             </div>
         </div>
     </div>
     ```
   *   **Card for Parameterized Combinatorial Input View:**
     ```html
     <!-- Add this card, perhaps alongside the "Start the Qoffee Maker" card or in the new "Quantum Concepts" section -->
     <div class="col-md-3"> <!-- Adjust size as needed -->
         <div class="card card-primary" data-rh-exec="lambda: setattr(data, 'view', 'combinatorics_input_view')">
           <div class="card-body">
             <h5 class="card-title">Custom Combinatorial Circuit</h5>
             <p class="card-text">Generate circuits with your parameters.</p>
             <span class="arrow">→</span>
           </div>
         </div>
     </div>
     ```

**5. Create the Parameter Input View (`view_combinatorics_input`):**
   This is a new view. In a new code cell, define it using `ipywidgets` and `ReactiveHtmlWidget` for layout if preferred.
   ```python
   from ipywidgets import Dropdown, IntText, FloatText, Button, VBox, HBox, Label, Accordion, Textarea

   # --- Define Input Widgets ---
   combo_type_dropdown = Dropdown(options=[
       ("Binomial Distribution", "binomial"),
       ("Combinations (N choose k)", "combination"),
       ("Custom Permutation", "permutation")
   ], description="Circuit Type:")

   n_input = IntText(value=3, description="N (qubits):", style={'description_width': 'initial'}, layout={'width': '200px'})
   k_input = IntText(value=2, description="k (to choose):", style={'description_width': 'initial'}, layout={'width': '200px'})
   p_input = FloatText(value=0.5, step=0.01, description="p (prob):", style={'description_width': 'initial'}, layout={'width': '200px'})
   # For permutation_list, using a Textarea is more flexible than trying to parse complex structures
   pattern_input = Textarea(value="0,2,1,3", placeholder="e.g., 0,2,1,3 for N=2", description="Permutation List (comma-separated indices):", style={'description_width': 'initial'})

   generate_button = Button(description="Generate and Load Circuit", button_style='primary')
   back_button_combinatorics = Button(description="Back to Welcome")

   # --- Link Widgets to data Traits ---
   widgets.link((combo_type_dropdown, 'value'), (data, 'selected_combinatorial_type'))
   widgets.link((n_input, 'value'), (data, 'combinatorial_N'))
   widgets.link((k_input, 'value'), (data, 'combinatorial_k'))
   widgets.link((p_input, 'value'), (data, 'combinatorial_p'))
   widgets.link((pattern_input, 'value'), (data, 'combinatorial_pattern'))

   # --- Define Visibility Logic (can be done with observe or within ReactiveHTML if preferred) ---
   # This is simpler to manage with Python observers for ipywidgets
   def on_combo_type_change(change):
       show_binomial = change.new == "binomial"
       show_combination = change.new == "combination"
       show_permutation = change.new == "permutation"

       k_input.layout.display = 'flex' if show_combination else 'none'
       p_input.layout.display = 'flex' if show_binomial else 'none'
       pattern_input.layout.display = 'flex' if show_permutation else 'none'
       # N is used by all, so always visible or adjust as needed
       n_input.description = "N (qubits):"
       if show_binomial: n_input.description = "N (trials/qubits):"
       if show_combination: n_input.description = "N (total items):"

   combo_type_dropdown.observe(on_combo_type_change, names='value')
   on_combo_type_change({'new': data.selected_combinatorial_type}) # Initial setup

   # --- Define Button Actions ---
   def on_generate_button_clicked(b):
       generate_and_load_custom_combinatorial_circuit()

   generate_button.on_click(on_generate_button_clicked)

   def on_back_button_combinatorics_clicked(b):
       load_welcome() # Assumes load_welcome() is defined
       data.ibmq_message = "" # Clear message when going back

   back_button_combinatorics.on_click(on_back_button_combinatorics_clicked)

   # --- Message Area ---
   # This uses ReactiveHtmlWidget for simplicity in showing the conditional message
   # This could also be an ipywidgets.HTML widget updated by an observer on data.ibmq_message
   param_message_area = appwidgets.ReactiveHtmlWidget("""
       <p data-rh-if="${ibmq_message}" style="color: red; margin-top:10px;">${ibmq_message}</p>
   """, data_model=data)

   # --- Assemble the View ---
   # Basic VBox layout
   input_widgets_box = VBox([
       combo_type_dropdown,
       n_input,
       k_input,
       p_input,
       pattern_input,
       generate_button,
       back_button_combinatorics,
       param_message_area
   ])

   # Using a ReactiveHtmlWidget for the overall title/container is also an option
   view_combinatorics_input_container = appwidgets.ReactiveHtmlWidget("""
       <div id="view-combinatorics-input" class="app-view-content">
           <h3>Generate Custom Combinatorial Circuit</h3>
           <!-- The VBox above will be a child of this overall view -->
       </div>
   """, data_model=data)

   view_combinatorics_input = VBox([view_combinatorics_input_container, input_widgets_box])

   # --- Add to App ---
   # In the cell where app.add_widget is called:
   # app.add_widget('combinatorics_input_view', view_combinatorics_input)
   ```
   **Note:** The `data-rh-set-val` attributes from the earlier conceptual HTML for inputs are replaced by direct `ipywidgets` linking to `data` traits, which is more robust for `ipywidgets`.

**6. Update Header and Other UI for Status Messages:**
   *   **Header:**
     Locate `header = appwidgets.ReactiveHtmlWidget(...)`. Modify its HTML to include:
     ```html
     <div id="status-indicators" style="position: absolute; right: 210px; top: 5px; color: white; font-size: 0.75em; text-align: right; line-height: 1.2;">
         <p style="margin: 0;" data-rh-if="${network_status_message}">${network_status_message}</p>
         <p style="margin: 0;" data-rh-if="${command_queue_length} > 0">Queued: ${command_queue_length}</p>
     </div>
     ```
     (Adjust styling/positioning as needed). Remember to call `refresh_ui_status_indicators()` to update these.
   *   **IBMQ Fallback Message in Composer Single Shot View:**
     Locate `singleShotComposerCode = """..."""`. Inside the `<div id="view-composer-singleshot">`, before or after the result display, add:
     ```html
     <div data-rh-if="${ibmq_message}" style="color: orange; font-size: 0.9em; margin-top: 5px; padding: 5px; background-color: #fff3cd; border: 1px solid #ffeeba; border-radius: 3px;">
         ${ibmq_message}
     </div>
     ```
     Ensure `CircuitExecutor.probabilities_ibmq` (in `qoffee.ipynb`) is manually updated to set `data.ibmq_message` on success, fallback, or error.
   *   **Educational Content Display in Composer View:**
     Locate `view_composer = VBox([...])`. Inside the main `VBox` that forms the content of the composer view (e.g., after the `HBox` containing histogram and single shot), add an `Accordion` or an `appwidgets.ReactiveHtmlWidget` to display `data.circuit_info_html`.
     ```python
     # Example with ReactiveHtmlWidget (simpler for basic HTML):
     circuit_info_display = appwidgets.ReactiveHtmlWidget("""
         <div data-rh-if="${circuit_info_html}" style="margin-top: 15px; padding: 10px; border: 1px solid #ccc; border-radius: 4px;">
             <h4>About this Circuit:</h4>
             <div>${circuit_info_html}</div>
         </div>
     """, data_model=data)

     # Then add circuit_info_display to the children of view_composer's main content VBox.
     # Example: view_composer_content_vbox.children = list(view_composer_content_vbox.children) + [circuit_info_display]
     ```

This completes the documentation task.

## Installation on RasQberry (draft):

Installation and startup of Qoffee-Maker has been fully integrated to the RasQberry automated setup. (Currently in branch "dev8", but will be merged to master soon.)

In rasqberry-config (started with `$ . ./RasQ-init.sh dev9`), use the following menu items in "D Quantum Demos" to run the locally build docker image or the image available on dockerhub: "QM Qoffee-Maker", "QMd Qoffee-Maker".

To trigger a rebuild, choose "A Advanced Config" -> "QMrb Qoffee-Maker rebuild".

To stop all qoffee containers, select "A Advanced Config" -> "QMst stop Qoffee-Maker".

The two versions of the demo can also be started using the "Qoffee Maker" desktop icons.

