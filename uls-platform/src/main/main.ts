// uls-platform/src/main/main.ts
import { app, BrowserWindow, ipcMain } from 'electron';
import * as path from 'path';
import { CausalReasoningService } from '../services/causalReasoningService';

let mainWindow: BrowserWindow | null = null;
let causalServiceInstance: CausalReasoningService | null = null;

// IPC Handlers Setup
function setupIpcHandlers() {
  if (!causalServiceInstance) {
    console.error("Electron Main: CausalServiceInstance is not available for IPC setup! This should not happen if setupIpcHandlers is called after instance creation.");
    return;
  }
  const service = causalServiceInstance;

  ipcMain.handle('ccre:loadDatasetFromString', async (_event, dataCsvString: string, datasetId: string) => {
    console.log(`Electron Main IPC: Received ccre:loadDatasetFromString for ${datasetId}`);
    try {
      return await service.loadDatasetFromString(dataCsvString, datasetId);
    } catch (e: any) {
      console.error(`Electron Main IPC: Error in loadDatasetFromString for ${datasetId}:`, e.message || e);
      return { status: "error", error: e.message || String(e) };
    }
  });

  ipcMain.handle('ccre:defineCausalModelSimple', async (_event, datasetId: string, graphGmlString: string, treatment: string, outcome: string, modelId: string) => {
    console.log(`Electron Main IPC: Received ccre:defineCausalModelSimple for ${modelId}`);
    try {
      return await service.defineCausalModelSimple(datasetId, graphGmlString, treatment, outcome, modelId);
    } catch (e: any) {
      console.error(`Electron Main IPC: Error in defineCausalModelSimple for ${modelId}:`, e.message || e);
      return { status: "error", error: e.message || String(e) };
    }
  });

  ipcMain.handle('ccre:estimateIdentifiedEffect', async (_event, modelId: string, estimatorMethod?: string) => {
    console.log(`Electron Main IPC: Received ccre:estimateIdentifiedEffect for ${modelId}`);
    try {
      return await service.estimateIdentifiedEffect(modelId, estimatorMethod);
    } catch (e: any) {
      console.error(`Electron Main IPC: Error in estimateIdentifiedEffect for ${modelId}:`, e.message || e);
      return { status: "error", error: e.message || String(e) };
    }
  });

  ipcMain.handle('ccre:testDoWhyWorkflow', async (_event) => {
    console.log(`Electron Main IPC: Received ccre:testDoWhyWorkflow`);
    try {
      return await service.testDoWhyWorkflow();
    } catch (e: any) {
      console.error(`Electron Main IPC: Error in testDoWhyWorkflow:`, e.message || e);
      return { error: e.message || String(e) };
    }
  });
  console.log("Electron Main: IPC Handlers for CCRE successfully set up.");
}


function createWindow(): void {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  // Determine the path to index.html.
  // For development, this might be a URL to a dev server (e.g., Vite, Webpack Dev Server).
  // For production, this will be a file path.
  let loadUrlOrFile: string;
  if (process.env.NODE_ENV === 'development' && process.env.ELECTRON_RENDERER_URL) {
    loadUrlOrFile = process.env.ELECTRON_RENDERER_URL; // URL from dev server
    console.log(`Electron Main: Loading renderer from dev server: ${loadUrlOrFile}`);
    mainWindow.loadURL(loadUrlOrFile);
  } else {
    // Path for packaged app. Assumes index.html is in a 'renderer' folder sibling to 'main' folder in the output.
    // e.g., out/main/main.js, out/renderer/index.html
    // __dirname here would be out/main/
    loadUrlOrFile = path.join(__dirname, '../renderer/index.html');
    console.log(`Electron Main: Loading renderer from file: ${loadUrlOrFile}`);
    mainWindow.loadFile(loadUrlOrFile)
      .then(() => console.log(`Electron Main: Loaded ${loadUrlOrFile}`))
      .catch(err => console.error(`Electron Main: Error loading ${loadUrlOrFile}:`, err));
  }
  console.log("Electron Main: BrowserWindow created.");

  // Open DevTools - useful for development, should be conditional for production.
  if (process.env.NODE_ENV === 'development' || process.env.DEBUG_PROD === 'true') {
    mainWindow.webContents.openDevTools();
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

app.on('ready', async () => {
  console.log("Electron Main: App is ready.");

  console.log("Electron Main: Instantiating CausalReasoningService...");
  causalServiceInstance = new CausalReasoningService();

  // Setup IPC handlers after service is instantiated
  setupIpcHandlers();

  try {
    console.log("Electron Main: Ensuring Pyodide is initialized by CausalReasoningService...");
    const pyodideInitialized = await causalServiceInstance.ensurePyodideInitialized();
    if (pyodideInitialized) {
      console.log("Electron Main: CausalReasoningService and Pyodide initialized successfully.");
    } else {
      console.error("Electron Main: CausalReasoningService or Pyodide FAILED to initialize.");
    }
  } catch (error: any) {
    console.error("Electron Main: Error during CausalReasoningService initialization:", error.message || error);
  }

  createWindow();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  }
});

// This function is not strictly needed for export if IPC handlers are defined in the same module scope.
// function getCausalServiceInstance(): CausalReasoningService | null {
//     if (!causalServiceInstance) {
//         console.warn("Electron Main: getCausalServiceInstance called before service is properly initialized!");
//     }
//     return causalServiceInstance;
// }

console.log("Electron Main: main.ts loaded, CausalReasoningService and IPC handlers are being set up.");
