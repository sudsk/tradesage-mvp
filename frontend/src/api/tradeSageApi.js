// frontend/src/api/tradeSageApi.js
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

class TradeSageAPI {
  async processHypothesis(data) {
    try {
      const response = await fetch(`${API_BASE_URL}/process`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error processing hypothesis:', error);
      throw error;
    }
  }
  
  async generateHypothesis(context) {
    return this.processHypothesis({
      mode: 'generate',
      context: context
    });
  }
  
  async refineIdea(idea) {
    return this.processHypothesis({
      mode: 'refine',
      idea: idea
    });
  }
  
  async analyzeHypothesis(hypothesis) {
    return this.processHypothesis({
      mode: 'analyze',
      hypothesis: hypothesis
    });
  }
  
  async healthCheck() {
    try {
      const response = await fetch(`${API_BASE_URL}/health`);
      return await response.json();
    } catch (error) {
      console.error('Health check failed:', error);
      throw error;
    }
  }
}

export default new TradeSageAPI();