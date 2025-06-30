// uls-platform/src/services/causalReasoningService.ts

import { loadPyodide, PyodideInterface } from "pyodide"; // Changed from global to import
// We'll still use 'any' for PyProxy for simplicity in this PoC, but PyodideInterface is typed.

interface PyodideOutput {
  results?: any; // Could be more specific if we knew all return types
  error?: string;
}

export class CausalReasoningService {
  private pyodide: PyodideInterface | null = null; // Use the imported type
  private isInitializing: boolean = false;
  private initializationPromise: Promise<void> | null = null;

  // For PoC, simple in-memory stores. In a real app, this might be more robust.
  private datasets: Map<string, any> = new Map(); // Stores Pyodide-side DataFrame proxies/names
  private causalModels: Map<string, any> = new Map(); // Stores Pyodide-side CausalModel proxies/names
  private identifiedEstimands: Map<string, any> = new Map(); // Stores Pyodide-side IdentifiedEstimand proxies/names

  constructor() {
    console.log("CausalReasoningService: Initializing...");
    // Initialization will be triggered by the first call that needs Pyodide.
    // Pre-load Pyodide on construction for faster first call for this PoC
    this.ensurePyodideInitialized().catch(err => {
        console.error("CausalReasoningService: Background Pyodide initialization failed on construct.", err);
    });
  }

  private async initializePyodide(): Promise<void> {
    if (this.pyodide) {
      console.log("CausalReasoningService: Pyodide already loaded.");
      return;
    }
    if (this.isInitializing && this.initializationPromise) {
      console.log("CausalReasoningService: Pyodide initialization in progress, awaiting completion.");
      return this.initializationPromise;
    }

    this.isInitializing = true;
    console.log("CausalReasoningService: Starting Pyodide load...");

    this.initializationPromise = (async () => {
      try {
        // When using `pyodide` npm package, `indexURL` behavior changes.
        // If Pyodide files are bundled locally (e.g., by a Vite plugin or Webpack plugin
        // copying them from `node_modules/pyodide/` to a static assets folder),
        // indexURL should point to that local relative path.
        // For Electron main process, this path needs to be resolvable.
        // A common strategy is to copy pyodide files to a known location in the app's packaged resources.
        // Example: if files are copied to './pyodide-dist/' relative to where this service runs (or an absolute path):
        // const pyodideBasePath = path.join(app.getAppPath(), 'dist/pyodide-files'); // Or similar
        // In a proper build system, this path would be determined by where the build tool places these assets.
        // For this step, we'll assume a placeholder relative path that step 3 will aim to populate.
        // The key change is that we are NO LONGER using the CDN by default with an npm install workflow.

        // Placeholder: Assume Pyodide files will be in 'node_modules/pyodide/build' or a location
        // copied by a build step. For Electron main, direct relative paths from __dirname can work if structure is known.
        // If using `pyodide/pyodide.js` directly from `node_modules` without `indexURL`, it might try to
        // load sibling files (like .wasm) from that `node_modules/pyodide/build` path.
        // For robustness and explicitness, especially for Electron's main process,
        // it's often better to ensure Pyodide files are copied to a known app location and use indexURL.
        // Let's assume for now that the `pyodide` npm package, when loaded in Node,
        // can find its own core files if `indexURL` is not provided, or we provide a path later.
        // The official docs for `pyodide` in Node.js usually imply it finds its files relative
        // For Electron main process, to ensure Pyodide files are found reliably,
        // especially in a packaged app, we will use an indexURL pointing to
        // a local directory where Pyodide's distribution files are expected to be.
        // This local directory (e.g., 'dist/pyodide_dist') should be populated by the build process
        // by copying files from 'node_modules/pyodide/build/'.

        // Dynamically determine the path to the local Pyodide distribution.
        // This requires `path` and potentially `app` from electron if running in main.
        // For now, this service is agnostic to Electron, so we'd need a way to pass this path in
        // or have a fixed relative expectation.
        // For PoC, let's assume a fixed relative path from where the app's resources are.
        // This would be something like './pyodide_dist/' if the service is run from the app root,
        // or more complex if run from a subdirectory within 'dist'.

        // For this conceptual step, we'll use a placeholder path.
        // The actual path resolution would be:
        // const isDev = !require('electron').app.isPackaged;
        // const resourcesPath = isDev ? path.join(__dirname, '..', '..', 'node_modules', 'pyodide', 'build') : path.join(process.resourcesPath, 'pyodide_dist');
        // const pyodideIndexURL = `file://${resourcesPath.replace(/\\/g, '/')}/`;
        // This logic is complex and better handled by the main Electron setup passing the URL to the service,
        // or the service being more aware of its environment.

        // For this step, we'll hardcode a relative path that a build system would aim to create.
        // This simulates the outcome of Step 3 "Local Pyodide Distribution".
        // IMPORTANT: This path is conceptual. Actual pathing depends on build output.
        // We are assuming that the build process places Pyodide files in a 'pyodide_files'
        // directory relative to where the CausalReasoningService.js (compiled) will be run from.
        // Or, if running from source with `ts-node` for main process, it might be relative to project root.

        // A simple relative path for Pyodide to try and resolve from its own location in node_modules
        // This is what `loadPyodide()` without indexURL does.
        // To explicitly test local file loading for a packaged scenario, we'd use a file:// URL.
        // Let's stick to no indexURL for this step to test default npm package behavior first,
        // and then step 3 (Local Pyodide Distribution) will be about ensuring files are copied
        // and THEN we'd add a local file:// indexURL if needed.
        // The previous step correctly changed to `await loadPyodide();`
        // This step is about TESTING that initialization.

        console.log("CausalReasoningService: Attempting to load Pyodide from npm package installation (default paths)...");
        this.pyodide = await loadPyodide();

        console.log("CausalReasoningService: Pyodide core loaded successfully via npm package (default paths).");

        // Package loading will still attempt to use Pyodide's default CDN for packages.
        // Making packages available locally is a separate, more advanced step.
        const packagesToLoad = ['pandas', 'numpy', 'scipy', 'statsmodels', 'networkx', 'dowhy'];
        console.log(`CausalReasoningService: Loading standard packages (defaulting to CDN via micropip): ${packagesToLoad.join(', ')}...`);
        await this.pyodide.loadPackage(packagesToLoad);
        console.log("CausalReasoningService: Standard packages for DoWhy loaded.");

      } catch (error: any) {
        console.error("CausalReasoningService: Pyodide (from npm package) or its packages failed to load.", error.message || error);
        this.pyodide = null;
        throw error;
      } finally {
        this.isInitializing = false;
      }
    })();
    return this.initializationPromise;
  }

