# Project Chimera - Matter CX.1: Causal & Counterfactual Reasoning Engine (CCRE) - PoC, Electron Integration, and Pyodide Setup Summary

## 1. Overview (Updated)

This document summarizes the Proof-of-Concept (PoC), initial Electron integration, and Pyodide setup strategy for the Causal and Counterfactual Reasoning Engine (CCRE), a core component of Project Chimera's Matter CX.1. The goal is to run a basic causal inference workflow using DoWhy, with the `CausalReasoningService` (utilizing an npm-installed `pyodide` package) in Electron's main process and a React-based UI in the renderer process.

**Key Objectives Achieved (Updated):**
*   **Basic Service Structure:** `CausalReasoningService` class in TypeScript.
*   **Pyodide Integration (npm-based):** `CausalReasoningService` now imports `loadPyodide` from the `pyodide` npm package. It attempts to initialize Pyodide using its default mechanism for finding core files (typically from `node_modules/pyodide/build/`). Python packages (`dowhy`, `pandas`, etc.) are loaded via `pyodide.loadPackage()`, which defaults to fetching wheels from Pyodide's CDN.
*   **Core API Endpoints:** Service exposes methods for data loading, model definition, and effect estimation.
*   **Electron Main Process Integration:** `CausalReasoningService` is instantiated in `main.ts`.
*   **IPC Communication:** Electron's IPC (`ipcMain.handle`, `contextBridge` in `preload.ts`) connects the renderer UI to the main process service.
*   **Basic React UI:** `CausalLabView.tsx` provides a UI for service interaction.
*   **Renderer Setup:** Basic React app structure (`index.html`, `App.tsx`, `renderer.tsx`).
*   **Strategy for Local Pyodide Distribution:** A plan is in place for future work to copy Pyodide core files into the packaged app and use a local `indexURL` for robust offline capability.

## 2. System Components (Updated)

*   **`uls-platform/src/services/causalReasoningService.ts`**: Handles Pyodide (via npm import), DoWhy, and core logic. Runs in Electron Main Process.
*   **`uls-platform/src/main/main.ts`**: Electron main process entry point.
*   **`uls-platform/src/main/preload.ts`**: Electron preload script exposing `ccreApi`.
*   **`uls-platform/src/renderer/index.html`**: Main HTML for renderer.
*   **`uls-platform/src/renderer/App.tsx`**: Root React component.
*   **`uls-platform/src/renderer/renderer.tsx`**: React DOM rendering.
*   **`uls-platform/src/renderer/components/CausalLabView.tsx`**: React UI for Causal Lab PoC.

## 3. How to Run (Updated for Electron & npm `pyodide`)

1.  **Prerequisites:**
    *   Node.js and npm/yarn.
    *   Project dependencies installed (run `npm install` or `yarn install` to get `electron`, `react`, `pyodide`, etc., as defined in `package.json`).
    *   A build system for TypeScript/React (e.g., Electron Forge with Vite/Webpack).
    *   Internet connection (still needed for `pyodide.loadPackage()` to fetch Python package wheels from CDN by default).
2.  **Build & Run:**
    *   Compile TypeScript and bundle React app via project build commands.
    *   Launch Electron app (e.g., `npm start`).
3.  **Developer Consoles:** Monitor main process (terminal) and renderer process (DevTools) consoles.
4.  **Interact with UI (`CausalLabView`):** Test the workflow (load data, define model, estimate effect).

## 4. Current State & Known Limitations (Updated)

*   **Functionality:** Basic causal workflow via Electron IPC using npm-imported `pyodide`.
*   **Pyodide Setup in Main Process:**
    *   Uses standard `pyodide` npm package. The research indicated a separate `pyodide-node` package is not the current primary solution.
    *   `loadPyodide()` is called without `indexURL`, relying on Pyodide to find its core files from `node_modules/pyodide/build/`. This generally works in development but is **not robust for packaged applications or offline use.**
    *   Python packages (`dowhy`, etc.) are still fetched from CDN by `pyodide.loadPackage()` by default.
*   **Performance:** Pyodide initialization and CDN package loading impact startup. CPU-intensive Python in main process can affect responsiveness.
*   **Next Step for Robustness:** The immediate next step for Pyodide setup is to implement local distribution of its *core files* (Wasm, stdlib) by configuring the build system to copy them into the app package and updating `CausalReasoningService` to use a local `indexURL` (e.g., `file://.../pyodide_dist/`). Local vendoring of *Python packages* is a subsequent optimization.

## 5. Potential Roadblocks (Updated)

*   **Default Pyodide File Loading in Packaged App:** `loadPyodide()` without `indexURL` might fail to find core files in a packaged Electron app (e.g., inside `asar`). Using a local `indexURL` after copying files is the planned mitigation.
*   **Pathing for Local `indexURL`:** Correctly determining the runtime path to locally vendored Pyodide files (for `indexURL`) in both development and packaged modes requires careful `path.join` and potentially `app.isPackaged` logic.
*   **Network Dependency for Packages:** `pyodide.loadPackage()` still hitting CDN is a limitation for offline use until Python package wheels are also vendored locally.

## 6. Next Steps for Expanding the CCRE (Focus Refined)

1.  **Implement Local Pyodide Core File Distribution:**
    *   Configure the build system (e.g., Vite/Webpack via Electron Forge/Builder) to copy `node_modules/pyodide/build/*` to a distributable location (e.g., `pyodide_dist/` within the app's resources).
    *   Modify `CausalReasoningService.initializePyodide()` to use `loadPyodide({ indexURL: "path/to/local/pyodide_dist/" })`.
2.  **Local Python Package Vendoring:**
    *   Download `.whl` files for `dowhy`, `pandas`, and all dependencies.
    *   Copy them into the app package via the build system.
    *   Modify `CausalReasoningService` to use `micropip.add_mock_package()` or install wheels from local paths (e.g., `emfs:` paths if files are in Pyodide's virtual FS, or by loading them into memory and installing).
3.  **Refine Pyodide Setup (if `pyodide-node` benefits emerge):** While standard `pyodide` is the current path, if specific Node.js environment issues persist that `pyodide-node` (if a stable, maintained version exists and offers advantages) demonstrably solves better, re-evaluate. *Current assessment is standard `pyodide` is preferred.*
4.  **Improved State Management in `CausalReasoningService`**.
5.  **Enhanced UI Features (React)**: Graph visualization, better results display, etc.
6.  **Expand Estimator Support & Add Counterfactual/Refutation APIs**.
7.  **True Asynchronous Operations for Long Tasks** (e.g., utility process).
8.  **Comprehensive Error Handling & AI Guidance**.
9.  **Full Testing Suite**.

This phase has adapted the CCRE service to use the npm `pyodide` package and outlined the critical path towards a fully local and robust Pyodide setup within Electron.
