// uls-platform/src/main/preload.ts
import { contextBridge, ipcRenderer } from 'electron';

// Define the API that will be exposed to the renderer process
// This should match the methods we want to call on CausalReasoningService
// and the parameters they expect.
contextBridge.exposeInMainWorld('ccreApi', {
  loadDatasetFromString: (dataCsvString: string, datasetId: string) =>
    ipcRenderer.invoke('ccre:loadDatasetFromString', dataCsvString, datasetId),

  defineCausalModelSimple: (datasetId: string, graphGmlString: string, treatment: string, outcome: string, modelId: string) =>
    ipcRenderer.invoke('ccre:defineCausalModelSimple', datasetId, graphGmlString, treatment, outcome, modelId),

  estimateIdentifiedEffect: (modelId: string, estimatorMethod?: string) =>
    ipcRenderer.invoke('ccre:estimateIdentifiedEffect', modelId, estimatorMethod),

  // We can also expose the testDoWhyWorkflow for debugging from renderer if needed
  testDoWhyWorkflow: () => ipcRenderer.invoke('ccre:testDoWhyWorkflow'),
});

console.log("Preload script (preload.ts) executed and ccreApi exposed.");