  public async ensurePyodideInitialized(): Promise<boolean> {
    if (!this.pyodide && !this.isInitializing) {
      await this.initializePyodide();
    } else if (this.isInitializing && this.initializationPromise) {
      await this.initializationPromise;
    }
    return !!this.pyodide;
  }

  public async runPythonCode(pythonCode: string): Promise<PyodideOutput> {
    const initialized = await this.ensurePyodideInitialized();
    if (!initialized || !this.pyodide) {
      console.error("CausalReasoningService: Pyodide not available for runPythonCode.");
      return { error: "Pyodide not initialized or failed to load." };
    }

    console.log(`CausalReasoningService: Running Python code:\n${pythonCode}`);
    try {
      // Ensure necessary global objects for some scripts, like 'js' for document access if needed by Python
      // For now, not strictly necessary for headless DoWhy.
      // this.pyodide.globals.set('js_document', document); // Example, if DOM access from Python was needed

      let results = await this.pyodide.runPythonAsync(pythonCode);

      if (results && typeof results.toJs === 'function') {
        try {
            // Convert PyProxy to JS, especially for dicts
            // Handle potential errors during conversion, e.g. for complex objects
            results = results.toJs({ dict_converter: Object.fromEntries, default_converter: (pyProxy: any, _target: any, _memo: any) => {
              // Fallback for unhandled types: return string representation or a placeholder
              console.warn(`CausalReasoningService: PyProxy default_converter used for type: ${pyProxy.type}`);
              try {
                return pyProxy.toString();
              } catch {
                return `[Unconvertible PyProxy: ${pyProxy.type}]`;
              }
            }});
        } catch (conversionError) {
            console.warn("CausalReasoningService: Could not convert PyProxy to JS. Returning raw proxy or its string representation.", conversionError);
            if (results && typeof results.toString === 'function') {
              results = results.toString(); // Fallback to string representation
            }
        }
      } else if (results === undefined) {
        results = "Python code executed successfully (no explicit return value)."
      }

      console.log("CausalReasoningService: Python code execution successful. Results:", results);
      return { results };
    } catch (error: any) {
      console.error("CausalReasoningService: Error running Python code.", error);
      return { error: error.message || String(error) };
    }
  }

