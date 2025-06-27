# Qoffee Explorer - Offline Quantum Combinatorics Tool

<img src="css/QoffeeMug.png" alt="Qoffee Explorer Logo" width="150">
<!-- TODO: Consider a new logo that is less coffee-specific -->

**Qoffee Explorer is an interactive, offline-first Jupyter Notebook environment for learning and experimenting with quantum circuits that represent combinatorial mathematics concepts. Explore permutations, combinations, binomial distributions, and more, all locally on your machine for up to ~10 qubits.**

This project has pivoted from its original "Qoffee-Maker" (IoT coffee machine control) concept to focus entirely on providing an educational tool for quantum computation. Home Connect related features have been removed.

## Core Features

*   **Offline Quantum Simulation:** Uses Qiskit Aer for local simulation of quantum circuits. No internet connection required for core functionality.
*   **Combinatorial Circuit Generation:**
    *   Generate circuits for **Binomial Distributions** (parameterized by N qubits & success probability p).
    *   Explore **Permutations** with pre-defined examples (SWAP, cycles, bit-reversal) and generate circuits for custom user-defined permutations.
    *   Create **N-choose-k Combination** superposition states (via `qc.initialize` for simulation clarity, and example gate-based W-states).
*   **Interactive Circuit Composer:** Utilizes `ibm_quantum_widgets.CircuitComposer` to visually build and modify quantum circuits within the Jupyter Notebook.
*   **Educational Content Display:** (Requires manual UI setup in `qoffee.ipynb`) Designed to show contextual explanations, formulas, and exploration ideas alongside circuits.
*   **Basic UI Feedback:** A global status bar in the browser provides simple network status.
*   **(Optional) IBM Quantum Integration:** If an `IBMQ_API_KEY` is provided, users can (when online) export circuits to the IBM Quantum Composer and (conceptually, if UI implemented) compare local simulations with real IBM Quantum hardware execution (with fallback to local noisy simulation if offline/unavailable).
*   **CLI Tool (`qoffee_cli.py`):** Provides a command-line interface for system health checks.

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
    cd qoffee-maker
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
    pip install ./qoffeeapi --user
    pip install ./appwidgets --user
    ```
    *Note: Using `--user` installs to your user site-packages. For isolated environments, you might prefer editable installs (`pip install -e ./qoffeeapi`) if you are developing these packages, or ensure your virtual environment is active.*

4.  **Enable Jupyter Extensions:**
    ```bash
    jupyter nbextension install --sys-prefix --overwrite --py appwidgets
    jupyter nbextension enable --sys-prefix --py appwidgets
    jupyter nbextension install --sys-prefix --overwrite --py qoffeefrontend
    jupyter nbextension enable --sys-prefix --py qoffeefrontend
    # For JupyterLab, you might need to build/install lab extensions separately
    # jupyter labextension develop appwidgets --overwrite
    # jupyter labextension develop qoffeefrontend --overwrite
    ```
    *Note: `--sys-prefix` installs for the current Python environment. Use `--user` if not in a venv and you want user-wide install, or `--system` for system-wide (usually requires admin).*

5.  **Set up Environment Variables (Optional):**
    Copy the `env-template` file to a new file named `.env` in the root of the project:
    ```bash
    cp env-template .env
    ```
    Edit `.env` if you plan to use optional online IBM Quantum features:
    *   `IBMQ_API_KEY`: Your API Key from your [IBM Quantum Account](https://quantum-computing.ibm.com/account). This is only needed if you want to try sending circuits to IBM Quantum hardware/cloud simulators. For fully offline use, this can be left blank.
    *   `QOFFEE_BASE_URL`: Only needed if you run the CLI tool and your Jupyter server is not at `http://localhost:8887`.

6.  **Run Jupyter Notebook/Lab:**
    ```bash
    jupyter notebook
    # or
    jupyter lab
    ```
    Open `qoffee.ipynb` from the Jupyter interface.

7.  **IMPORTANT: Manual UI Setup in `qoffee.ipynb`:**
    To enable the full user interface for combinatorial circuit generation, educational content display, and other advanced UI feedback, **you must manually edit several cells within the `qoffee.ipynb` notebook.**
    Detailed step-by-step instructions are provided in:
    **[MANUAL_QOFFEE_IPYNB_SETUP.md](MANUAL_QOFFEE_IPYNB_SETUP.md)**

    A condensed version for getting started quickly is available in:
    **[UI_SETUP_QUICKSTART.md](UI_SETUP_QUICKSTART.md)**

    *This manual setup is necessary due to limitations in programmatically modifying complex notebook structures reliably with current automated tooling.*

8.  **Activate App Mode:**
    Once `qoffee.ipynb` is open and you have (ideally) performed the manual UI setup, run all cells. Then, click the rocket icon (🚀) in the Jupyter Notebook toolbar to activate "App Mode" for a cleaner interface.

## Project Structure Overview

*   **`qoffee.ipynb`**: The main Jupyter Notebook providing the interactive UI (requires manual setup for full features).
*   **`qoffeeapi/`**: Python package for the backend Jupyter server extension.
    *   `qoffeeapi/api_orchestrator.py`: Defines API handlers (e.g., for `/api/health`).
    *   `qoffeeapi/combinatorial_circuits.py`: Core logic for generating quantum circuits for combinatorial concepts.
*   **`qoffeefrontend/`**: Jupyter Notebook extension for frontend JavaScript (`app.js`) and CSS.
*   **`appwidgets/`**: Python package for custom ipywidgets used in `qoffee.ipynb`.
*   **`qoffee_cli.py`**: Command-line tool for system health checks.
*   **`MANUAL_QOFFEE_IPYNB_SETUP.md`**: **Essential guide for manual UI setup in the notebook.**
*   **`UI_SETUP_QUICKSTART.md`**: Abridged version of the manual setup guide.
*   **`DEVELOPER_GUIDE.md`**: In-depth technical details about the project architecture, APIs, extending features, and troubleshooting.

## Security Considerations

Please review the following security considerations when using or developing this project:

*   **IBMQ API Key (`.env` file):** If you use an `IBMQ_API_KEY`, protect your `.env` file. Do not commit it to public repositories.
*   **Jupyter Server Security:** Secure your Jupyter server with a token or password, and avoid exposing it publicly without proper security measures. Refer to Jupyter's official security documentation.
*   **Code Execution from UI (`data-rh-exec` in `qoffee.ipynb`):** The notebook UI allows execution of Python code defined in its templates. Only run notebooks from trusted sources.
*   **Docker Container Security (if used):** Ensure base images are trusted and up-to-date.

(For more details, see the "Security Considerations" section in the [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)).

## For Developers and Advanced Users

*   **Manual UI Setup Guide:** [MANUAL_QOFFEE_IPYNB_SETUP.md](MANUAL_QOFFEE_IPYNB_SETUP.md)
*   **Developer Guide (Technical Details & Architecture):** [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)
*   **Future Development Roadmap:** [PROJECT_ROADMAP.md](PROJECT_ROADMAP.md)

## Installation on RasQberry (Legacy Note)

The "Installation on RasQberry" section below refers to a previous version of this project that had different functionalities. It may not be directly applicable to the current "Quantum Combinatorics Explorer" focus.

---
*Legacy RasQberry instructions removed as they are no longer relevant to the core refocused project.*
