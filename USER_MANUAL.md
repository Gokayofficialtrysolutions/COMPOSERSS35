# CHIMera Explorer - User Manual

## 1. Introduction

Welcome to CHIMera Explorer! This tool is an interactive Jupyter Notebook environment designed for learning and experimenting with quantum circuits that represent various combinatorial mathematics concepts and introductory quantum algorithms. You can build, simulate, and analyze quantum circuits locally on your machine.

**Key Goals:**
*   Provide an intuitive platform for understanding the connection between quantum computation and discrete mathematics.
*   Allow exploration of concepts like binomial distributions, permutations, combinations, and W-states using quantum circuits.
*   Introduce foundational quantum algorithms like Deutsch-Jozsa, Grover's Search, and a conceptual look at Quantum Counting.
*   Enable hands-on experience with Qiskit for circuit generation and simulation.

## 2. Installation

Please refer to the main [README.md](README.md) for detailed, up-to-date installation instructions. A summary is provided here:

**Prerequisites:**
*   Python 3.8+
*   Jupyter Notebook or JupyterLab
*   Qiskit (and its dependencies)

**Steps:**
1.  **Clone the Repository:**
    ```bash
    git clone <repository_url>
    cd <project_directory_name> # e.g., CHIMera-Explorer
    ```
2.  **Set up Virtual Environment (Recommended) & Install Dependencies:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```
3.  **Install Local Project Packages:**
    From the root of the project directory:
    ```bash
    pip install ./qoffeeapi --user
    pip install ./appwidgets --user
    ```
    *(Note: The directory `qoffeeapi` is preserved for technical reasons; its internal branding and functionality align with CHIMera Explorer.)*
4.  **Enable Jupyter Extensions:**
    ```bash
    jupyter nbextension install --sys-prefix --overwrite --py appwidgets
    jupyter nbextension enable --sys-prefix --py appwidgets
    jupyter nbextension install --sys-prefix --overwrite --py qoffeefrontend
    jupyter nbextension enable --sys-prefix --py qoffeefrontend
    ```
    *(Note: The extension name `qoffeefrontend` is preserved for technical reasons.)*
5.  **Set up Environment Variables (Optional):**
    Copy `env-template` to `.env` and edit if you plan to use optional online IBM Quantum features:
    *   `IBMQ_API_KEY`: For sending circuits to IBM Quantum hardware/cloud simulators.
    *   `CHIMERA_BASE_URL`: If your Jupyter server runs on a non-default URL and you use `chimera_cli.py`.

## 3. Launching and Navigating CHIMera Explorer

1.  **Start Jupyter:**
    ```bash
    jupyter notebook
    # or
    jupyter lab
    ```
2.  **Open the Notebook:** Navigate to and open `chimera.ipynb`.
3.  **Run All Cells:** It's recommended to run all cells when you first open the notebook to initialize all components. Click "Cell" -> "Run All" in the Jupyter menu.
4.  **Activate App Mode:** Once all cells have run, click the **rocket icon (🚀)** in the Jupyter Notebook toolbar. This provides a cleaner, app-like interface by hiding most of the Jupyter UI elements. To exit App Mode, press the `ESC` key.

## 4. Using CHIMera Explorer

### 4.1. Welcome View

Upon launching, you'll be greeted by the Welcome View. This is your main navigation hub.

*   **Header:**
    *   **CHIMera Explorer Logo & Title:** Displays the application name.
    *   **"Q" Button:** Toggles the device used for "Single Shot" measurements in the Composer View (Simulator, Mock Device, IBMQ Device - if configured).
    *   **Back Arrow (ᐊ):** Appears when not on the Welcome View; click to return to the Welcome View.
    *   **Help Button (?):** Opens an overlay with links to documentation and resources.

*   **Explore Quantum Concepts (Examples):**
    *   A series of cards, each representing a pre-defined quantum circuit or algorithm.
    *   Clicking a card loads the corresponding circuit into the Composer View along with educational information about it.
    *   Examples include: Binomial Distributions, Permutations, Combinations, W-States.

*   **Explore Quantum Algorithms:**
    *   Cards for introductory quantum algorithms.
    *   Examples include: Deutsch-Jozsa, Grover's Search (2-qubit), Quantum Counting (conceptual).
    *   Clicking a card loads the algorithm into the Composer View with explanations.

*   **Custom Combinatorial Circuit:**
    *   A special card that takes you to the "Custom Combinatorial Circuit Input View" (see section 4.3).

*   **Original CHIMera System Demos (Legacy):**
    *   These are circuits from a previous iteration of the project. They are functional but may not align with the current Quantum Combinatorics focus.

### 4.2. Composer View

This is where you interact with and analyze the quantum circuits.

*   **Circuit Composer Widget:**
    *   A visual drag-and-drop interface (from `ibm_quantum_widgets`) to build or modify the currently loaded quantum circuit.
    *   You can add/remove qubits and gates.
*   **Measurement Probabilities Section:**
    *   **Histograms:** Dynamically generated bar charts showing the theoretical (analytical) probabilities of measuring each basis state.
        *   You can toggle the display of results from an error-free QASM simulator and a noisy mock simulator (simulating a real quantum device).
    *   **"Export to IBM Quantum Composer" Button:** Generates a QR code. Scanning this with your mobile device (requires internet) opens the current circuit in the IBM Quantum Composer web interface. The raw QASM is also displayed for copying.
    *   **"Show Bloch Spheres" Button:** Displays Bloch sphere representations for each qubit in the current statevector (calculated analytically). Useful for visualizing single-qubit states.
*   **Educational Content Area:**
    *   Displays information about the currently loaded circuit/concept, including:
        *   **Concept:** A brief description.
        *   **Circuit Details:** Parameters used to generate it.
        *   **Interpretation:** Explanation of what the circuit does or represents.
        *   **Key Formulas/Representations:** Relevant mathematical formulas.
        *   **Try Exploring:** Suggestions for further experimentation.
*   **Single Shot Execution Area:**
    *   **"Run Single Shot" Button:** Executes the current circuit once on the selected device (toggled by the "Q" button in the header).
    *   **Result Display:** Shows the measured bitstring.
    *   **"Clear Result" Button:** Clears the displayed single-shot result.
    *   **Status/IBMQ Message:** Displays messages related to IBMQ execution attempts or errors.

### 4.3. Custom Combinatorial Circuit Input View

Accessible from the Welcome View, this allows you to generate specific combinatorial circuits with your own parameters.

1.  **Select Circuit Type:**
    *   **Binomial Distribution:** Models independent trials.
        *   **Parameters:** Number of Qubits (N), Success Probability (p).
    *   **Combination (N choose k):** Creates a superposition of states with 'k' ones.
        *   **Parameters:** Number of Qubits (N), Qubits to Select (k).
    *   **Permutation (Custom List):** Implements a specific permutation of basis states.
        *   **Parameters:** Number of Qubits (N), Permutation List (comma-separated integers representing the mapping).
2.  **Enter Parameters:** Fill in the input fields relevant to your chosen circuit type. Irrelevant fields may be hidden.
3.  **Click "Generate & Load Circuit":** This creates the circuit with your parameters and loads it into the Composer View, along with relevant educational content.
4.  **Error Messages:** If parameters are invalid, an error message will be displayed.

## 5. Overview of Quantum Concepts & Algorithms

*   **Binomial Distribution:** Quantum circuits where each qubit's measurement outcome (|0⟩ or |1⟩) follows a Bernoulli trial, and the collective measurements approximate a binomial distribution.
*   **Permutations:** Circuits that reorder (permute) the computational basis states.
*   **Combinations (N choose k):** Circuits that prepare an equal superposition of all N-qubit basis states that have exactly 'k' qubits in the |1⟩ state.
*   **W-States:** A specific type of entangled state where one qubit is in |1⟩ and the rest are in |0⟩, in superposition across all possible single-excitation positions.
*   **Deutsch-Jozsa Algorithm:** A foundational quantum algorithm that determines if a given (oracle) function is constant or balanced, often outperforming classical algorithms.
*   **Grover's Search Algorithm (2-Qubit Example):** A quantum search algorithm that can find a specific "marked" item in an unstructured database quadratically faster than classical search. The example demonstrates finding one marked state out of four.
*   **Quantum Counting (Conceptual Example):** Illustrates how Quantum Phase Estimation can be used with Grover's operator to estimate the number of solutions (marked items) in a search space. The provided example is conceptual due to qubit limitations for full precision.

## 6. Troubleshooting

*   **UI Not Responding / Errors in Notebook:**
    *   Try restarting the Jupyter kernel: "Kernel" -> "Restart". Then run all cells again.
    *   Check the Jupyter server logs in your terminal for error messages.
    *   Check your web browser's developer console (usually F12) for JavaScript errors.
*   **Circuit Not Loading / Incorrect Behavior:**
    *   Ensure all necessary Python packages (Qiskit, appwidgets, etc.) are installed correctly.
    *   If using custom parameters, double-check they are valid for the selected circuit type.
    *   Refer to `MANUAL_CHIMERA_IPYNB_SETUP.md` if you suspect issues from manual notebook setup (though current development aims to minimize this need).
*   **IBMQ Features Not Working:**
    *   Ensure your `IBMQ_API_KEY` is correctly set in the `.env` file.
    *   An internet connection is required for all IBM Quantum online features.
    *   Check the "Status/IBMQ Message" area in the Composer View for error details.

## 7. Exiting App Mode

*   Press the `ESC` key to deactivate App Mode and return to the standard Jupyter Notebook interface.

We hope you enjoy exploring the world of quantum combinatorics with CHIMera Explorer!
