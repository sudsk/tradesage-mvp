// frontend/src/App.js
import React from 'react';
import TradingDashboard from './components/TradingDashboard';
import './App.css';
import './fallback.css'; // Fallback CSS in case Tailwind doesn't load

function App() {
  return (
    <div className="App">
      <TradingDashboard />
    </div>
  );
}

export default App;
