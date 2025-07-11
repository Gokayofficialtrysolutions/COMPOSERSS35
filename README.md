# CHIMera Explorer - Offline Quantum Combinatorics Tool

<img src="css/CHIMeraMug.png" alt="CHIMera Explorer Logo" width="150">
<!-- TODO: Consider a new logo that is less coffee-specific -->

**CHIMera Explorer is an interactive, offline-first Jupyter Notebook environment for learning and experimenting with quantum circuits that represent combinatorial mathematics concepts. Explore permutations, combinations, binomial distributions, and more, all locally on your machine for up to ~10 qubits.**

This project has pivoted from its original project concept (an IoT coffee machine controller) to focus entirely on providing an educational tool for quantum computation. Home Connect related features have been removed.

## Core Features

*   **Offline Quantum Simulation:** Uses Qiskit Aer for local simulation.
*   **Circuit Library & Generation:**
    *   **Combinatorial Circuits:** Binomial distributions, permutations (pre-defined & custom), N-choose-k combinations, W-states.
    *   **Introductory Quantum Algorithms:** Includes examples like the Deutsch-Jozsa algorithm.
*   **Interactive Circuit Composer:** Visually build and modify circuits using `ibm_quantum_widgets.CircuitComposer`.
*   **Dynamic Measurement Visualization:** Adaptive histograms for measurement probabilities.
*   **State Visualization:** Includes Bloch sphere representations for individual qubit states (`plot_bloch_multivector`).
*   **Educational Content Display:** Contextual explanations, formulas, and exploration ideas alongside circuits within `chimera.ipynb`.
*   **Single-Shot Execution:** Simulate single measurement outcomes.
*   **Basic UI Feedback:** Global status bar and IBMQ execution messages.
*   **(Optional) IBM Quantum Integration:** Export to IBM Quantum Composer, potential for future hardware comparison.
*   **CLI Tool (`chimera_cli.py`):** System health checks.

## Getting Started

### Prerequisites

*   Python 3.8+
*   Jupyter Notebook or JupyterLab
*   Qiskit (and its dependencies like Matplotlib, NumPy)
*   Other Python packages as listed in `requirements.txt`.

### Installation

1.  **Clone the Repository:**
    ```bash
    git clone <repository_url>
    cd <project_directory_name> # e.g., CHIMera-Explorer
    ```

2.  **Install Dependencies:**
    It's highly recommended to use a Python virtual environment.
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```
    This will install Qiskit, Jupyter, and other necessary packages.

3.  **Install Project Packages:**
    Install the local Python packages that provide the backend API and custom widgets:
    ```bash
    pip install ./qoffeeapi --user  # Directory 'qoffeeapi' and its internal package name are preserved
    pip install ./appwidgets --user
    ```
    *Note: Using `--user` installs to your user site-packages. For isolated environments, you might prefer editable installs (`pip install -e ./qoffeeapi`) if you are developing these packages, or ensure your virtual environment is active.*

4.  **Enable Jupyter Extensions:**
    ```bash
    jupyter nbextension install --sys-prefix --overwrite --py appwidgets
    jupyter nbextension enable --sys-prefix --py appwidgets
    jupyter nbextension install --sys-prefix --overwrite --py qoffeefrontend # Directory 'qoffeefrontend' is preserved
    jupyter nbextension enable --sys-prefix --py qoffeefrontend # Directory 'qoffeefrontend' is preserved
    # For JupyterLab, you might need to build/install lab extensions separately
    # jupyter labextension develop appwidgets --overwrite
    # jupyter labextension develop qoffeefrontend --overwrite # Directory 'qoffeefrontend' is preserved
    ```
    *Note: `--sys-prefix` installs for the current Python environment. Use `--user` if not in a venv and you want user-wide install, or `--system` for system-wide (usually requires admin).*

5.  **Set up Environment Variables (Optional):**
    Copy the `env-template` file to a new file named `.env` in the root of the project:
    ```bash
    cp env-template .env
    ```
    Edit `.env` if you plan to use optional online IBM Quantum features:
    *   `IBMQ_API_KEY`: Your API Key from your [IBM Quantum Account](https://quantum-computing.ibm.com/account). This is only needed if you want to try sending circuits to IBM Quantum hardware/cloud simulators. For fully offline use, this can be left blank.
    *   `CHIMERA_BASE_URL` (formerly `QOFFEE_BASE_URL`): Only needed if you run the CLI tool (`chimera_cli.py`) and your Jupyter server is not at `http://localhost:8887`.

