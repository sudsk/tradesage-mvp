// Create src/components/TradeSageInterface.jsx
import React, { useState, useEffect } from 'react';
import TradeSageAPI from '../api/tradeSageApi';

const TradeSageInterface = () => {
  const [mode, setMode] = useState('analyze');
  const [input, setInput] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    TradeSageAPI.healthCheck()
      .then(res => console.log('API Status:', res))
      .catch(err => console.error('API Health Check Failed:', err));
  }, []);
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    try {
      const requestData = { mode };
      
      if (mode === 'generate') {
        requestData.context = {
          sectors: ['technology', 'healthcare'],
          timeframe: 'quarterly',
          risk_tolerance: 'moderate'
        };
      } else if (mode === 'refine') {
        requestData.idea = input;
      } else {
        requestData.hypothesis = input;
      }
      
      const response = await TradeSageAPI.processHypothesis(requestData);
      setResult(response);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="container">
      <div className="card">
        <h1 className="title">TradeSage AI</h1>
        
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Analysis Mode</label>
            <select value={mode} onChange={(e) => setMode(e.target.value)}>
              <option value="analyze">Analyze Hypothesis</option>
              <option value="refine">Refine Trading Idea</option>
              <option value="generate">Generate New Hypothesis</option>
            </select>
          </div>
          
          {mode === 'generate' ? (
            <div className="result-section">
              <p>When you select "Generate", the system will create a new trading hypothesis based on current market conditions.</p>
            </div>
          ) : (
            <div className="form-group">
              <label>{mode === 'refine' ? 'Trading Idea' : 'Hypothesis'}</label>
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={
                  mode === 'refine' 
                    ? "Enter your rough trading idea..."
                    : "Enter your structured hypothesis..."
                }
                required
              />
            </div>
          )}
          
          <button type="submit" disabled={loading} className="btn">
            {loading ? 'Processing...' : 'Analyze'}
          </button>
        </form>
        
        {error && (
          <div className="error">
            <strong>Error:</strong> {error}
          </div>
        )}
        
        {result && (
          <div>
            <div className="result-section">
              <div className="result-title">Processed Hypothesis</div>
              <div className="result-content">{result.processed_hypothesis}</div>
            </div>
            
            <div className="result-section">
              <div className="result-title">Research Summary</div>
              <div className="result-content">
                {result.research?.summary || 'No research data available'}
              </div>
            </div>
            
            {result.contradictions?.length > 0 && (
              <div className="result-section">
                <div className="result-title">Challenges & Contradictions</div>
                <div className="result-content">
                  <ul>
                    {result.contradictions.map((item, index) => (
                      <li key={index}>{item.content || item}</li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
            
            <div className="result-section">
              <div className="result-title">Analysis Synthesis</div>
              <div className="result-content">{result.synthesis}</div>
            </div>
            
            {result.alerts?.length > 0 && (
              <div className="result-section">
                <div className="result-title">Alerts & Recommendations</div>
                <div className="result-content">
                  <ul>
                    {result.alerts.map((alert, index) => (
                      <li key={index}>{alert.message || alert}</li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
            
            <div className="result-section">
              <div className="result-title">Final Recommendations</div>
              <div className="result-content">{result.recommendations}</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default TradeSageInterface;