  public async testDoWhyWorkflow(): Promise<PyodideOutput> {
    console.log("CausalReasoningService: testDoWhyWorkflow called.");
    const initialized = await this.ensurePyodideInitialized();
    if (!initialized || !this.pyodide) {
      console.error("CausalReasoningService: Pyodide not available for testDoWhyWorkflow.");
      return { error: "Pyodide not initialized or failed to load for DoWhy test." };
    }

    // A minimal DoWhy example
    const testCode = `
import pandas as pd
import numpy as np
from dowhy import CausalModel

# Suppress specific warnings if necessary for cleaner PoC logs, not for production
import warnings
# warnings.filterwarnings("ignore", category=FutureWarning, module="dowhy.causal_estimators.propensity_score_estimator")

print("DoWhy Test: Starting...")

# 1. Create a sample dataset
data = pd.DataFrame({
    'Z': np.random.randint(0, 2, size=100),  # Confounder
    'X': np.random.randint(0, 2, size=100),  # Treatment
    'Y': np.random.normal(size=100)         # Outcome
})
data['Y'] = data['Y'] + data['Z']*0.5 + data['X']*0.8 + np.random.normal(0, 0.5, 100)
data['X'] = data['X'] + data['Z']*0.3 + np.random.binomial(1, 0.3, 100)
data['X'] = (data['X'] > 0.5).astype(int) # Ensure X is binary after adding Z effect

print("DoWhy Test: Sample data created.")
# print(data.head().to_string()) # For debugging data

# 2. Define the causal graph (GML format)
# Z -> X, Z -> Y, X -> Y
graph_gml = """
graph [
  directed 1
  node [ id "Z" label "Z" ]
  node [ id "X" label "X" ]
  node [ id "Y" label "Y" ]
  edge [ source "Z" target "X" ]
  edge [ source "Z" target "Y" ]
  edge [ source "X" target "Y" ]
]
"""
print("DoWhy Test: Causal graph defined.")

# 3. Create CausalModel
# For Pyodide, ensure observed_node_names are explicitly listed if not inferable
# from graph string directly by all versions or for robustness.
model = CausalModel(
    data=data,
    treatment='X',
    outcome='Y',
    graph=graph_gml,
    # common_causes=['Z'] # Can be explicit or inferred from graph
)
print("DoWhy Test: CausalModel created.")

# 4. Identify causal effect
identified_estimand = model.identify_effect(proceed_when_unidentifiable=True)
print("DoWhy Test: Effect identified.")
# print(identified_estimand) # For debugging

# 5. Estimate the causal effect (using a simple method)
# Using linear regression for simplicity in PoC. Propensity score matching might need more setup/data.
estimate = model.estimate_effect(
    identified_estimand,
    method_name="backdoor.linear_regression", # Using linear_regression for simplicity
    test_significance=True
)
print("DoWhy Test: Effect estimated.")
# print(estimate) # For debugging

# Prepare a dictionary to return
result_dict = {
    "identified_estimand_str": str(identified_estimand),
    "estimated_effect_value": estimate.value,
    "estimate_ci": None, # CI might be more complex to extract depending on estimator
    "realized_estimand_expression": str(estimate.realized_estimand_expression) if hasattr(estimate, 'realized_estimand_expression') else "N/A"
}
if hasattr(estimate, 'get_confidence_intervals'):
    try:
        ci = estimate.get_confidence_intervals()
        result_dict["estimate_ci"] = str(ci) # Convert CI to string for simplicity
    except Exception as e:
        print(f"DoWhy Test: Could not get CI: {e}")
        result_dict["estimate_ci"] = "Error retrieving CI"


# Attempt to access specific fields, ensure they exist
# Some attributes might not be present in all versions or for all estimators
if hasattr(identified_estimand, 'textual_summary'):
    result_dict["identified_estimand_summary"] = identified_estimand.textual_summary
if hasattr(estimate, 'params') and 'p_value' in estimate.params:
     result_dict["p_value"] = estimate.params['p_value'][0] # Assuming p-value is in params

print(f"DoWhy Test: Preparing to return dict: {result_dict}")
result_dict # This will be the return value of runPythonAsync
    `;
    return this.runPythonCode(testCode);
  }

  // --- Core API Endpoints for PoC ---