6.  **Run Jupyter Notebook/Lab:**
    ```bash
    jupyter notebook
    # or
    jupyter lab
    ```
    Open `chimera.ipynb` (formerly `qoffee.ipynb`) from the Jupyter interface.

7.  **IMPORTANT: Manual UI Setup in `chimera.ipynb`:**
    The core functionality of this project, especially the interactive Quantum Combinatorics Explorer, relies on UI elements within the `chimera.ipynb` notebook. While some enhancements are being made programmatically by the AI agent, the initial setup and potentially some future complex UI additions might require manual adjustments to this notebook.
    Refer to **[MANUAL_CHIMERA_IPYNB_SETUP.md](MANUAL_CHIMERA_IPYNB_SETUP.md)** for historical context on manual setup. Current development aims to reduce reliance on extensive manual setup by direct notebook modification where possible.

8.  **Activate App Mode:**
    Once `chimera.ipynb` is open and you have run all cells, click the rocket icon (🚀) in the Jupyter Notebook toolbar to activate "App Mode" for a cleaner interface.

## Project Structure Overview

*   **`chimera.ipynb`** (formerly `qoffee.ipynb`): The main Jupyter Notebook providing the interactive UI.
*   **`qoffeeapi/`**: Python package for the backend (directory name preserved due to tool limitations; internal branding is CHIMera).
    *   `api_orchestrator.py`: Defines API handlers (e.g., for `/api/health`).
    *   `combinatorial_circuits.py`: Core logic for generating quantum circuits.
*   **`qoffeefrontend/`**: Jupyter Notebook extension for frontend JavaScript (`app.js`) and CSS (directory name preserved).
*   **`appwidgets/`**: Python package for custom ipywidgets used in `chimera.ipynb`.
*   **`chimera_cli.py`** (formerly `qoffee_cli.py`): Command-line tool for system health checks.
*   **`MANUAL_CHIMERA_IPYNB_SETUP.md`**: Historical guide for manual UI setup in the notebook. Current development by the AI agent modifies `chimera.ipynb` directly.
*   **`UI_SETUP_QUICKSTART.md`**: Abridged version of the manual setup guide.
*   **`DEVELOPER_GUIDE.md`**: In-depth technical details.

## Security Considerations

Please review the following security considerations when using or developing this project:

*   **IBMQ API Key (`.env` file):** If you use an `IBMQ_API_KEY`, protect your `.env` file. Do not commit it to public repositories.
*   **Jupyter Server Security:** Secure your Jupyter server with a token or password, and avoid exposing it publicly without proper security measures. Refer to Jupyter's official security documentation.
*   **Code Execution from UI (`data-rh-exec` in `chimera.ipynb`):** The notebook UI allows execution of Python code defined in its templates. Only run notebooks from trusted sources.
*   **Docker Container Security (if used):** Ensure base images are trusted and up-to-date.

(For more details, see the "Security Considerations" section in the [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)).

## For Developers and Advanced Users

*   **Manual UI Setup Guide (Historical):** [MANUAL_CHIMERA_IPYNB_SETUP.md](MANUAL_CHIMERA_IPYNB_SETUP.md) (Note: AI agent now directly modifies `chimera.ipynb`)
*   **Developer Guide (Technical Details & Architecture):** [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)
*   **Future Development Roadmap:** [PROJECT_ROADMAP.md](PROJECT_ROADMAP.md)

## CHIMera Quantum Operating System (QOS) Initiative

This project is also the incubation ground for the **CHIMera Quantum Operating System (QOS)**, a long-term vision to develop a comprehensive software stack for managing and orchestrating quantum laboratory environments.

*   **Vision:** To create a modular, scalable, and robust QOS that can interface with diverse quantum hardware and simulators, manage complex experimental workflows, and provide a rich environment for quantum algorithm development and execution.
*   **Core Services (Architectural Blueprints):** The initial architectural designs for key QOS services are being developed. For more details, see the [CHIMera QOS Core Service Architectural Blueprints](./qos_core_services/README.md).
*   **Current Status:** The QOS initiative is in the early architectural design and planning stages. The `qos_core_services` directory contains the first set of conceptual blueprints.

## Installation on RasQberry (Legacy Note)

The "Installation on RasQberry" section below refers to a previous version of this project that had different functionalities. It may not be directly applicable to the current "Quantum Combinatorics Explorer" focus.

---
*Legacy RasQberry instructions removed as they are no longer relevant to the core refocused project.*
