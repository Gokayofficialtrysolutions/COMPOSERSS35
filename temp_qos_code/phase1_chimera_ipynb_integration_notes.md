# CHIMera QOS Phase 1 - `chimera.ipynb` Integration Notes

This document outlines the necessary modifications and additions to `chimera.ipynb` to integrate the Phase 1 QOS stack (AES, QLCS, simplified RMS, PTSS_Stub, SACS_Stub, basic SHMS logger) using the `ChimeraQOSClient` SDK.

## I. Setup and Initialization Cell(s)

1.  **Import Necessary QOS Components:**
    *   Add a new code cell early in the notebook (e.g., after initial Qiskit/numpy imports).
    *   This cell will import all required QOS service classes/stubs and the SDK.
    ```python
    # --- CHIMera QOS Phase 1 Stack Initialization ---
    print("Importing CHIMera QOS Phase 1 components...")
    import sys
    import os
    # Assuming 'temp_qos_code' is in the same directory or PYTHONPATH is set
    # For robust imports if temp_qos_code is a subdir of notebook's dir:
    # module_path = os.path.abspath(os.path.join('.', 'temp_qos_code'))
    # if module_path not in sys.path:
    #     sys.path.append(module_path)

    try:
        from phase0_qhal import QHALService, SimulatedQPU_Driver
        from phase0_pecs import PECS, SimulatedTemperatureController # If PECS interaction is desired
        from phase0_ptss_stub import PTSS_Stub, OperationSequence, LogicalOperation, OperationPriority, GateType # GateType might be from qhal
        from phase1_qlcs_aes import QLCSService, AESService, ExperimentJob, QubitRequirement, QHALTranspiledSequence
        from phase1_rms_simplified import RMS_Phase1_Simulated, QubitState, TrackedQubitInfo
        from phase1_sacs_stub import SACS_Stub_Phase1, UserCredentials, SecurityToken, TokenIntrospectionResponse, AuthorizationRequest
        from common_logger import get_qos_logger # Assuming common_logger.py is created
        from phase1_sdk import ChimeraQOSClient
        print("QOS components imported successfully.")
    except ImportError as e:
        print(f"ERROR importing QOS components: {e}")
        print("Please ensure all temp_qos_code/*.py files are accessible.")
        # Potentially raise the error to stop notebook execution if QOS is critical path
    ```

2.  **Instantiate and Wire QOS Services:**
    *   In the same cell or a subsequent one, instantiate all services and the SDK client.
    ```python
    print("Instantiating CHIMera QOS Phase 1 stack (simulated)...")

    # Basic Loggers for each service
    qhal_logger = get_qos_logger("QHALService_nb")
    pecs_logger = get_qos_logger("PECS_nb") # if PECS is actively used
    ptss_logger = get_qos_logger("PTSS_Stub_nb")
    rms_logger = get_qos_logger("RMS_Phase1_nb")
    qlcs_logger = get_qos_logger("QLCS_Phase1_nb")
    aes_logger = get_qos_logger("AES_Phase1_nb")
    sacs_logger = get_qos_logger("SACS_Stub_nb")

    # Instantiate Phase 0 Services
    qhal_service = QHALService()
    qpu_config = {"num_qubits": 5, "model_name": "NotebookSimQPU_5Q"} # Example: 5 qubits
    sim_qpu_driver = SimulatedQPU_Driver(device_id="sim_qpu_notebook", device_config=qpu_config)
    if not qhal_service.register_driver(sim_qpu_driver):
        print("CRITICAL ERROR: Could not register SimulatedQPU_Driver with QHALService.")

    pecs_service = PECS()
    # Optional: Instantiate and register a simulated PECS device
    # sim_tc_driver = SimulatedTemperatureController(device_id="tc_notebook", device_config={})
    # pecs_service.register_device(sim_tc_driver)

    ptss_stub = PTSS_Stub(qhal_service_instance=qhal_service)
    # ptss_stub.logger = ptss_logger # If PTSS_Stub is updated to take a logger

    # Instantiate Phase 1 Services
    sacs_stub = SACS_Stub_Phase1(shms_logger_instance=sacs_logger)
    rms_service = RMS_Phase1_Simulated(qhal_service_instance=qhal_service, shms_logger_instance=rms_logger)
    qlcs_service = QLCSService(shms_logger_instance=qlcs_logger)

    aes_service = AESService(
        qlcs=qlcs_service,
        rms=rms_service,
        ptss=ptss_stub,
        qhal_service=qhal_service,
        sacs_stub=sacs_stub,
        shms_logger=aes_logger
    )

    # Instantiate SDK Client
    # For Phase 1, SDK directly uses the aes_service instance.
    qos_sdk_client = ChimeraQOSClient(aes_service_instance=aes_service)

    print("CHIMera QOS Phase 1 Stack (Simulated) Initialized and SDK client is ready as 'qos_sdk_client'.")
    ```

