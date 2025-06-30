# Project Chimera - Matter CX.1: Causal & Counterfactual Reasoning Engine (CCRE) - PoC & Electron Integration Summary

## 1. Overview (Updated)

This document summarizes the Proof-of-Concept (PoC) and subsequent initial Electron integration for the Causal and Counterfactual Reasoning Engine (CCRE), a core component of Project Chimera's Matter CX.1. The goal is to demonstrate running a basic causal inference workflow using DoWhy, with the service backend in Electron's main process and a React-based UI in the renderer process.

**Key Objectives Achieved (Updated):**
*   **Basic Service Structure:** `CausalReasoningService` class in TypeScript for Pyodide interaction.
*   **Pyodide Integration:** Service initializes Pyodide and loads `dowhy` and dependencies.
*   **Core API Endpoints:** Service exposes methods for data loading, model definition, and effect estimation.
*   **Electron Main Process Integration:** `CausalReasoningService` is instantiated in the Electron main process (`main.ts`).
*   **IPC Communication:** Electron's IPC ( `ipcMain.handle` and `contextBridge` in `preload.ts`) established for communication between the renderer (UI) and the main process service.
*   **Basic React UI:** A `CausalLabView.tsx` React component provides a UI to interact with the service via IPC.
*   **Renderer Setup:** Basic React app structure (`index.html`, `App.tsx`, `renderer.tsx`) to host `CausalLabView`.
*   **State Management (PoC):** Python objects (DataFrames, CausalModels) are stored in Pyodide's global scope within the main process service, referenced by name.

## 2. System Components (Updated)

*   **`uls-platform/src/services/causalReasoningService.ts`**: TypeScript class for CCRE. Handles Pyodide, DoWhy, and core logic. Runs in Electron Main Process.
*   **`uls-platform/src/main/main.ts`**: Electron main process entry point. Initializes Electron app, BrowserWindow, instantiates `CausalReasoningService`, and sets up IPC handlers.
*   **`uls-platform/src/main/preload.ts`**: Electron preload script. Securely exposes IPC functions (`ccreApi`) to the renderer process.
*   **`uls-platform/src/renderer/index.html`**: Main HTML file for the renderer process.
*   **`uls-platform/src/renderer/App.tsx`**: Root React component.
*   **`uls-platform/src/renderer/renderer.tsx`**: React DOM rendering entry point.
*   **`uls-platform/src/renderer/components/CausalLabView.tsx`**: React component providing the UI for the Causal Lab PoC, interacting with `ccreApi`.

## 3. How to Run (Updated for Electron)

1.  **Environment:**
    *   Node.js and npm/yarn.
    *   Electron (as a project dependency).
    *   A build system for TypeScript and React (e.g., configured with Electron Forge or electron-builder using Vite/Webpack).
    *   Internet connection (if Pyodide still uses CDN for packages/main files).
2.  **Build & Run:**
    *   Install dependencies: `npm install` or `yarn install`.
    *   Compile TypeScript (main, preload, renderer) and bundle React app using your project's build commands (e.g., `npm run make`, `npm run start`, `yarn electron:dev`).
    *   Launch the Electron application (e.g., `npm start` or by running the built executable).
3.  **Developer Consoles:**
    *   **Main Process:** Observe terminal output where you launched Electron.
    *   **Renderer Process:** Open via "View" > "Toggle Developer Tools" in the Electron app menu.
4.  **Interact with the UI (`CausalLabView`):**
    *   The UI should indicate CCRE API availability.
    *   Use the input fields to provide data (CSV string), graph (GML string), and parameters.
    *   Click "Load Dataset," "Define Model & Identify Effect," and "Estimate Effect" in sequence.
    *   Observe outputs and status messages in the UI and check both consoles for detailed logs and errors.

## 4. Current State & Known Limitations (Updated)

*   **Functionality:** Basic causal workflow (load data -> define model -> identify -> estimate) is functional via Electron IPC.
*   **Error Handling:** Basic error propagation from service to UI. UI shows loading states and disables buttons during operations.
*   **UI:** React-based but still minimal, focused on testing the Electron workflow.
*   **Pyodide in Main Process:** The PoC attempts to run standard Pyodide in the main process. This remains a point for careful observation during testing. **If issues arise (performance, stability, resource management, `fetch` compatibility), migrating `CausalReasoningService` to use `pyodide-node` is the primary recommended refinement.**
*   **State Management:** Still PoC-level (Pyodide globals).
*   **Performance:** Pyodide initialization in the main process and subsequent Python execution will impact main process responsiveness if not handled carefully (though `async` methods help). Long operations could still make the service temporarily unresponsive to new IPC calls if Pyodide itself is blocking within an async Python task.
*   **Build System Assumption:** This documentation assumes a standard Electron build system is in place to compile TypeScript, bundle React, and correctly structure paths for `preload.js` and `index.html`.

## 5. Potential Roadblocks (Updated Title)

*   **Pyodide in Electron Main:** As highlighted, standard Pyodide might have limitations in a Node.js environment. `pyodide-node` is a likely solution if problems occur. This could involve changes to how Pyodide is loaded/used and how its file system for packages is accessed.
*   **Pathing in Packaged App:** Ensuring correct paths to `preload.js` and `index.html` (and any Pyodide assets if vendored locally) in a packaged Electron app (`asar` archives) requires careful build tool configuration.
*   **IPC Data Serialization:** Electron's IPC handles common data types well. Very large datasets or complex, non-serializable objects (if returned directly from Python without conversion) could cause issues. Current PoC returns JSON-friendly data.

## 6. Next Steps for Expanding the CCRE (Largely Same, Context Updated)

The next steps remain broadly similar to the previous PoC outline, but now within the context of an established Electron application structure:

1.  **Refine Pyodide Setup (if needed):** Based on testing, switch to `pyodide-node` in `CausalReasoningService` if standard Pyodide proves problematic in the main process. This might involve local vendoring of Pyodide files.
2.  **Improved State Management:** Implement robust state management for datasets and models within `CausalReasoningService`.
3.  **Enhanced UI Features (React):**
    *   Interactive causal graph visualization/editor (e.g., Cytoscape.js integrated into a React component).
    *   Better display of results (React data grids, charting libraries).
    *   User-friendly input forms with validation.
4.  **Expand Estimator Support (DoWhy & CausalML):** Integrate more estimation methods.
5.  **Counterfactual & Refutation APIs:** Implement service methods and UI interactions for counterfactual queries and DoWhy's refutation methods.
6.  **True Asynchronous Operations:** If Pyodide tasks in the main process block it for too long, explore moving Pyodide execution to a utility process or a hidden renderer process acting as a worker, communicating back to the main service via IPC. This is more complex than Web Workers directly in the main process.
7.  **Error Handling & AI Guidance:** More comprehensive error handling, and integration with the AI Core for user guidance.
8.  **Testing:** Formal unit tests for `CausalReasoningService`, integration tests for IPC, and E2E tests using an Electron testing framework (e.g., Playwright, Spectron).
9.  **Local Vendoring of Pyodide (if not done in step 1):** Ensure Pyodide and its packages are part of the application bundle for offline use and version consistency.

This phase has successfully laid the groundwork for a more robust CCRE within the ULS Electron application.
