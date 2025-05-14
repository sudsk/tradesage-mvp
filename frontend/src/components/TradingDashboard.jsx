import React, { useState, useEffect } from 'react';
import TradeSageAPI from '../api/tradeSageApi';
import Notification from './Notification';

const TradingDashboard = () => {
  const [hypotheses, setHypotheses] = useState([]);
  const [selectedHypothesis, setSelectedHypothesis] = useState(null);
  const [activeTab, setActiveTab] = useState('analysis');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [notification, setNotification] = useState(null);
  
  // Form state
  const [formData, setFormData] = useState({
    mode: 'analyze',
    hypothesis: '',
    idea: '',
    context: ''
  });

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const response = await TradeSageAPI.getDashboardData();
      
      if (response.status === 'success') {
        setHypotheses(response.data);
        if (response.data.length > 0 && !selectedHypothesis) {
          setSelectedHypothesis(response.data[0]);
        }
      } else {
        setError('Failed to fetch dashboard data');
      }
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
      setError('Error loading dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const handleFormSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    
    try {
      const payload = formData.mode === 'generate' 
        ? { mode: 'generate', context: formData.context }
        : formData.mode === 'refine'
        ? { mode: 'refine', idea: formData.idea }
        : { mode: 'analyze', hypothesis: formData.hypothesis };

      const response = await TradeSageAPI.processHypothesis(payload);
      
      if (response.status === 'success') {
        setShowForm(false);
        setFormData({ mode: 'analyze', hypothesis: '', idea: '', context: '' });
        await fetchDashboardData(); // Refresh dashboard
        
        // Show success notification instead of alert
        setNotification({
          type: 'success',
          message: `Hypothesis processed successfully! Analysis added to dashboard.`
        });
      } else {
        throw new Error(response.error || 'Failed to process hypothesis');
      }
    } catch (err) {
      console.error('Error processing hypothesis:', err);
      setNotification({
        type: 'error',
        message: `Failed to process hypothesis: ${err.message}`
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-16 w-16 border-4 border-blue-500 border-t-transparent"></div>
          <p className="mt-4 text-gray-600 font-medium">Loading TradeSage Dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-red-50 flex items-center justify-center">
        <div className="text-center bg-white p-8 rounded-lg shadow-lg">
          <div className="text-red-500 text-6xl mb-4">⚠️</div>
          <p className="text-xl text-red-600 mb-4 font-semibold">{error}</p>
          <button 
            onClick={fetchDashboardData}
            className="px-6 py-3 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors font-semibold"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  const getStatusColor = (status) => {
    if (status.toLowerCase().includes('schedule')) return 'bg-green-100 text-green-800 border-green-200';
    if (status.toLowerCase().includes('demand')) return 'bg-blue-100 text-blue-800 border-blue-200';
    return 'bg-gray-100 text-gray-800 border-gray-200';
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 70) return 'bg-green-500';
    if (confidence >= 50) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Notification */}
      {notification && (
        <Notification
          message={notification.message}
          type={notification.type}
          onClose={() => setNotification(null)}
        />
      )}
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Enhanced Header */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-8 border border-gray-100">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                TradeSage AI Dashboard
              </h1>
              <p className="text-gray-600 mt-2">Multi-agent contradiction analysis for trading hypotheses</p>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setShowForm(true)}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-semibold focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              >
                ✚ New Analysis
              </button>
              <div className="text-right">
                <div className="text-2xl font-bold text-gray-800">{hypotheses.length}</div>
                <div className="text-sm text-gray-500">Active Hypotheses</div>
              </div>
              <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                <span className="text-white text-xl">📈</span>
              </div>
            </div>
          </div>
        </div>

        {/* Hypothesis Form Modal */}
        {showForm && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-90vh overflow-y-auto">
              <div className="p-6 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <h2 className="text-2xl font-bold text-gray-900">Submit Trading Hypothesis</h2>
                  <button
                    onClick={() => setShowForm(false)}
                    className="text-gray-400 hover:text-gray-600 text-2xl focus:outline-none"
                  >
                    ×
                  </button>
                </div>
              </div>
              
              <form onSubmit={handleFormSubmit} className="p-6">
                <div className="mb-6">
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Analysis Mode
                  </label>
                  <select
                    name="mode"
                    value={formData.mode}
                    onChange={handleInputChange}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
                  >
                    <option value="analyze">Analyze Existing Hypothesis</option>
                    <option value="refine">Refine Trading Idea</option>
                    <option value="generate">Generate New Hypothesis</option>
                  </select>
                </div>

                {formData.mode === 'analyze' && (
                  <div className="mb-6">
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Trading Hypothesis
                    </label>
                    <textarea
                      name="hypothesis"
                      value={formData.hypothesis}
                      onChange={handleInputChange}
                      placeholder="e.g., Bitcoin will reach $100,000 by end of Q2 2025 due to institutional adoption and ETF inflows"
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
                      rows="4"
                      required
                    />
                  </div>
                )}

                {formData.mode === 'refine' && (
                  <div className="mb-6">
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Trading Idea to Refine
                    </label>
                    <textarea
                      name="idea"
                      value={formData.idea}
                      onChange={handleInputChange}
                      placeholder="e.g., I think tech stocks will go up because of AI developments"
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
                      rows="4"
                      required
                    />
                  </div>
                )}

                {formData.mode === 'generate' && (
                  <div className="mb-6">
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Market Context (Optional)
                    </label>
                    <textarea
                      name="context"
                      value={formData.context}
                      onChange={handleInputChange}
                      placeholder="e.g., Current market conditions, sectors of interest, time horizon preferences"
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
                      rows="4"
                    />
                  </div>
                )}

                <div className="flex items-center space-x-4">
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="flex-1 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors font-semibold focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                  >
                    {isSubmitting ? (
                      <span className="flex items-center justify-center">
                        <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent mr-2"></div>
                        Processing...
                      </span>
                    ) : (
                      'Analyze Hypothesis'
                    )}
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowForm(false)}
                    className="px-6 py-3 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors font-semibold focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {hypotheses.length === 0 ? (
          <div className="text-center bg-white p-12 rounded-lg shadow-lg">
            <div className="text-6xl mb-4">📊</div>
            <h2 className="text-2xl font-bold text-gray-800 mb-4">No Hypotheses Found</h2>
            <p className="text-gray-600 mb-6">Start analyzing your first trading hypothesis</p>
            <button 
              onClick={() => setShowForm(true)}
              className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors font-semibold"
            >
              Create Hypothesis
            </button>
          </div>
        ) : (
          <>
            {/* Improved Hypothesis Cards Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6 mb-8">
              {hypotheses.map((hyp) => (
                <div
                  key={hyp.id}
                  className={`bg-white rounded-xl shadow-lg p-6 cursor-pointer transition-all duration-300 hover:shadow-xl border-2 ${
                    selectedHypothesis?.id === hyp.id 
                      ? 'border-blue-500 ring-2 ring-blue-200' 
                      : 'border-gray-100 hover:border-blue-200'
                  }`}
                  onClick={() => setSelectedHypothesis(hyp)}
                >
                  {/* Card Header */}
                  <div className="mb-4">
                    <h3 className="font-bold text-lg text-gray-800 leading-tight mb-3 line-clamp-2">{hyp.title}</h3>
                    <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold border ${getStatusColor(hyp.status)}`}>
                      <div className="w-2 h-2 rounded-full bg-current mr-2"></div>
                      {hyp.status}
                    </div>
                  </div>

                  {/* Metrics Row - Better Spacing */}
                  <div className="grid grid-cols-3 gap-4 mb-4">
                    <div className="text-center bg-red-50 rounded-lg p-3">
                      <div className="text-xl font-bold text-red-600">{hyp.contradictions}</div>
                      <div className="text-xs text-gray-600">Contradictions</div>
                    </div>
                    <div className="text-center bg-green-50 rounded-lg p-3">
                      <div className="text-xl font-bold text-green-600">{hyp.confirmations}</div>
                      <div className="text-xs text-gray-600">Confirmations</div>
                    </div>
                    <div className="text-center bg-blue-50 rounded-lg p-3">
                      <div className="text-xl font-bold text-blue-600">{hyp.confidence}%</div>
                      <div className="text-xs text-gray-600">Confidence</div>
                    </div>
                  </div>

                  {/* Confidence Bar */}
                  <div className="mb-4">
                    <div className="flex justify-between text-sm mb-2">
                      <span className="text-gray-600 font-medium">Confidence Score</span>
                      <span className="font-bold">{hyp.confidence}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-3">
                      <div
                        className={`h-3 rounded-full transition-all duration-700 ${getConfidenceColor(hyp.confidence)}`}
                        style={{ width: `${hyp.confidence}%` }}
                      ></div>
                    </div>
                  </div>

                  {/* Price Info - Better Formatted */}
                  {hyp.trendData && hyp.trendData.length > 0 && (
                    <div className="bg-gray-50 rounded-lg p-3 mb-4">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600 font-medium">Current Price</span>
                        <span className="text-lg font-bold text-gray-800">
                          ${hyp.trendData[hyp.trendData.length - 1]?.value || 'N/A'}
                        </span>
                      </div>
                    </div>
                  )}

                  {/* Last Updated */}
                  <div className="text-xs text-gray-500 text-right">
                    Updated {hyp.lastUpdated}
                  </div>
                </div>
              ))}
            </div>

            {/* Enhanced Detailed Analysis Panel */}
            {selectedHypothesis && (
              <div className="bg-white rounded-xl shadow-lg border border-gray-100">
                {/* Tab Navigation */}
                <div className="border-b border-gray-200">
                  <nav className="flex">
                    <button
                      className={`px-8 py-4 text-sm font-semibold transition-colors relative ${
                        activeTab === 'analysis'
                          ? 'text-blue-600 bg-blue-50'
                          : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                      }`}
                      onClick={() => setActiveTab('analysis')}
                    >
                      <span className="flex items-center">
                        📊 Analysis Breakdown
                      </span>
                      {activeTab === 'analysis' && (
                        <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-600"></div>
                      )}
                    </button>
                    <button
                      className={`px-8 py-4 text-sm font-semibold transition-colors relative ${
                        activeTab === 'trends'
                          ? 'text-blue-600 bg-blue-50'
                          : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                      }`}
                      onClick={() => setActiveTab('trends')}
                    >
                      <span className="flex items-center">
                        📈 Trends & Insights
                      </span>
                      {activeTab === 'trends' && (
                        <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-600"></div>
                      )}
                    </button>
                  </nav>
                </div>

                {/* Tab Content */}
                <div className="p-8">
                  {activeTab === 'analysis' ? (
                    <div>
                      <h2 className="text-3xl font-bold text-gray-800 mb-6">{selectedHypothesis.title}</h2>
                      
                      {/* Enhanced Summary Stats Cards */}
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                        <div className="bg-gradient-to-br from-red-50 to-red-100 p-6 rounded-xl border border-red-200">
                          <div className="flex items-center justify-between">
                            <div>
                              <div className="text-red-700 text-sm font-bold uppercase tracking-wide">Contradictions Found</div>
                              <div className="text-3xl font-black text-red-600 mt-1">{selectedHypothesis.contradictions}</div>
                            </div>
                            <div className="text-red-500 text-3xl">❌</div>
                          </div>
                        </div>
                        <div className="bg-gradient-to-br from-green-50 to-green-100 p-6 rounded-xl border border-green-200">
                          <div className="flex items-center justify-between">
                            <div>
                              <div className="text-green-700 text-sm font-bold uppercase tracking-wide">Confirmations Found</div>
                              <div className="text-3xl font-black text-green-600 mt-1">{selectedHypothesis.confirmations}</div>
                            </div>
                            <div className="text-green-500 text-3xl">✅</div>
                          </div>
                        </div>
                        <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-6 rounded-xl border border-blue-200">
                          <div className="flex items-center justify-between">
                            <div>
                              <div className="text-blue-700 text-sm font-bold uppercase tracking-wide">Confidence Score</div>
                              <div className="text-3xl font-black text-blue-600 mt-1">{selectedHypothesis.confidence}%</div>
                            </div>
                            <div className="text-blue-500 text-3xl">🎯</div>
                          </div>
                        </div>
                      </div>

                      {/* Evidence Details with Better Spacing */}
                      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                        {/* Contradictions Section */}
                        <div className="bg-red-50 rounded-xl p-6 border border-red-200">
                          <h3 className="text-xl font-bold text-red-700 mb-6 flex items-center">
                            <span className="mr-3">❌</span>
                            {selectedHypothesis.contradictions} Contradictions
                          </h3>
                          <div className="space-y-4 max-h-96 overflow-y-auto">
                            {selectedHypothesis.contradictions_detail?.slice(0, 5).map((item, index) => (
                              <div key={index} className="bg-white rounded-lg p-4 border-l-4 border-red-500 shadow-sm">
                                <p className="text-gray-800 mb-3 text-sm italic leading-relaxed">"{item.quote}"</p>
                                <p className="text-xs text-gray-600 mb-3">
                                  <strong>Reason:</strong> {item.reason}
                                </p>
                                <div className="flex justify-between items-center text-xs">
                                  <span className="text-gray-500 truncate mr-2">{item.source}</span>
                                  <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                                    item.strength === 'Strong' 
                                      ? 'bg-red-100 text-red-800' 
                                      : 'bg-orange-100 text-orange-800'
                                  }`}>
                                    {item.strength}
                                  </span>
                                </div>
                              </div>
                            ))}
                            {selectedHypothesis.contradictions > 5 && (
                              <div className="text-center text-red-600 text-sm font-semibold py-2">
                                + {selectedHypothesis.contradictions - 5} more contradictions
                              </div>
                            )}
                          </div>
                        </div>

                        {/* Confirmations Section */}
                        <div className="bg-green-50 rounded-xl p-6 border border-green-200">
                          <h3 className="text-xl font-bold text-green-700 mb-6 flex items-center">
                            <span className="mr-3">✅</span>
                            {selectedHypothesis.confirmations} Confirmations
                          </h3>
                          <div className="space-y-4 max-h-96 overflow-y-auto">
                            {selectedHypothesis.confirmations_detail?.slice(0, 5).map((item, index) => (
                              <div key={index} className="bg-white rounded-lg p-4 border-l-4 border-green-500 shadow-sm">
                                <p className="text-gray-800 mb-3 text-sm italic leading-relaxed">"{item.quote}"</p>
                                <p className="text-xs text-gray-600 mb-3">
                                  <strong>Reason:</strong> {item.reason}
                                </p>
                                <div className="flex justify-between items-center text-xs">
                                  <span className="text-gray-500 truncate mr-2">{item.source}</span>
                                  <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                                    item.strength === 'Strong'
                                      ? 'bg-green-100 text-green-800'
                                      : 'bg-yellow-100 text-yellow-800'
                                  }`}>
                                    {item.strength}
                                  </span>
                                </div>
                              </div>
                            ))}
                            {selectedHypothesis.confirmations > 5 && (
                              <div className="text-center text-green-600 text-sm font-semibold py-2">
                                + {selectedHypothesis.confirmations - 5} more confirmations
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div>
                      <h2 className="text-3xl font-bold text-gray-800 mb-6">Price Trends & Market Insights</h2>
                      
                      {/* Price Metrics Grid */}
                      {selectedHypothesis.trendData && selectedHypothesis.trendData.length > 0 && (
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                          <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-6 rounded-xl border border-blue-200">
                            <div className="text-blue-700 text-sm font-bold uppercase tracking-wide">Current Price</div>
                            <div className="text-2xl font-black text-blue-600">
                              ${selectedHypothesis.trendData[selectedHypothesis.trendData.length - 1]?.value}
                            </div>
                          </div>
                          <div className="bg-gradient-to-br from-green-50 to-green-100 p-6 rounded-xl border border-green-200">
                            <div className="text-green-700 text-sm font-bold uppercase tracking-wide">Week High</div>
                            <div className="text-2xl font-black text-green-600">
                              ${Math.max(...selectedHypothesis.trendData.map(d => d.value))}
                            </div>
                          </div>
                          <div className="bg-gradient-to-br from-orange-50 to-orange-100 p-6 rounded-xl border border-orange-200">
                            <div className="text-orange-700 text-sm font-bold uppercase tracking-wide">Week Low</div>
                            <div className="text-2xl font-black text-orange-600">
                              ${Math.min(...selectedHypothesis.trendData.map(d => d.value))}
                            </div>
                          </div>
                          <div className="bg-gradient-to-br from-purple-50 to-purple-100 p-6 rounded-xl border border-purple-200">
                            <div className="text-purple-700 text-sm font-bold uppercase tracking-wide">Target Price</div>
                            <div className="text-2xl font-black text-purple-600">$85.00</div>
                          </div>
                        </div>
                      )}

                      {/* Enhanced Price History */}
                      <div className="bg-gray-50 rounded-xl p-6 border border-gray-200">
                        <h3 className="text-lg font-semibold text-gray-800 mb-4">Recent Price History</h3>
                        {selectedHypothesis.trendData && selectedHypothesis.trendData.length > 0 ? (
                          <div className="space-y-3">
                            {selectedHypothesis.trendData.slice(-7).map((point, index) => (
                              <div key={index} className="flex justify-between items-center py-3 px-4 bg-white rounded-lg border border-gray-100">
                                <span className="text-gray-600 font-medium">{point.date}</span>
                                <span className="font-bold text-xl text-gray-800">${point.value}</span>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <p className="text-gray-500 text-center py-8">No price history available</p>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default TradingDashboard;
