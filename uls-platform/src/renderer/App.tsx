// uls-platform/src/renderer/App.tsx
import React from 'react';
import CausalLabView from './components/CausalLabView';

const App: React.FC = () => {
  const appStyles: React.CSSProperties = {
    margin: 0,
    padding: 0,
    boxSizing: 'border-box',
    backgroundColor: '#e0e0e0',
    minHeight: '100vh',
    display: 'flex',
    flexDirection: 'column',
  };

  const headerStyles: React.CSSProperties = {
    backgroundColor: '#2c3e50', // Darker, more professional header
    color: 'white',
    padding: '15px 20px',
    textAlign: 'center',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
  };

  const mainContentStyles: React.CSSProperties = {
    flexGrow: 1,
    padding: '20px', // Add padding around the main content area
  };

  return (
    <div style={appStyles}>
      <header style={headerStyles}>
        <h1>Unified Laboratories Suite (ULS) - Project Chimera</h1>
      </header>
      <main style={mainContentStyles}>
        {/* In a real app, you'd have routing here to different labs/views */}
        {/* For this PoC, we directly render CausalLabView */}
        <CausalLabView />
      </main>
      {/* Footer or other common elements could go here */}
    </div>
  );
};

export default App;
