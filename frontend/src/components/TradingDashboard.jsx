import React, { useState, useEffect } from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

const TradingDashboard = () => {
  const [hypotheses, setHypotheses] = useState([]);
  const [selectedHypothesis, setSelectedHypothesis] = useState(null);
  const [activeTab, setActiveTab] = useState('analysis');

  // Mock data - replace with API calls
  useEffect(() => {
    const mockHypotheses = [
      {
        id: 1,
        title: "Oil prices to go above $85/barrel by March",
        status: "On schedule",
        contradictions: 14,
        confirmations: 10,
        confidence: 65,
        lastUpdated: "24/01/2025 11:00",
        trendData: [
          { date: '20/01', value: 82 },
          { date: '21/01', value: 83.5 },
          { date: '22/01', value: 82.8 },
          { date: '23/01', value: 84.2 },
          { date: '24/01', value: 83.9 }
        ],
        contradictions_detail: [
          {
            quote: "Oil headed for the first weekly decline this year after Donald Trump raised the prospect of trade wars and said he will ask Saudi Arabia and OPEC to lower prices as his first week as the new US president.",
            reason: "This quote presents a contradictory perspective, indicating potential downward pressure on oil prices due to geopolitical factors and interventions.",
            source: "Oil Set for First Weekly Drop This Year as Trump Rattles Market | Bloomberg | 23/01/2025",
            strength: "Strong"
          },
          {
            quote: "Market volatility expected as new policies unfold",
            reason: "Uncertainty in energy markets could lead to price fluctuations rather than steady upward trend",
            source: "Energy Analysis Today | 22/01/2025",
            strength: "Medium"
          }
        ],
        confirmations_detail: [
          {
            quote: "Oil edged higher as US sanctions on Russian crude tighten the market.",
            reason: "The tightening of the market due to US sanctions on Russian crude could lead to higher Brent prices.",
            source: "Oil Edges Higher as Sanctions on Russian Crude Tighten Market | Transcripts | 23/01/2025",
            strength: "Strong"
          },
          {
            quote: "Supply chain disruptions continue to affect global oil markets",
            reason: "Ongoing supply issues support upward price pressure in oil markets",
            source: "Global Energy Report | 21/01/2025",
            strength: "Medium"
          }
        ]
      },
      {
        id: 2,
        title: "US inflation rate increase next year",
        status: "On demand",
        contradictions: 10,
        confirmations: 4,
        confidence: 45,
        lastUpdated: "24/01/2025 09:00",
        trendData: [
          { date: '20/01', value: 2.1 },
          { date: '21/01', value: 2.3 },
          { date: '22/01', value: 2.2 },
          { date: '23/01', value: 2.4 },
          { date: '24/01', value: 2.3 }
        ]
      },
      {
        id: 3,
        title: "Long TTF due to inelastic demand and high degree of weather risk",
        status: "On demand",
        contradictions: 8,
        confirmations: 12,
        confidence: 72,
        lastUpdated: "24/01/2025 08:30",
        trendData: [
          { date: '20/01', value: 45.2 },
          { date: '21/01', value: 46.8 },
          { date: '22/01', value: 47.5 },
          { date: '23/01', value: 48.1 },
          { date: '24/01', value: 48.9 }
        ]
      }
    ];
    setHypotheses(mockHypotheses);
    setSelectedHypothesis(mockHypotheses[0]);
  }, []);

  const getStatusColor = (status) => {
    if (status.toLowerCase().includes('schedule')) return 'text-green-600 bg-green-50';
    if (status.toLowerCase().includes('demand')) return 'text-blue-600 bg-blue-50';
    return 'text-gray-600 bg-gray-50';
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 70) return 'bg-green-500';
    if (confidence >= 50) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const pieData = selectedHypothesis ? [
    { name: 'Contradictions', value: selectedHypothesis.contradictions, color: '#EF4444' },
    { name: 'Confirmations', value: selectedHypothesis.confirmations, color: '#10B981' }
  ] : [];

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        <header className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">TradeSage Trading Dashboard</h1>
          <p className="text-gray-600 mt-2">Multi-agent contradiction analysis for trading hypotheses</p>
        </header>

        {/* Hypothesis Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          {hypotheses.map((hyp) => (
            <div
              key={hyp.id}
              className={`bg-white rounded-lg shadow-md p-6 cursor-pointer transition-all duration-200 ${
                selectedHypothesis?.id === hyp.id ? 'ring-2 ring-blue-500' : 'hover:shadow-lg'
              }`}
              onClick={() => setSelectedHypothesis(hyp)}
            >
              <h3 className="font-semibold text-lg mb-3 text-gray-800">{hyp.title}</h3>
              
              {/* Mini Chart */}
              <div className="h-32 mb-4">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={hyp.trendData}>
                    <Line type="monotone" dataKey="value" stroke="#3B82F6" strokeWidth={2} dot={false} />
                    <Tooltip formatter={(value) => [`$${value}`, 'Price']} />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              {/* Contradictions/Confirmations Summary */}
              <div className="flex justify-between items-center mb-3">
                <div className="flex items-center space-x-4">
                  <span className="text-red-600 flex items-center">
                    <span className="text-xl">✗</span>
                    <span className="ml-1 font-semibold">{hyp.contradictions}</span>
                  </span>
                  <span className="text-green-600 flex items-center">
                    <span className="text-xl">✓</span>
                    <span className="ml-1 font-semibold">{hyp.confirmations}</span>
                  </span>
                </div>
                <div className="flex items-center">
                  <div className={`h-2 w-16 rounded-full bg-gray-200 overflow-hidden`}>
                    <div
                      className={`h-full ${getConfidenceColor(hyp.confidence)}`}
                      style={{ width: `${hyp.confidence}%` }}
                    />
                  </div>
                  <span className="ml-2 text-sm text-gray-600">{hyp.confidence}%</span>
                </div>
              </div>

              {/* Status and Last Updated */}
              <div className="flex justify-between items-center">
                <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(hyp.status)}`}>
                  {hyp.status}
                </span>
                <span className="text-xs text-gray-500">As of {hyp.lastUpdated}</span>
              </div>
            </div>
          ))}
        </div>

        {/* Detailed Analysis Panel */}
        {selectedHypothesis && (
          <div className="bg-white rounded-lg shadow-md">
            <div className="border-b border-gray-200">
              <nav className="flex space-x-8">
                <button
                  className={`py-4 px-6 text-sm font-medium ${
                    activeTab === 'analysis' 
                      ? 'border-b-2 border-blue-500 text-blue-600' 
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                  onClick={() => setActiveTab('analysis')}
                >
                  Analysis Breakdown
                </button>
                <button
                  className={`py-4 px-6 text-sm font-medium ${
                    activeTab === 'trends' 
                      ? 'border-b-2 border-blue-500 text-blue-600' 
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                  onClick={() => setActiveTab('trends')}
                >
                  Trends & Charts
                </button>
              </nav>
            </div>

            <div className="p-6">
              {activeTab === 'analysis' && (
                <div>
                  <h2 className="text-2xl font-bold mb-6">{selectedHypothesis.title}</h2>
                  
                  {/* Summary Stats */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                    <div className="bg-red-50 p-4 rounded-lg">
                      <div className="text-red-700 text-sm font-medium">Contradictions Found</div>
                      <div className="text-3xl font-bold text-red-600 mt-1">{selectedHypothesis.contradictions}</div>
                    </div>
                    <div className="bg-green-50 p-4 rounded-lg">
                      <div className="text-green-700 text-sm font-medium">Confirmations Found</div>
                      <div className="text-3xl font-bold text-green-600 mt-1">{selectedHypothesis.confirmations}</div>
                    </div>
                    <div className="bg-blue-50 p-4 rounded-lg">
                      <div className="text-blue-700 text-sm font-medium">Confidence Score</div>
                      <div className="text-3xl font-bold text-blue-600 mt-1">{selectedHypothesis.confidence}%</div>
                    </div>
                  </div>

                  {/* Pie Chart */}
                  <div className="mb-8">
                    <h3 className="text-lg font-semibold mb-4">Evidence Distribution</h3>
                    <div className="h-64">
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie
                            data={pieData}
                            cx="50%"
                            cy="50%"
                            outerRadius={80}
                            dataKey="value"
                            label={({ name, value }) => `${name}: ${value}`}
                          >
                            {pieData.map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={entry.color} />
                            ))}
                          </Pie>
                          <Tooltip />
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                  </div>

                  {/* Detailed Analysis */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    {/* Contradictions Section */}
                    <div>
                      <h3 className="text-lg font-semibold text-red-700 mb-4">
                        {selectedHypothesis.contradictions} Contradictions Found
                      </h3>
                      {selectedHypothesis.contradictions_detail?.map((item, index) => (
                        <div key={index} className="border-l-4 border-red-500 bg-red-50 p-4 mb-4">
                          <p className="text-gray-800 mb-2 italic">"{item.quote}"</p>
                          <p className="text-sm text-gray-600 mb-2">
                            <strong>Reason:</strong> {item.reason}
                          </p>
                          <div className="flex justify-between items-center text-xs">
                            <span className="text-gray-500">{item.source}</span>
                            <span className={`px-2 py-1 rounded ${
                              item.strength === 'Strong' ? 'bg-red-200 text-red-800' : 'bg-orange-200 text-orange-800'
                            }`}>
                              {item.strength}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>

                    {/* Confirmations Section */}
                    <div>
                      <h3 className="text-lg font-semibold text-green-700 mb-4">
                        {selectedHypothesis.confirmations} Confirmations Found
                      </h3>
                      {selectedHypothesis.confirmations_detail?.map((item, index) => (
                        <div key={index} className="border-l-4 border-green-500 bg-green-50 p-4 mb-4">
                          <p className="text-gray-800 mb-2 italic">"{item.quote}"</p>
                          <p className="text-sm text-gray-600 mb-2">
                            <strong>Reason:</strong> {item.reason}
                          </p>
                          <div className="flex justify-between items-center text-xs">
                            <span className="text-gray-500">{item.source}</span>
                            <span className={`px-2 py-1 rounded ${
                              item.strength === 'Strong' ? 'bg-green-200 text-green-800' : 'bg-yellow-200 text-yellow-800'
                            }`}>
                              {item.strength}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'trends' && (
                <div>
                  <h2 className="text-2xl font-bold mb-6">Price Trends & Metrics</h2>
                  
                  {/* Large Trend Chart */}
                  <div className="h-96 mb-8">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={selectedHypothesis.trendData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="date" />
                        <YAxis />
                        <Tooltip formatter={(value) => [`$${value}`, 'Price']} />
                        <Line type="monotone" dataKey="value" stroke="#2563EB" strokeWidth={3} />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>

                  {/* Key Metrics */}
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <div className="text-sm text-gray-600">Current Price</div>
                      <div className="text-xl font-bold">${selectedHypothesis.trendData[selectedHypothesis.trendData.length - 1]?.value}</div>
                    </div>
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <div className="text-sm text-gray-600">Week High</div>
                      <div className="text-xl font-bold">${Math.max(...selectedHypothesis.trendData.map(d => d.value))}</div>
                    </div>
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <div className="text-sm text-gray-600">Week Low</div>
                      <div className="text-xl font-bold">${Math.min(...selectedHypothesis.trendData.map(d => d.value))}</div>
                    </div>
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <div className="text-sm text-gray-600">Target Price</div>
                      <div className="text-xl font-bold text-blue-600">$85.00</div>
                    </div>
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
