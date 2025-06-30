// uls-platform/src/renderer/renderer.tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

// This is the entry point for the React application in the Electron renderer process.

const rootElement = document.getElementById('root');
if (rootElement) {
  const root = ReactDOM.createRoot(rootElement);
  root.render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
  console.log('React app mounted successfully.');
} else {
  console.error('Root element (#root) not found in index.html. React app cannot be mounted.');
  // You might want to display an error message to the user in the HTML body itself
  // if the #root element is missing, as React won't be able to render.
  const errorDiv = document.createElement('div');
  errorDiv.innerHTML = `
    <div style="font-family: sans-serif; padding: 20px; text-align: center; background-color: #ffdddd; border: 1px solid #ffaaaa; color: #d8000c;">
      <h1>Application Error</h1>
      <p>The core application element (#root) is missing. The application cannot start.</p>
      <p>Please check the console for more details or contact support.</p>
    </div>
  `;
  document.body.appendChild(errorDiv);
}