## II. UI Additions/Modifications in Composer View

Locate the cell(s) in `chimera.ipynb` where `ipywidgets` for the composer view are defined (e.g., where `view_composer_button_bar`, `composer`, `data` widget, etc., are handled).

1.  **Add New Traits to `data` Widget:**
    *   In the cell defining the global `data = Widget()`:
    ```python
    # ... existing traits ...
    qos_job_id = Unicode("N/A").tag(sync=True),
    qos_job_status_msg = Unicode("Idle").tag(sync=True), # For user-friendly status messages
    qos_job_results_html = Unicode("").tag(sync=True),
    qos_num_shots = Int(1024).tag(sync=True), # Default shots for QOS runs
    # ...
    ```

2.  **Add New UI Widgets for QOS Interaction:**
    *   In a cell where other composer view widgets are defined:
    ```python
    # For QOS Interaction
    qos_run_button = widgets.Button(description="Run on CHIMera QOS (Sim)", button_style='success', icon='cogs')
    qos_num_shots_input = widgets.IntText(value=data.qos_num_shots, description='QOS Shots:', style={'description_width': 'initial'}, layout=widgets.Layout(width='200px'))
    link((qos_num_shots_input, 'value'), (data, 'qos_num_shots')) # Link to data model

    qos_job_id_display = appwidgets.ReactiveHtmlWidget("<div><strong>QOS Job ID:</strong> ${qos_job_id}</div>", data_model=data)
    qos_status_display = appwidgets.ReactiveHtmlWidget("<div style='margin-top:5px;'><strong>QOS Status:</strong> <span style='font-style:italic;'>${qos_job_status_msg}</span></div>", data_model=data)
    qos_results_display = appwidgets.ReactiveHtmlWidget("<div style='margin-top:10px; padding:10px; border:1px solid #ddd; background-color:#f9f9f9; min-height:50px;'><h4>QOS Results:</h4>${qos_job_results_html}</div>", data_model=data)

    # Arrange them, e.g., in an HBox or VBox
    qos_controls_box = widgets.VBox([
        widgets.HTML("<h4>Execute via CHIMera QOS (Simulated)</h4>"),
        qos_num_shots_input,
        qos_run_button,
        qos_job_id_display,
        qos_status_display
    ])
    ```

3.  **Integrate New Widgets into Composer View Layout:**
    *   Modify the `VBox` or `HBox` that defines `view_composer` (or its sub-panels) to include `qos_controls_box` and `qos_results_display`. For example, `qos_controls_box` could go into the right-hand panel alongside/below the existing single-shot controls. `qos_results_display` could go below the main composer or below the histogram area.
    *   Example: If `view_composer_singleshot` is in a right-hand VBox:
        ```python
        # Existing right_panel = VBox([view_composer_singleshot, ...])
        # New:
        # right_panel = VBox([view_composer_singleshot, qos_controls_box, ...])

        # And add qos_results_display to the main content area, e.g.,
        # main_composer_area = VBox([view_composer_button_bar, view_composer_hist_container_widget, circuit_info_display, qos_results_display])
        ```

## III. Python Callback Function for "Run on CHIMera QOS" Button

