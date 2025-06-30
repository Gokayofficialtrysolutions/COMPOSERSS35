// uls-platform/src/renderer/components/CausalLabView.tsx
import React, { useState, useEffect } from 'react';

// Define the structure of the API exposed by preload.ts
// This helps with TypeScript type checking in the renderer.
declare global {
  interface Window {
    ccreApi: {
      loadDatasetFromString: (dataCsvString: string, datasetId: string) => Promise<{ status: string; columns?: string[]; error?: string }>;
      defineCausalModelSimple: (datasetId: string, graphGmlString: string, treatment: string, outcome: string, modelId: string) => Promise<{ model_id_ref?: string; status: string; identified_estimand_str?: string; error?: string }>;
      estimateIdentifiedEffect: (modelId: string, estimatorMethod?: string) => Promise<{ results?: any; status: string; error?: string }>;
      testDoWhyWorkflow: () => Promise<any>; // For debugging if needed
    };
  }
}

const CausalLabView: React.FC = () => {
  // State for inputs
  const [csvData, setCsvData] = useState<string>(`Z,X,Y\n0,0,1.2\n1,0,2.5\n0,1,3.1\n1,1,4.8\n0,0,1.5\n1,1,5.0\n0,1,2.8\n1,0,2.1`);
  const [datasetId, setDatasetId] = useState<string>('react_poc_data_01');
  const [gmlData, setGmlData] = useState<string>(`graph [\n  directed 1\n  node [ id "Z" label "Z" ]\n  node [ id "X" label "X" ]\n  node [ id "Y" label "Y" ]\n  edge [ source "Z" target "X" ]\n  edge [ source "Z" target "Y" ]\n  edge [ source "X" target "Y" ]\n]`);
  const [treatmentVar, setTreatmentVar] = useState<string>('X');
  const [outcomeVar, setOutcomeVar] = useState<string>('Y');
  const [modelId, setModelId] = useState<string>('react_poc_model_01');
  const [estimatorMethod, setEstimatorMethod] = useState<string>('backdoor.linear_regression');

  // State for outputs/status
  const [loadDataOutput, setLoadDataOutput] = useState<string | null>(null);
  const [loadDataStatus, setLoadDataStatus] = useState<'success' | 'error' | null>(null);

  const [defineModelOutput, setDefineModelOutput] = useState<string | null>(null);
  const [defineModelStatus, setDefineModelStatus] = useState<'success' | 'error' | null>(null);

  const [estimateEffectOutput, setEstimateEffectOutput] = useState<string | null>(null);
  const [estimateEffectStatus, setEstimateEffectStatus] = useState<'success' | 'error' | null>(null);

  const [isLoadingData, setIsLoadingData] = useState<boolean>(false);
  const [isDefiningModel, setIsDefiningModel] = useState<boolean>(false);
  const [isEstimatingEffect, setIsEstimatingEffect] = useState<boolean>(false);

  const [initializationStatus, setInitializationStatus] = useState<string>("Initializing CCRE Interface...");
  const [isApiAvailable, setIsApiAvailable] = useState<boolean | null>(null);

  useEffect(() => {
    if (window.ccreApi) {
        setInitializationStatus("CCRE API connection established. Pyodide initialization occurs in the main Electron process and may take time. UI is ready for interaction.");
        setIsApiAvailable(true);
    } else {
        setInitializationStatus("CCRE API (window.ccreApi) not found. This UI component will not function. Ensure the Electron preload script is correctly configured and the app is running within Electron.");
        setIsApiAvailable(false);
    }
  }, []);


  const handleLoadData = async () => {
    if (!window.ccreApi) {
      setLoadDataOutput("Error: CCRE API not available. Cannot load dataset.");
      setLoadDataStatus('error');
      return;
    }
    setIsLoadingData(true);
    setLoadDataOutput('Loading dataset via IPC to main process...');
    setLoadDataStatus(null);
    try {
      const result = await window.ccreApi.loadDatasetFromString(csvData, datasetId);
      if (result.error) throw new Error(result.error);
      setLoadDataOutput(`Dataset loaded. Columns: ${(result.columns || []).join(', ')}`);
      setLoadDataStatus('success');
    } catch (e: any) {
      setLoadDataOutput(`Error loading dataset: ${e.message || String(e)}`);
      setLoadDataStatus('error');
    } finally {
      setIsLoadingData(false);
    }
  };

  const handleDefineModel = async () => {
    if (!window.ccreApi) {
      setDefineModelOutput("Error: CCRE API not available. Cannot define model.");
      setDefineModelStatus('error');
      return;
    }
    setIsDefiningModel(true);
    setDefineModelOutput('Defining model and identifying effect via IPC...');
    setDefineModelStatus(null);
    try {
      const result = await window.ccreApi.defineCausalModelSimple(datasetId, gmlData, treatmentVar, outcomeVar, modelId);
      if (result.error) throw new Error(result.error);
      setDefineModelOutput(`Model defined (ID: ${result.model_id_ref}). Identified Estimand: <pre>${result.identified_estimand_str}</pre>`);
      setDefineModelStatus('success');
    } catch (e: any) {
      setDefineModelOutput(`Error defining model: ${e.message || String(e)}`);
      setDefineModelStatus('error');
    } finally {
      setIsDefiningModel(false);
    }
  };

  const handleEstimateEffect = async () => {
    if (!window.ccreApi) {
      setEstimateEffectOutput("Error: CCRE API not available. Cannot estimate effect.");
      setEstimateEffectStatus('error');
      return;
    }
    setIsEstimatingEffect(true);
    setEstimateEffectOutput('Estimating effect via IPC...');
    setEstimateEffectStatus(null);
    try {
      const result = await window.ccreApi.estimateIdentifiedEffect(modelId, estimatorMethod);
      if (result.error) throw new Error(result.error);
      setEstimateEffectOutput(`Estimation Complete: <pre>${JSON.stringify(result.results, null, 2)}</pre>`);
      setEstimateEffectStatus('success');
    } catch (e: any) {
      setEstimateEffectOutput(`Error estimating effect: ${e.message || String(e)}`);
      setEstimateEffectStatus('error');
    } finally {
      setIsEstimatingEffect(false);
    }
  };

  const styles = {
    container: { padding: '20px', fontFamily: 'sans-serif', backgroundColor: '#f9f9f9', color: '#333' },
    section: { backgroundColor: '#fff', padding: '15px', marginBottom: '15px', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' },
    label: { display: 'block', marginTop: '10px', fontWeight: 'bold', marginBottom: '5px' } as React.CSSProperties,
    textarea: { width: 'calc(100% - 16px)', padding: '8px', marginTop: '5px', borderRadius: '4px', border: '1px solid #ddd', fontFamily: 'monospace', minHeight: '80px' },
    input: { width: 'calc(100% - 16px)', padding: '8px', marginTop: '5px', borderRadius: '4px', border: '1px solid #ddd' },
    button: {
      backgroundColor: '#007bff', color: 'white', padding: '10px 15px',
      border: 'none', borderRadius: '4px', cursor: 'pointer',
      marginTop: '15px', marginRight: '10px',
      opacity: 1, transition: 'opacity 0.3s ease'
    } as React.CSSProperties,
    buttonDisabled: {
        backgroundColor: '#007bff', color: 'white', padding: '10px 15px',
        border: 'none', borderRadius: '4px', cursor: 'not-allowed',
        marginTop: '15px', marginRight: '10px',
        opacity: 0.6,
    } as React.CSSProperties,
    status: { marginTop: '10px', padding: '10px', borderRadius: '4px', border: '1px solid transparent', whiteSpace: 'pre-wrap', wordWrap: 'break-word', fontSize: '0.9em' } as React.CSSProperties,
    info: { backgroundColor: '#e7f3fe', color: '#0c5460', borderColor: '#b8daff'},
    success: { backgroundColor: '#d4edda', color: '#155724', borderColor: '#c3e6cb' },
    error: { backgroundColor: '#f8d7da', color: '#721c24', borderColor: '#f5c6cb' },
  };

  const getStatusStyle = (status: 'success' | 'error' | null) => {
    if (status === 'success') return styles.success;
    if (status === 'error') return styles.error;
    return styles.info; // Default to info style for neutral messages
  };

  return (
    <div style={styles.container}>
      <h1>Causal Lab (React PoC)</h1>
      <div style={{...styles.status, ...(isApiAvailable === false ? styles.error : styles.info)}}>
        {initializationStatus}
      </div>

      <div style={styles.section}>
        <h2>1. Load Data</h2>
        <label htmlFor="csvData" style={styles.label}>Paste CSV Data:</label>
        <textarea id="csvData" style={styles.textarea} value={csvData} onChange={(e) => setCsvData(e.target.value)} disabled={isLoadingData || isApiAvailable === false} />
        <label htmlFor="datasetId" style={styles.label}>Dataset ID:</label>
        <input type="text" id="datasetId" style={styles.input} value={datasetId} onChange={(e) => setDatasetId(e.target.value)} disabled={isLoadingData || isApiAvailable === false} />
        <button onClick={handleLoadData} style={isLoadingData || isApiAvailable === false ? styles.buttonDisabled : styles.button} disabled={isLoadingData || isApiAvailable === false}>
          {isLoadingData ? 'Loading...' : 'Load Dataset'}
        </button>
        {loadDataOutput && (
          <div style={{...styles.status, ...getStatusStyle(loadDataStatus)}}
               dangerouslySetInnerHTML={{ __html: loadDataOutput }} />
        )}
      </div>

      <div style={styles.section}>
        <h2>2. Define Causal Model</h2>
        <label htmlFor="gmlData" style={styles.label}>Paste GML Graph Data:</label>
        <textarea id="gmlData" style={styles.textarea} value={gmlData} onChange={(e) => setGmlData(e.target.value)} disabled={isDefiningModel || isApiAvailable === false} />
        <label htmlFor="treatmentVar" style={styles.label}>Treatment Variable:</label>
        <input type="text" id="treatmentVar" style={styles.input} value={treatmentVar} onChange={(e) => setTreatmentVar(e.target.value)} disabled={isDefiningModel || isApiAvailable === false} />
        <label htmlFor="outcomeVar" style={styles.label}>Outcome Variable:</label>
        <input type="text" id="outcomeVar" style={styles.input} value={outcomeVar} onChange={(e) => setOutcomeVar(e.target.value)} disabled={isDefiningModel || isApiAvailable === false} />
        <label htmlFor="modelId" style={styles.label}>Model ID:</label>
        <input type="text" id="modelId" style={styles.input} value={modelId} onChange={(e) => setModelId(e.target.value)} disabled={isDefiningModel || isApiAvailable === false} />
        <button onClick={handleDefineModel} style={isDefiningModel || isApiAvailable === false ? styles.buttonDisabled : styles.button} disabled={isDefiningModel || isApiAvailable === false}>
          {isDefiningModel ? 'Defining...' : 'Define Model & Identify Effect'}
        </button>
        {defineModelOutput && (
          <div style={{...styles.status, ...getStatusStyle(defineModelStatus)}}
               dangerouslySetInnerHTML={{ __html: defineModelOutput }} />
        )}
      </div>

      <div style={styles.section}>
        <h2>3. Estimate Effect</h2>
        <label htmlFor="estimatorMethod" style={styles.label}>Estimator Method:</label>
        <input type="text" id="estimatorMethod" style={styles.input} value={estimatorMethod} onChange={(e) => setEstimatorMethod(e.target.value)} disabled={isEstimatingEffect || isApiAvailable === false} />
        <button onClick={handleEstimateEffect} style={isEstimatingEffect || isApiAvailable === false ? styles.buttonDisabled : styles.button} disabled={isEstimatingEffect || isApiAvailable === false}>
          {isEstimatingEffect ? 'Estimating...' : 'Estimate Effect'}
        </button>
        {estimateEffectOutput && (
          <div style={{...styles.status, ...getStatusStyle(estimateEffectStatus)}}
               dangerouslySetInnerHTML={{ __html: estimateEffectOutput }} />
        )}
      </div>
    </div>
  );
};

export default CausalLabView;