  public async loadDatasetFromString(
    dataCsvString: string,
    datasetId: string
  ): Promise<{ status: string; columns?: string[]; error?: string }> {
    const initialized = await this.ensurePyodideInitialized();
    if (!initialized || !this.pyodide) {
      return { status: "error", error: "Pyodide not initialized." };
    }

    // Make data_csv_string available to Python
    this.pyodide.globals.set('js_data_csv_string', dataCsvString);
    this.pyodide.globals.set('js_dataset_id', datasetId);

    const pythonCode = `
import pandas as pd
from io import StringIO

print(f"Python: Loading dataset {js_dataset_id} from CSV string...")
data_string = str(js_data_csv_string) # Ensure it's a string
df = pd.read_csv(StringIO(data_string))
# Store DataFrame in Pyodide's global scope for later use
# Pyodide's global scope is not directly accessible like Python's global()
# We'll manage references through JS. For this PoC, we store the df proxy.
# A better way would be to assign it to a global variable:
# pyodide.globals.set(f"df_{js_dataset_id}", df)
# For now, we rely on the service's JS map to hold the proxy.

# For this PoC, we'll just return columns. Storing the actual df proxy
# in the service's 'datasets' map is more complex due to PyProxy lifecycle.
# A simple approach for PoC: store the df in python global and refer by name.
pyodide.globals.set(f"df_{js_dataset_id}", df)

print(f"Python: Dataset {js_dataset_id} loaded. Shape: {df.shape}")
df_columns = list(df.columns)
df_columns
    `;

    const output = await this.runPythonCode(pythonCode);
    if (output.error) {
      return { status: "error", error: output.error };
    }

    // For PoC, we assume the Python code assigns the df to a global var like f"df_{datasetId}"
    // and the service can refer to it by that name in subsequent calls.
    // This simplifies state management across calls for the PoC.
    this.datasets.set(datasetId, `df_${datasetId}`); // Store the Python variable name

    return { status: "success", columns: output.results as string[] };
  }

  public async defineCausalModelSimple(
    datasetId: string,
    graphGmlString: string,
    treatment: string,
    outcome: string,
    modelId: string // Added modelId for referencing
  ): Promise<{ model_id_ref?: string; status: string; identified_estimand_str?: string; error?: string }> {
    const initialized = await this.ensurePyodideInitialized();
    if (!initialized || !this.pyodide) {
      return { status: "error", error: "Pyodide not initialized." };
    }

    const df_name = this.datasets.get(datasetId);
    if (!df_name) {
        return { status: "error", error: `Dataset ${datasetId} not found or not loaded.` };
    }

    this.pyodide.globals.set('js_df_name_str', df_name);
    this.pyodide.globals.set('js_graph_gml_string', graphGmlString);
    this.pyodide.globals.set('js_treatment_name', treatment);
    this.pyodide.globals.set('js_outcome_name', outcome);
    this.pyodide.globals.set('js_model_id', modelId);


    const pythonCode = `
from dowhy import CausalModel
import pandas as pd # Just in case, though df should be global

print(f"Python: Defining causal model {js_model_id}...")
# Retrieve the DataFrame from global scope
current_df = pyodide.globals.get(js_df_name_str)
if current_df is None:
    raise ValueError(f"DataFrame {js_df_name_str} not found in Pyodide globals.")

# print(f"Data for model: {current_df.head().to_string()}") # Debug

causal_model_instance = CausalModel(
    data=current_df,
    treatment=str(js_treatment_name),
    outcome=str(js_outcome_name),
    graph=str(js_graph_gml_string)
)
print(f"Python: CausalModel {js_model_id} created.")

identified_estimand_instance = causal_model_instance.identify_effect(proceed_when_unidentifiable=True)
print(f"Python: Effect identified for model {js_model_id}.")

# Store model and estimand in Pyodide global scope for PoC
pyodide.globals.set(f"cm_{js_model_id}", causal_model_instance)
pyodide.globals.set(f"ie_{js_model_id}", identified_estimand_instance)

{
    "identified_estimand_str": str(identified_estimand_instance)
}
    `;

    const output = await this.runPythonCode(pythonCode);

    if (output.error) {
      return { status: "error", error: output.error };
    }

    // Store references to the Python global variable names
    this.causalModels.set(modelId, `cm_${modelId}`);
    this.identifiedEstimands.set(modelId, `ie_${modelId}`); // Using modelId as key for its estimand

    return {
      model_id_ref: modelId, // Return the same modelId used as input for clarity
      status: "success",
      identified_estimand_str: output.results?.identified_estimand_str,
    };
  }