1.  **Define `run_circuit_via_qos()`:**
    *   In a code cell (likely where other UI callbacks like `get_single_shot_result` are):
    ```python
    import traceback # For better error reporting in UI

    def run_circuit_via_qos(b=None): # b is the button argument from on_click
        global data, composer, qos_sdk_client # Ensure SDK client is global or passed

        data.qos_job_id = "Submitting..."
        data.qos_job_status_msg = "Preparing QASM and submitting to QOS..."
        data.qos_job_results_html = "" # Clear previous results

        try:
            if composer.circuit is None or composer.circuit.num_qubits == 0:
                data.qos_job_status_msg = "Error: No circuit in composer or circuit is empty."
                data.qos_job_results_html = "<p style='color:red;'>Please build a circuit first.</p>"
                data.qos_job_id = "N/A"
                return

            current_qasm = composer.circuit.qasm()
            num_shots = data.qos_num_shots # Get from data model, linked to input widget

            if not qos_sdk_client: # Should have been initialized
                data.qos_job_status_msg = "Error: QOS SDK Client not initialized."
                data.qos_job_results_html = "<p style='color:red;'>SDK Client missing. Check notebook setup.</p>"
                data.qos_job_id = "N/A"
                return

            # Submit experiment using the SDK
            job_id = qos_sdk_client.submit_experiment(
                qasm_str=current_qasm,
                num_shots=num_shots,
                user_id="chimera_notebook_user" # Example user
            )
            data.qos_job_id = job_id
            data.qos_job_status_msg = f"Submitted. Polling status for Job ID: {job_id}"

            # Polling for results (simplified for Phase 1)
            # In a real UI, use threading or ipywidgets.interactive_output for non-blocking updates
            max_polls = 20  # e.g., 20 * 0.5s = 10s timeout
            poll_interval = 0.5
            for i in range(max_polls):
                status_info = qos_sdk_client.get_job_status(job_id)
                if status_info:
                    data.qos_job_status_msg = f"Status: {status_info.get('status', 'Unknown')}"
                    if status_info.get('status') == "COMPLETED":
                        results = qos_sdk_client.get_job_results(job_id)
                        if results:
                            html_results = "<ul>"
                            for outcome, count in results.items():
                                html_results += f"<li>{outcome}: {count}</li>"
                            html_results += "</ul>"
                            data.qos_job_results_html = html_results
                        else:
                            data.qos_job_results_html = "<p style='color:orange;'>Job completed, but no results returned by SDK.</p>"
                        break
                    elif "FAILED" in status_info.get('status', '').upper():
                        err_msg = status_info.get('error_message', 'Unknown error during QOS execution.')
                        data.qos_job_results_html = f"<p style='color:red;'>Job Failed: {err_msg}</p>"
                        break
                else:
                    data.qos_job_status_msg = f"Status: Waiting for update (poll {i+1}/{max_polls})..."

                if i < max_polls -1 : # Don't sleep after last poll
                    time.sleep(poll_interval)
            else: # Loop finished without break (timeout)
                data.qos_job_status_msg = f"Status: Timed out waiting for job {job_id} to complete."
                data.qos_job_results_html = "<p style='color:orange;'>Job did not complete within timeout.</p>"

        except Exception as e:
            tb_str = traceback.format_exc()
            data.qos_job_id = "Error"
            data.qos_job_status_msg = "Exception during QOS submission/polling."
            data.qos_job_results_html = f"<p style='color:red;'>An error occurred:<br><pre>{str(e)}</pre><br>Traceback:<pre>{tb_str}</pre></p>"
            if hasattr(e, 'job_id') and e.job_id: # If SDK exception includes job_id
                data.qos_job_id = e.job_id
    ```

2.  **Attach Callback to Button:**
    ```python
    qos_run_button.on_click(run_circuit_via_qos)
    ```

## IV. User Guidance (Markdown Cells)

*   Add a new Markdown cell or update an existing one in the notebook:
    *   Explaining the "Run on CHIMera QOS (Sim)" button.
    *   Noting that it uses a simulated backend for Phase 1.
    *   Explaining the Job ID, Status, and Results display areas.

This integration plan provides the necessary Python snippets and structural guidance to incorporate the Phase 1 QOS execution path into `chimera.ipynb`.
```
