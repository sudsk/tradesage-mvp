import React, { useState, useEffect } from 'react';
import TradeSageAPI from '../api/tradeSageApi';
import Notification from './Notification';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { cleanMarkdownText, extractQuoteAndReason, formatHypothesisTitle } from '../utils/textUtils';

const TradingDashboard = () => {
  const [hypotheses, setHypotheses] = useState([]);
  const [selectedHypothesis, setSelectedHypothesis] = useState(null);
  const [activeTab, setActiveTab] = useState('analysis');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [notification, setNotification] = useState(null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  
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
        await fetchDashboardData();
        
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

  const getStatusColor = (status) => {
    const statusColors = {
      'on schedule': 'bg-emerald-500 text-white',
      'on demand': 'bg-blue-500 text-white',
      'active': 'bg-purple-500 text-white',
      'completed': 'bg-green-500 text-white',
      'cancelled': 'bg-red-500 text-white'
    };
    return statusColors[status.toLowerCase()] || 'bg-gray-500 text-white';
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 70) return 'bg-gradient-to-r from-green-500 to-emerald-600';
    if (confidence >= 50) return 'bg-gradient-to-r from-yellow-500 to-orange-500';
    return 'bg-gradient-to-r from-red-500 to-pink-600';
  };

  const formatPriceData = (trendData) => {
    return trendData?.map((point, index) => ({
      name: point.date,
      value: parseFloat(point.value),
      index
    })) || [];
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex items-center justify-center">
        <div className="text-center p-8">
          <div className="inline-block relative">
            <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
            <div className="w-12 h-12 border-4 border-purple-600 border-t-transparent rounded-full animate-spin absolute top-2 left-2" style={{animationDirection: 'reverse', animationDuration: '0.8s'}}></div>
          </div>
          <h3 className="mt-6 text-xl font-semibold text-gray-700">Loading TradeSage Dashboard</h3>
          <p className="text-gray-500 mt-2">Analyzing market data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-red-50 to-orange-50 flex items-center justify-center">
        <div className="text-center bg-white p-8 rounded-2xl shadow-2xl border border-red-100">
          <div className="w-20 h-20 mx-auto mb-6 bg-red-100 rounded-full flex items-center justify-center">
            <svg className="w-10 h-10 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.963-.833-2.732 0l-4.138 4.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-red-600 mb-4">Dashboard Error</h2>
          <p className="text-gray-600 mb-6">{error}</p>
          <button 
            onClick={fetchDashboardData}
            className="px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-all duration-200 font-semibold shadow-lg hover:shadow-xl"
          >
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* Notification */}
      {notification && (
        <Notification
          message={notification.message}
          type={notification.type}
          onClose={() => setNotification(null)}
        />
      )}
      
      <div className="flex">
        {/* Enhanced Sidebar */}
        <div className={`${sidebarCollapsed ? 'w-16' : 'w-80'} bg-white shadow-2xl transition-all duration-300 min-h-screen border-r border-gray-100`}>
          <div className="p-6 border-b border-gray-100">
            <div className="flex items-center justify-between">
              {!sidebarCollapsed && (
                <div>
                  <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                    TradeSage AI
                  </h1>
                  <p className="text-sm text-gray-500 mt-1">Multi-Agent Analysis</p>
                </div>
              )}
              <button
                onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
                className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={sidebarCollapsed ? "M9 5l7 7-7 7" : "M15 19l-7-7 7-7"} />
                </svg>
              </button>
            </div>
          </div>

          {/* Sidebar Actions */}
          <div className="p-4 border-b border-gray-100">
            <button
              onClick={() => setShowForm(true)}
              className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl py-3 px-4 font-semibold hover:shadow-lg transition-all duration-200 flex items-center justify-center group"
            >
              {sidebarCollapsed ? (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
              ) : (
                <>
                  <svg className="w-5 h-5 mr-2 group-hover:scale-110 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                  New Analysis
                </>
              )}
            </button>
          </div>

          {/* Hypothesis List */}
          <div className="flex-1 overflow-y-auto">
            {!sidebarCollapsed && <h3 className="px-4 py-3 text-sm font-semibold text-gray-700 uppercase tracking-wide">Active Hypotheses</h3>}
            <div className="space-y-2 px-2">
              {hypotheses.map((hyp) => (
                <div
                  key={hyp.id}
                  className={`p-3 rounded-xl cursor-pointer transition-all duration-200 ${
                    selectedHypothesis?.id === hyp.id 
                      ? 'bg-gradient-to-r from-blue-50 to-purple-50 border-2 border-blue-200 shadow-md' 
                      : 'hover:bg-gray-50 border border-transparent'
                  }`}
                  onClick={() => setSelectedHypothesis(hyp)}
                  title={sidebarCollapsed ? hyp.title : ''}
                >
                  {sidebarCollapsed ? (
                    <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-100 to-purple-100 flex items-center justify-center">
                      <span className="text-blue-700 font-bold text-lg">{hyp.title.charAt(0)}</span>
                    </div>
                  ) : (
                    <>
                      <h3 className="font-semibold text-gray-800 text-sm mb-2 line-clamp-2">
                        {formatHypothesisTitle(hyp.title)}
                      </h3>
                      <div className="flex items-center space-x-3 text-xs">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(hyp.status)}`}>
                          {hyp.status}
                        </span>
                        <span className="text-gray-500">{hyp.confidence}%</span>
                      </div>
                      <div className="flex justify-between text-xs text-gray-500 mt-2">
                        <span>{hyp.contradictions}✗</span>
                        <span>{hyp.confirmations}✓</span>
                      </div>
                    </>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Sidebar Stats */}
          {!sidebarCollapsed && (
            <div className="p-4 border-t border-gray-100 bg-gray-50">
              <div className="grid grid-cols-2 gap-3 text-center">
                <div className="bg-white rounded-lg p-3 shadow-sm">
                  <div className="text-lg font-bold text-blue-600">{hypotheses.length}</div>
                  <div className="text-xs text-gray-500">Total</div>
                </div>
                <div className="bg-white rounded-lg p-3 shadow-sm">
                  <div className="text-lg font-bold text-green-600">
                    {Math.round(hypotheses.reduce((acc, h) => acc + h.confidence, 0) / hypotheses.length) || 0}%
                  </div>
                  <div className="text-xs text-gray-500">Avg. Confidence</div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Enhanced Main Content */}
        <div className="flex-1 p-8">
          {hypotheses.length === 0 ? (
            <div className="h-full flex items-center justify-center">
              <div className="text-center bg-white rounded-2xl p-12 shadow-xl border border-gray-100">
                <div className="w-24 h-24 mx-auto mb-6 bg-gradient-to-br from-blue-100 to-purple-100 rounded-2xl flex items-center justify-center">
                  <svg className="w-12 h-12 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
                <h2 className="text-2xl font-bold text-gray-800 mb-4">Welcome to TradeSage AI</h2>
                <p className="text-gray-600 mb-8 max-w-md mx-auto">
                  Start by analyzing your first trading hypothesis. Our multi-agent system will provide comprehensive contradictions and confirmations.
                </p>
                <button 
                  onClick={() => setShowForm(true)}
                  className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-8 py-4 rounded-xl font-semibold hover:shadow-xl transition-all duration-200 transform hover:scale-105"
                >
                  Create Your First Analysis
                </button>
              </div>
            </div>
          ) : selectedHypothesis ? (
            <div className="bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden">
              {/* Enhanced Header */}
              <div className="bg-gradient-to-r from-slate-50 to-blue-50 p-8 border-b border-gray-100">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h1 className="text-3xl font-bold text-gray-800 mb-2">{selectedHypothesis.title}</h1>
                    <div className="flex items-center space-x-4">
                      <span className={`px-4 py-2 rounded-full text-sm font-semibold ${getStatusColor(selectedHypothesis.status)}`}>
                        {selectedHypothesis.status}
                      </span>
                      <span className="text-gray-500 text-sm">Updated {selectedHypothesis.lastUpdated}</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-3xl font-bold text-gray-800">{selectedHypothesis.confidence}%</div>
                    <div className="text-sm text-gray-500">Confidence Score</div>
                  </div>
                </div>
              </div>

              {/* Enhanced Metrics Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 p-8 border-b border-gray-100">
                <div className="bg-gradient-to-br from-red-50 to-red-100 p-6 rounded-2xl border border-red-200 hover:shadow-lg transition-shadow">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-red-700 text-sm font-bold uppercase tracking-wide mb-1">Contradictions</div>
                      <div className="text-3xl font-black text-red-600">{selectedHypothesis.contradictions}</div>
                    </div>
                    <div className="w-12 h-12 bg-red-200 rounded-xl flex items-center justify-center">
                      <span className="text-red-600 text-2xl">❌</span>
                    </div>
                  </div>
                  <div className="mt-3 text-xs text-red-600">
                    <span className="font-medium">
                      {selectedHypothesis.contradictions > 5 ? 'High' : selectedHypothesis.contradictions > 2 ? 'Medium' : 'Low'} opposition
                    </span>
                  </div>
                </div>

                <div className="bg-gradient-to-br from-green-50 to-green-100 p-6 rounded-2xl border border-green-200 hover:shadow-lg transition-shadow">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-green-700 text-sm font-bold uppercase tracking-wide mb-1">Confirmations</div>
                      <div className="text-3xl font-black text-green-600">{selectedHypothesis.confirmations}</div>
                    </div>
                    <div className="w-12 h-12 bg-green-200 rounded-xl flex items-center justify-center">
                      <span className="text-green-600 text-2xl">✅</span>
                    </div>
                  </div>
                  <div className="mt-3 text-xs text-green-600">
                    <span className="font-medium">
                      {selectedHypothesis.confirmations > 8 ? 'Strong' : selectedHypothesis.confirmations > 4 ? 'Moderate' : 'Weak'} support
                    </span>
                  </div>
                </div>

                <div className="bg-gradient-to-br from-blue-50 to-purple-100 p-6 rounded-2xl border border-blue-200 hover:shadow-lg transition-shadow">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-blue-700 text-sm font-bold uppercase tracking-wide mb-1">Confidence</div>
                      <div className="text-3xl font-black text-blue-600">{selectedHypothesis.confidence}%</div>
                    </div>
                    <div className="w-12 h-12 bg-blue-200 rounded-xl flex items-center justify-center">
                      <span className="text-blue-600 text-2xl">🎯</span>
                    </div>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2 mt-3">
                    <div
                      className={`h-2 rounded-full transition-all duration-700 ${getConfidenceColor(selectedHypothesis.confidence)}`}
                      style={{ width: `${selectedHypothesis.confidence}%` }}
                    ></div>
                  </div>
                </div>
              </div>

              {/* Enhanced Tabs */}
              <div className="border-b border-gray-100">
                <nav className="flex">
                  <button
                    className={`px-8 py-4 text-sm font-semibold transition-all relative ${
                      activeTab === 'analysis'
                        ? 'text-blue-600 bg-blue-50 border-b-2 border-blue-600'
                        : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                    }`}
                    onClick={() => setActiveTab('analysis')}
                  >
                    <span className="flex items-center">
                      <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                      </svg>
                      Detailed Analysis
                    </span>
                  </button>
                  <button
                    className={`px-8 py-4 text-sm font-semibold transition-all relative ${
                      activeTab === 'trends'
                        ? 'text-blue-600 bg-blue-50 border-b-2 border-blue-600'
                        : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                    }`}
                    onClick={() => setActiveTab('trends')}
                  >
                    <span className="flex items-center">
                      <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                      </svg>
                      Market Trends
                    </span>
                  </button>
                </nav>
              </div>

              {/* Tab Content */}
              <div className="p-8">
                {activeTab === 'analysis' ? (
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    {/* Enhanced Contradictions */}
                    <div className="bg-red-50 rounded-2xl p-6 border border-red-200">
                      <h3 className="text-xl font-bold text-red-700 mb-6 flex items-center">
                        <span className="w-8 h-8 bg-red-200 rounded-lg flex items-center justify-center mr-3">
                          <span className="text-red-600">❌</span>
                        </span>
                        Contradictions ({selectedHypothesis.contradictions})
                      </h3>
                      <div className="space-y-4 max-h-96 overflow-y-auto">
                        {selectedHypothesis.contradictions_detail?.slice(0, 5).map((item, index) => (
                          <div key={index} className="bg-white rounded-xl p-4 border-l-4 border-red-500 shadow-sm hover:shadow-md transition-shadow">
                            <p className="text-gray-800 mb-3 text-sm leading-relaxed font-medium">
                              <span dangerouslySetInnerHTML={{ __html: `"${cleanMarkdownText(extractQuoteAndReason(item.quote).quote)}"` }} />
                            </p>
                            <p className="text-xs text-gray-600 mb-3">
                              <strong className="text-red-600">Analysis:</strong>
                              <span dangerouslySetInnerHTML={{ __html: cleanMarkdownText(extractQuoteAndReason(item.reason).reason) }} />
                            </p>
                            <div className="flex justify-between items-center text-xs">
                              <span className="text-gray-500 truncate mr-2">{item.source}</span>
                              <span className={`px-3 py-1 rounded-full text-xs font-bold ${
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
                          <div className="text-center text-red-600 text-sm font-semibold py-3 bg-red-100 rounded-lg">
                            + {selectedHypothesis.contradictions - 5} more contradictions
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Enhanced Confirmations */}
                    <div className="bg-green-50 rounded-2xl p-6 border border-green-200">
                      <h3 className="text-xl font-bold text-green-700 mb-6 flex items-center">
                        <span className="w-8 h-8 bg-green-200 rounded-lg flex items-center justify-center mr-3">
                          <span className="text-green-600">✅</span>
                        </span>
                        Confirmations ({selectedHypothesis.confirmations})
                      </h3>
                      <div className="space-y-4 max-h-96 overflow-y-auto">
                        {selectedHypothesis.confirmations_detail?.slice(0, 5).map((item, index) => (
                          <div key={index} className="bg-white rounded-xl p-4 border-l-4 border-green-500 shadow-sm hover:shadow-md transition-shadow">
                            <p className="text-gray-800 mb-3 text-sm leading-relaxed font-medium">
                              <span dangerouslySetInnerHTML={{ __html: `"${cleanMarkdownText(extractQuoteAndReason(item.quote).quote)}"` }} />
                            </p>
                            <p className="text-xs text-gray-600 mb-3">
                              <strong className="text-green-600">Analysis:</strong>
                              <span dangerouslySetInnerHTML={{ __html: cleanMarkdownText(extractQuoteAndReason(item.reason).reason) }} />
                            </p>
                            <div className="flex justify-between items-center text-xs">
                              <span className="text-gray-500 truncate mr-2">{item.source}</span>
                              <span className={`px-3 py-1 rounded-full text-xs font-bold ${
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
                          <div className="text-center text-green-600 text-sm font-semibold py-3 bg-green-100 rounded-lg">
                            + {selectedHypothesis.confirmations - 5} more confirmations
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div>
                    {/* Enhanced Price Metrics */}
                    {selectedHypothesis.trendData && selectedHypothesis.trendData.length > 0 && (
                      <>
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                          <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-6 rounded-xl border border-blue-200">
                            <div className="text-blue-700 text-sm font-bold uppercase tracking-wide">Current Price</div>
                            <div className="text-2xl font-black text-blue-600">
                              ${selectedHypothesis.trendData[selectedHypothesis.trendData.length - 1]?.value}
                            </div>
                            <div className="text-xs text-blue-600 mt-2">
                              <span className="inline-block w-2 h-2 bg-blue-500 rounded-full mr-1"></span>
                              Live Data
                            </div>
                          </div>
                          <div className="bg-gradient-to-br from-green-50 to-green-100 p-6 rounded-xl border border-green-200">
                            <div className="text-green-700 text-sm font-bold uppercase tracking-wide">7-Day High</div>
                            <div className="text-2xl font-black text-green-600">
                              ${Math.max(...selectedHypothesis.trendData.map(d => d.value)).toFixed(2)}
                            </div>
                            <div className="text-xs text-green-600 mt-2">
                              <span className="inline-block w-2 h-2 bg-green-500 rounded-full mr-1"></span>
                              Peak Value
                            </div>
                          </div>
                          <div className="bg-gradient-to-br from-orange-50 to-orange-100 p-6 rounded-xl border border-orange-200">
                            <div className="text-orange-700 text-sm font-bold uppercase tracking-wide">7-Day Low</div>
                            <div className="text-2xl font-black text-orange-600">
                              ${Math.min(...selectedHypothesis.trendData.map(d => d.value)).toFixed(2)}
                            </div>
                            <div className="text-xs text-orange-600 mt-2">
                              <span className="inline-block w-2 h-2 bg-orange-500 rounded-full mr-1"></span>
                              Lowest Point
                            </div>
                          </div>
                          <div className="bg-gradient-to-br from-purple-50 to-purple-100 p-6 rounded-xl border border-purple-200">
                            <div className="text-purple-700 text-sm font-bold uppercase tracking-wide">Target Price</div>
                            <div className="text-2xl font-black text-purple-600">$85.00</div>
                            <div className="text-xs text-purple-600 mt-2">
                              <span className="inline-block w-2 h-2 bg-purple-500 rounded-full mr-1"></span>
                              Hypothesis Goal
                            </div>
                          </div>
                        </div>

                        {/* Enhanced Chart */}
                        <div className="bg-gray-50 rounded-xl p-6 border border-gray-200 mb-8">
                          <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                            <svg className="w-5 h-5 mr-2 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                            </svg>
                            Price Trend Analysis
                          </h3>
                          <div className="h-64">
                            <ResponsiveContainer width="100%" height="100%">
                              <AreaChart data={formatPriceData(selectedHypothesis.trendData)}>
                                <defs>
                                  <linearGradient id="colorGradient" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3}/>
                                    <stop offset="95%" stopColor="#3B82F6" stopOpacity={0.1}/>
                                  </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                                <XAxis 
                                  dataKey="name" 
                                  stroke="#6B7280"
                                  fontSize={12}
                                />
                                <YAxis 
                                  stroke="#6B7280"
                                  fontSize={12}
                                  domain={['dataMin - 1', 'dataMax + 1']}
                                />
                                <Tooltip 
                                  contentStyle={{
                                    backgroundColor: 'white',
                                    border: '1px solid #E5E7EB',
                                    borderRadius: '8px',
                                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                                  }}
                                />
                                <Area
                                  type="monotone"
                                  dataKey="value"
                                  stroke="#3B82F6"
                                  strokeWidth={3}
                                  fill="url(#colorGradient)"
                                />
                              </AreaChart>
                            </ResponsiveContainer>
                          </div>
                        </div>

                        {/* Price History Table */}
                        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
                          <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
                            <h3 className="text-lg font-semibold text-gray-800">Recent Price History</h3>
                          </div>
                          <div className="divide-y divide-gray-200">
                            {selectedHypothesis.trendData.slice(-7).map((point, index) => {
                              const prevValue = index > 0 ? selectedHypothesis.trendData[selectedHypothesis.trendData.length - 7 + index - 1]?.value : point.value;
                              const change = point.value - prevValue;
                              const changePercent = prevValue ? ((change / prevValue) * 100) : 0;
                              
                              return (
                                <div key={index} className="px-6 py-4 hover:bg-gray-50 transition-colors">
                                  <div className="flex justify-between items-center">
                                    <span className="text-gray-600 font-medium">{point.date}</span>
                                    <div className="text-right">
                                      <span className="font-bold text-xl text-gray-800">${point.value}</span>
                                      {index > 0 && (
                                        <div className={`text-sm font-medium ${
                                          change >= 0 ? 'text-green-600' : 'text-red-600'
                                        }`}>
                                          {change >= 0 ? '+' : ''}{change.toFixed(2)} ({changePercent.toFixed(2)}%)
                                        </div>
                                      )}
                                    </div>
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      </>
                    )}
                  </div>
                )}
              </div>
            </div>
          ) : null}
        </div>
      </div>

      {/* Enhanced Form Modal */}
      {showForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-90vh overflow-y-auto">
            <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-6 rounded-t-2xl">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-bold text-white">Submit Trading Hypothesis</h2>
                  <p className="text-blue-100 mt-1">Let our AI agents analyze your trading idea</p>
                </div>
                <button
                  onClick={() => setShowForm(false)}
                  className="text-white hover:text-blue-200 text-2xl p-2 hover:bg-white hover:bg-opacity-10 rounded-lg transition-all"
                >
                  ×
                </button>
              </div>
            </div>
            
            <form onSubmit={handleFormSubmit} className="p-6">
              <div className="mb-6">
                <label className="block text-sm font-semibold text-gray-700 mb-3">
                  Analysis Mode
                </label>
                <div className="grid grid-cols-3 gap-3">
                  {[
                    { value: 'analyze', label: 'Analyze', icon: '🔍', desc: 'Existing hypothesis' },
                    { value: 'refine', label: 'Refine', icon: '✨', desc: 'Trading idea' },
                    { value: 'generate', label: 'Generate', icon: '🚀', desc: 'New hypothesis' }
                  ].map((mode) => (
                    <label
                      key={mode.value}
                      className={`relative cursor-pointer rounded-xl border-2 p-4 transition-all ${
                        formData.mode === mode.value
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                      }`}
                    >
                      <input
                        type="radio"
                        name="mode"
                        value={mode.value}
                        checked={formData.mode === mode.value}
                        onChange={handleInputChange}
                        className="absolute top-3 right-3"
                      />
                      <div className="text-2xl mb-2">{mode.icon}</div>
                      <div className="font-semibold text-gray-800">{mode.label}</div>
                      <div className="text-xs text-gray-500">{mode.desc}</div>
                    </label>
                  ))}
                </div>
              </div>

              {formData.mode === 'analyze' && (
                <div className="mb-6">
                  <label className="block text-sm font-semibold text-gray-700 mb-3">
                    <span className="flex items-center">
                      <span className="text-blue-600 mr-2">🔍</span>
                      Trading Hypothesis
                    </span>
                  </label>
                  <textarea
                    name="hypothesis"
                    value={formData.hypothesis}
                    onChange={handleInputChange}
                    placeholder="e.g., Bitcoin will reach $100,000 by end of Q2 2025 due to institutional adoption and ETF inflows"
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none transition-all"
                    rows="4"
                    required
                  />
                  <p className="text-xs text-gray-500 mt-2">Provide a specific, actionable trading hypothesis with reasoning</p>
                </div>
              )}

              {formData.mode === 'refine' && (
                <div className="mb-6">
                  <label className="block text-sm font-semibold text-gray-700 mb-3">
                    <span className="flex items-center">
                      <span className="text-purple-600 mr-2">✨</span>
                      Trading Idea to Refine
                    </span>
                  </label>
                  <textarea
                    name="idea"
                    value={formData.idea}
                    onChange={handleInputChange}
                    placeholder="e.g., I think tech stocks will go up because of AI developments"
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 resize-none transition-all"
                    rows="4"
                    required
                  />
                  <p className="text-xs text-gray-500 mt-2">Share your basic trading idea - we'll help structure it into a formal hypothesis</p>
                </div>
              )}

              {formData.mode === 'generate' && (
                <div className="mb-6">
                  <label className="block text-sm font-semibold text-gray-700 mb-3">
                    <span className="flex items-center">
                      <span className="text-green-600 mr-2">🚀</span>
                      Market Context (Optional)
                    </span>
                  </label>
                  <textarea
                    name="context"
                    value={formData.context}
                    onChange={handleInputChange}
                    placeholder="e.g., Current market conditions, sectors of interest, time horizon preferences"
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-green-500 resize-none transition-all"
                    rows="4"
                  />
                  <p className="text-xs text-gray-500 mt-2">Provide market context to help generate a relevant hypothesis</p>
                </div>
              )}

              <div className="flex items-center space-x-4">
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="flex-1 bg-gradient-to-r from-blue-600 to-purple-600 text-white py-4 rounded-xl hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 font-semibold text-lg"
                >
                  {isSubmitting ? (
                    <span className="flex items-center justify-center">
                      <svg className="animate-spin h-5 w-5 mr-3 text-white" fill="none" viewBox="0 0 24 24">
                        <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" className="opacity-25"></circle>
                        <path fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" className="opacity-75"></path>
                      </svg>
                      Analyzing with AI Agents...
                    </span>
                  ) : (
                    <>🧠 Analyze with TradeSage AI</>
                  )}
                </button>
                <button
                  type="button"
                  onClick={() => setShowForm(false)}
                  className="px-6 py-4 bg-gray-100 text-gray-700 rounded-xl hover:bg-gray-200 transition-colors font-semibold"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default TradingDashboard;
