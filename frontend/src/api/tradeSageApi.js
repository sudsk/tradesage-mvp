// frontend/src/api/tradeSageApi.js
const API_BASE_URL = process.env.REACT_APP_API_URL || '';

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
  
  // New dashboard endpoints
  async getDashboardData() {
    try {
      const response = await fetch(`${API_BASE_URL}/dashboard`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      throw error;
    }
  }
  
  async getHypothesisDetail(hypothesisId) {
    try {
      const response = await fetch(`${API_BASE_URL}/hypothesis/${hypothesisId}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching hypothesis detail:', error);
      throw error;
    }
  }
  
  async getAlerts() {
    try {
      const response = await fetch(`${API_BASE_URL}/alerts`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching alerts:', error);
      throw error;
    }
  }
  
  async markAlertAsRead(alertId) {
    try {
      const response = await fetch(`${API_BASE_URL}/alerts/${alertId}/read`, {
        method: 'PATCH',
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error marking alert as read:', error);
      throw error;
    }
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
