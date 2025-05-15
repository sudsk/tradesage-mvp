import React, { useEffect, useState } from 'react';
import TradingDashboard from './components/TradingDashboard';
import './index.css';

function App() {
  const [isLoading, setIsLoading] = useState(true);
  const [theme, setTheme] = useState('light');

  useEffect(() => {
    // Simulate app initialization
    const initializeApp = async () => {
      // Check for saved theme preference
      const savedTheme = localStorage.getItem('tradeSageTheme') || 'light';
      setTheme(savedTheme);
      
      // Apply theme to document
      document.documentElement.className = savedTheme;
      
      // Simulate loading time
      await new Promise(resolve => setTimeout(resolve, 1000));
      setIsLoading(false);
    };

    initializeApp();
  }, []);

  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
    localStorage.setItem('tradeSageTheme', newTheme);
    document.documentElement.className = newTheme;
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 flex items-center justify-center">
        <div className="text-center">
          {/* Enhanced loading animation */}
          <div className="relative mb-8">
            <div className="w-20 h-20 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
            <div className="w-16 h-16 border-4 border-purple-600 border-t-transparent rounded-full animate-spin absolute top-2 left-2" style={{animationDirection: 'reverse', animationDuration: '0.8s'}}></div>
            <div className="w-12 h-12 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin absolute top-4 left-4" style={{animationDuration: '0.6s'}}></div>
          </div>
          
          {/* Loading text with gradient */}
          <h1 className="text-4xl font-bold mb-4 text-gradient animate-pulse">
            TradeSage AI
          </h1>
          <p className="text-gray-600 text-lg mb-4">
            Initializing Multi-Agent Trading Analysis
          </p>
          
          {/* Loading dots */}
          <div className="flex justify-center space-x-2">
            <div className="w-3 h-3 bg-blue-600 rounded-full animate-bounce"></div>
            <div className="w-3 h-3 bg-purple-600 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
            <div className="w-3 h-3 bg-indigo-600 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`App min-h-screen ${theme}`}>
      {/* Theme toggle button */}
      <button
        onClick={toggleTheme}
        className="fixed top-4 left-4 z-50 p-3 bg-white dark:bg-slate-800 rounded-full shadow-lg hover:shadow-xl transition-all duration-200 border border-gray-200 dark:border-slate-600 no-print"
        aria-label="Toggle theme"
      >
        {theme === 'light' ? (
          <svg className="w-5 h-5 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
          </svg>
        ) : (
          <svg className="w-5 h-5 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
          </svg>
        )}
      </button>

      {/* Version info */}
      <div className="fixed bottom-4 left-4 z-40 text-xs text-gray-500 no-print">
        TradeSage AI v2.0 - Enhanced UI
      </div>

      {/* Main dashboard */}
      <TradingDashboard />
    </div>
  );
}

export default App;