  public async estimateIdentifiedEffect(
    modelId: string,
    estimatorMethod: string = "backdoor.linear_regression"
  ): Promise<{ results?: any; status: string; error?: string }> {
    const initialized = await this.ensurePyodideInitialized();
    if (!initialized || !this.pyodide) {
      return { status: "error", error: "Pyodide not initialized." };
    }

    const cm_name = this.causalModels.get(modelId);
    const ie_name = this.identifiedEstimands.get(modelId);

    if (!cm_name || !ie_name) {
      return { status: "error", error: `Causal model or identified estimand for ${modelId} not found.` };
    }

    this.pyodide.globals.set('js_cm_name_str', cm_name);
    this.pyodide.globals.set('js_ie_name_str', ie_name);
    this.pyodide.globals.set('js_estimator_method_str', estimatorMethod);
    this.pyodide.globals.set('js_model_id_str', modelId);


    const pythonCode = `
print(f"Python: Estimating effect for model {js_model_id_str} using {js_estimator_method_str}...")
# Retrieve model and estimand from global scope
causal_model_instance = pyodide.globals.get(js_cm_name_str)
identified_estimand_instance = pyodide.globals.get(js_ie_name_str)

if causal_model_instance is None or identified_estimand_instance is None:
    raise ValueError(f"Causal model or estimand for {js_model_id_str} not found in Pyodide globals.")

estimate = causal_model_instance.estimate_effect(
    identified_estimand_instance,
    method_name=str(js_estimator_method_str),
    test_significance=True # Or make this an option
)
print(f"Python: Effect estimated for model {js_model_id_str}.")

# Prepare a dictionary to return
# This is a simplified version of the one in testDoWhyWorkflow for PoC
result_dict = {
    "estimated_effect_value": estimate.value,
    "estimator_used": str(js_estimator_method_str),
    "realized_estimand_expression": str(estimate.realized_estimand_expression) if hasattr(estimate, 'realized_estimand_expression') else "N/A"
}
try:
    ci = estimate.get_confidence_intervals()
    result_dict["estimate_ci"] = str(ci)
except Exception as e:
    print(f"Python: Could not get CI for {js_model_id_str}: {e}")
    result_dict["estimate_ci"] = "Error retrieving CI"

# Store estimate in globals for PoC if needed later (e.g. for refutation)
pyodide.globals.set(f"est_{js_model_id_str}", estimate)

result_dict
    `;

    const output = await this.runPythonCode(pythonCode);

    if (output.error) {
      return { status: "error", error: output.error };
    }
    return { results: output.results, status: "success" };
  }
}

// Example usage (would typically be in Electron main process or a dedicated service manager)
// async function testApiEndpoints() {
//   console.log("API Test: Creating CausalReasoningService instance...");
//   const service = new CausalReasoningService(); // Constructor now calls ensurePyodideInitialized

//   // Wait a bit for background initialization if it's happening
//   await new Promise(resolve => setTimeout(resolve, 3000)); // Adjust time as needed for Pyodide init

//   const initStatus = await service.ensurePyodideInitialized(); // Should be quick if pre-init started
//   console.log("API Test: Pyodide initialization status:", initStatus);

//   if (!initStatus) {
//     console.error("API Test: Pyodide failed to initialize. Aborting tests.");
//     return;
//   }

//   console.log("API Test: --- Testing loadDatasetFromString ---");
//   const csvData = "Z,X,Y\\n0,0,1.2\\n1,0,2.5\\n0,1,3.1\\n1,1,4.8\\n0,0,1.5\\n1,1,5.0"; // Minimal CSV
//   const datasetId = "test_data_01";
//   const loadResp = await service.loadDatasetFromString(csvData, datasetId);
//   console.log("API Test: loadDatasetFromString response:", loadResp);
//   if (loadResp.error) return;

//   console.log("API Test: --- Testing defineCausalModelSimple ---");
//   const gml = "graph [ directed 1 node [ id \\"Z\\" label \\"Z\\" ] node [ id \\"X\\" label \\"X\\" ] node [ id \\"Y\\" label \\"Y\\" ] edge [ source \\"Z\\" target \\"X\\" ] edge [ source \\"Z\\" target \\"Y\\" ] edge [ source \\"X\\" target \\"Y\\" ] ]";
//   const modelId = "test_model_01";
//   const defineResp = await service.defineCausalModelSimple(datasetId, gml, "X", "Y", modelId);
//   console.log("API Test: defineCausalModelSimple response:", defineResp);
//   if (defineResp.error) return;

//   console.log("API Test: --- Testing estimateIdentifiedEffect ---");
//   const estimateResp = await service.estimateIdentifiedEffect(modelId, "backdoor.linear_regression");
//   console.log("API Test: estimateIdentifiedEffect response:", estimateResp);
// }

// // To run this test, similar setup as testDoWhyWorkflow is needed.
// // (async () => {
// //     if (typeof window !== 'undefined') {
// //         console.log("API Test Script: Detected browser-like environment, attempting to run testApiEndpoints()...");
// //         // await testApiEndpoints();
// //     } else {
// //         console.log("API Test Script: Not in a browser-like environment.");
// //     }
// // })();
