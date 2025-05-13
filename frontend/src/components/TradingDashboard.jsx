import React, { useState, useEffect } from 'react';
import TradeSageAPI from '../api/tradeSageApi';

const TradingDashboard = () => {
  const [hypotheses, setHypotheses] = useState([]);
  const [selectedHypothesis, setSelectedHypothesis] = useState(null);
  const [activeTab, setActiveTab] = useState('analysis');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const response = await TradeSageAPI.getDashboardData();
      
      if (response.status === 'success') {
        setHypotheses(response.data);
        if (response.data.length > 0) {
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

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-16 w-16 border-4 border-blue-500 border-t-transparent"></div>
          <p className="mt-4 text-gray-600 font-medium">Loading TradeSage Dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-red-50 to-pink-100 flex items-center justify-center">
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

  if (!hypotheses || hypotheses.length === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-100 flex items-center justify-center">
        <div className="text-center bg-white p-12 rounded-lg shadow-lg">
          <div className="text-6xl mb-4">📊</div>
          <h2 className="text-2xl font-bold text-gray-800 mb-4">No Hypotheses Found</h2>
          <p className="text-gray-600 mb-6">Initialize the database with sample data to get started</p>
          <button 
            onClick={fetchDashboardData}
            className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors font-semibold"
          >
            Refresh Dashboard
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
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <div className="container mx-auto px-6 py-8">
        {/* Header */}
        <div className="bg-white rounded-xl shadow-lg p-8 mb-8 border border-blue-100">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                TradeSage AI Dashboard
              </h1>
              <p className="text-gray-600 mt-2 text-lg">Multi-agent contradiction analysis for trading hypotheses</p>
            </div>
            <div className="hidden md:flex items-center space-x-4">
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

        {/* Hypothesis Cards Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6 mb-8">
          {hypotheses.map((hyp) => (
            <div
              key={hyp.id}
              className={`bg-white rounded-xl shadow-lg p-6 cursor-pointer transition-all duration-300 hover:scale-105 hover:shadow-xl border-2 ${
                selectedHypothesis?.id === hyp.id 
                  ? 'border-blue-500 shadow-blue-100' 
                  : 'border-gray-100 hover:border-blue-200'
              }`}
              onClick={() => setSelectedHypothesis(hyp)}
            >
              {/* Card Header */}
              <div className="mb-4">
                <h3 className="font-bold text-xl text-gray-800 leading-tight mb-2">{hyp.title}</h3>
                <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold border ${getStatusColor(hyp.status)}`}>
                  <div className="w-2 h-2 rounded-full bg-current mr-2"></div>
                  {hyp.status}
                </div>
              </div>

              {/* Metrics Row */}
              <div className="grid grid-cols-3 gap-4 mb-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-red-500">{hyp.contradictions}</div>
                  <div className="text-xs text-gray-500">Contradictions</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-500">{hyp.confirmations}</div>
                  <div className="text-xs text-gray-500">Confirmations</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-500">{hyp.confidence}%</div>
                  <div className="text-xs text-gray-500">Confidence</div>
                </div>
              </div>

              {/* Confidence Bar */}
              <div className="mb-4">
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-600">Confidence Score</span>
                  <span className="font-semibold">{hyp.confidence}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full transition-all duration-500 ${getConfidenceColor(hyp.confidence)}`}
                    style={{ width: `${hyp.confidence}%` }}
                  ></div>
                </div>
              </div>

              {/* Price Info */}
              {hyp.trendData && hyp.trendData.length > 0 && (
                <div className="bg-gray-50 rounded-lg p-3 mb-4">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Current Price</span>
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

        {/* Detailed Analysis Panel */}
        {selectedHypothesis && (
          <div className="bg-white rounded-xl shadow-lg border border-gray-100">
            {/* Tab Navigation */}
            <div className="border-b border-gray-200">
              <nav className="flex">
                <button
                  className={`px-8 py-4 text-sm font-semibold transition-colors ${
                    activeTab === 'analysis'
                      ? 'border-b-2 border-blue-500 text-blue-600 bg-blue-50'
                      : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                  }`}
                  onClick={() => setActiveTab('analysis')}
                >
                  <span className="flex items-center">
                    📊 Analysis Breakdown
                  </span>
                </button>
                <button
                  className={`px-8 py-4 text-sm font-semibold transition-colors ${
                    activeTab === 'trends'
                      ? 'border-b-2 border-blue-500 text-blue-600 bg-blue-50'
                      : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                  }`}
                  onClick={() => setActiveTab('trends')}
                >
                  <span className="flex items-center">
                    📈 Trends & Insights
                  </span>
                </button>
              </nav>
            </div>

            {/* Tab Content */}
            <div className="p-8">
              {activeTab === 'analysis' ? (
                <div>
                  <h2 className="text-3xl font-bold text-gray-800 mb-6">{selectedHypothesis.title}</h2>
                  
                  {/* Summary Stats Cards */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                    <div className="bg-gradient-to-br from-red-50 to-red-100 p-6 rounded-lg border border-red-200">
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="text-red-700 text-sm font-semibold">Contradictions Found</div>
                          <div className="text-3xl font-bold text-red-600 mt-1">{selectedHypothesis.contradictions}</div>
                        </div>
                        <div className="text-red-500 text-3xl">❌</div>
                      </div>
                    </div>
                    <div className="bg-gradient-to-br from-green-50 to-green-100 p-6 rounded-lg border border-green-200">
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="text-green-700 text-sm font-semibold">Confirmations Found</div>
                          <div className="text-3xl font-bold text-green-600 mt-1">{selectedHypothesis.confirmations}</div>
                        </div>
                        <div className="text-green-500 text-3xl">✅</div>
                      </div>
                    </div>
                    <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-6 rounded-lg border border-blue-200">
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="text-blue-700 text-sm font-semibold">Confidence Score</div>
                          <div className="text-3xl font-bold text-blue-600 mt-1">{selectedHypothesis.confidence}%</div>
                        </div>
                        <div className="text-blue-500 text-3xl">🎯</div>
                      </div>
                    </div>
                  </div>

                  {/* Evidence Details */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    {/* Contradictions Section */}
                    <div className="bg-red-50 rounded-lg p-6 border border-red-200">
                      <h3 className="text-xl font-bold text-red-700 mb-4 flex items-center">
                        <span className="mr-2">❌</span>
                        {selectedHypothesis.contradictions} Contradictions
                      </h3>
                      <div className="space-y-4 max-h-96 overflow-y-auto">
                        {selectedHypothesis.contradictions_detail?.slice(0, 5).map((item, index) => (
                          <div key={index} className="bg-white rounded-lg p-4 border-l-4 border-red-500">
                            <p className="text-gray-800 mb-2 italic text-sm">"{item.quote}"</p>
                            <p className="text-xs text-gray-600 mb-2">
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
                          <div className="text-center text-red-600 text-sm font-semibold">
                            + {selectedHypothesis.contradictions - 5} more contradictions
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Confirmations Section */}
                    <div className="bg-green-50 rounded-lg p-6 border border-green-200">
                      <h3 className="text-xl font-bold text-green-700 mb-4 flex items-center">
                        <span className="mr-2">✅</span>
                        {selectedHypothesis.confirmations} Confirmations
                      </h3>
                      <div className="space-y-4 max-h-96 overflow-y-auto">
                        {selectedHypothesis.confirmations_detail?.slice(0, 5).map((item, index) => (
                          <div key={index} className="bg-white rounded-lg p-4 border-l-4 border-green-500">
                            <p className="text-gray-800 mb-2 italic text-sm">"{item.quote}"</p>
                            <p className="text-xs text-gray-600 mb-2">
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
                          <div className="text-center text-green-600 text-sm font-semibold">
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
                      <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-6 rounded-lg">
                        <div className="text-blue-700 text-sm font-semibold">Current Price</div>
                        <div className="text-2xl font-bold text-blue-600">
                          ${selectedHypothesis.trendData[selectedHypothesis.trendData.length - 1]?.value}
                        </div>
                      </div>
                      <div className="bg-gradient-to-br from-green-50 to-green-100 p-6 rounded-lg">
                        <div className="text-green-700 text-sm font-semibold">Week High</div>
                        <div className="text-2xl font-bold text-green-600">
                          ${Math.max(...selectedHypothesis.trendData.map(d => d.value))}
                        </div>
                      </div>
                      <div className="bg-gradient-to-br from-orange-50 to-orange-100 p-6 rounded-lg">
                        <div className="text-orange-700 text-sm font-semibold">Week Low</div>
                        <div className="text-2xl font-bold text-orange-600">
                          ${Math.min(...selectedHypothesis.trendData.map(d => d.value))}
                        </div>
                      </div>
                      <div className="bg-gradient-to-br from-purple-50 to-purple-100 p-6 rounded-lg">
                        <div className="text-purple-700 text-sm font-semibold">Target Price</div>
                        <div className="text-2xl font-bold text-purple-600">$85.00</div>
                      </div>
                    </div>
                  )}

                  {/* Simple Price History Display */}
                  <div className="bg-gray-50 rounded-lg p-6">
                    <h3 className="text-lg font-semibold text-gray-800 mb-4">Recent Price History</h3>
                    {selectedHypothesis.trendData && selectedHypothesis.trendData.length > 0 ? (
                      <div className="space-y-2">
                        {selectedHypothesis.trendData.slice(-7).map((point, index) => (
                          <div key={index} className="flex justify-between items-center py-2 border-b border-gray-200 last:border-b-0">
                            <span className="text-gray-600">{point.date}</span>
                            <span className="font-semibold text-lg">${point.value}</span>
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
      </div>
    </div>
  );
};

export default TradingDashboard;
