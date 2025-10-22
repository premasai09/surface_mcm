import React, { useState, useEffect } from 'react';

// LoginPage Component
function LoginPage({ onLogin }) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Sign in to your account
          </h2>
        </div>
        <div className="mt-8 space-y-6">
          <div>
            <button
              onClick={onLogin}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition duration-150 ease-in-out"
            >
              Login
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ResultsDisplay Component
function ResultsDisplay({ results }) {
  if (!results) return null;

  return (
    <div className="mt-8 space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">Campaign Results</h2>
      
      {/* Audience Segments Card */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <div className="flex items-center mb-3">
          <svg className="w-5 h-5 text-blue-600 mr-2" fill="currentColor" viewBox="0 0 20 20">
            <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
          <h3 className="text-lg font-semibold text-blue-900">Target Audience</h3>
        </div>
        <p className="text-blue-800">{results.audience_segments}</p>
      </div>

      {/* Content Card */}
      <div className="bg-green-50 border border-green-200 rounded-lg p-6">
        <div className="flex items-center mb-3">
          <svg className="w-5 h-5 text-green-600 mr-2" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd"/>
          </svg>
          <h3 className="text-lg font-semibold text-green-900">Campaign Content</h3>
        </div>
        <div className="space-y-4">
          {results.content.map((item, index) => (
            <div key={index} className="p-3 bg-white rounded-md border border-gray-200">
              <h4 className="text-indigo-600 font-medium mb-2">{item.segment}</h4>
              <p className="text-gray-700">{item.copy}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Review Task Card */}
      <div className="bg-purple-50 border border-purple-200 rounded-lg p-6">
        <div className="flex items-center mb-3">
          <svg className="w-5 h-5 text-purple-600 mr-2" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clipRule="evenodd"/>
          </svg>
          <h3 className="text-lg font-semibold text-purple-900">Review Task</h3>
        </div>
        {results.review_task && (
          <div>
            <h4 className="font-medium text-purple-900">{results.review_task.title}</h4>
            <p className="text-purple-800 mt-2">{results.review_task.details}</p>
            <div className="mt-3">
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                results.review_task.status === 'completed' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
              }`}>
                {results.review_task.status}
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// DashboardPage Component
function DashboardPage({ onTaskCreated }) {
  const [campaignBrief, setCampaignBrief] = useState('');
  const [backendStatus, setBackendStatus] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);

  useEffect(() => {
    // Fetch data from backend when component mounts
    const fetchBackendStatus = async () => {
      try {
        const response = await fetch('http://localhost:9000/api/hello');
        const data = await response.json();
        setBackendStatus(data.message);
      } catch (error) {
        console.error('Error fetching backend status:', error);
        setBackendStatus('Backend connection failed');
      }
    };

    fetchBackendStatus();
  }, []); // Empty dependency array means this runs once on mount

  const handleGenerateCampaign = async () => {
    if (!campaignBrief.trim()) {
      alert('Please enter a campaign brief');
      return;
    }

    setLoading(true);
    setResults(null);

    try {
      const response = await fetch('http://localhost:9000/api/run-campaign', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          intent_brief: campaignBrief
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setResults(data);
      
      // If we have a review task, add it to the task list
      if (data.review_task) {
        onTaskCreated(data.review_task);
      }
    } catch (error) {
      console.error('Error generating campaign:', error);
      alert('Failed to generate campaign. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Campaign Manager
          </h1>
          {backendStatus && (
            <div className="mb-8">
              <div className="inline-flex items-center px-4 py-2 rounded-md text-sm font-medium bg-green-100 text-green-800 border border-green-200">
                <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                Backend Status: {backendStatus}
              </div>
            </div>
          )}
        </div>
        
        <div className="bg-white shadow-lg rounded-lg p-8">
          <div className="mb-6">
            <label htmlFor="campaign-brief" className="block text-sm font-medium text-gray-700 mb-2">
              Campaign Brief
            </label>
            <textarea
              id="campaign-brief"
              rows={8}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 resize-none"
              placeholder="Enter your campaign brief here..."
              value={campaignBrief}
              onChange={(e) => setCampaignBrief(e.target.value)}
            />
          </div>
          
          <div className="text-center">
            <button
              onClick={handleGenerateCampaign}
              disabled={loading}
              className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition duration-150 ease-in-out disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Generating...
                </>
              ) : (
                'Generate Campaign'
              )}
            </button>
          </div>
        </div>
        
        {/* Results Display */}
        <ResultsDisplay results={results} />
      </div>
    </div>
  );
}

// Main App Component
// TaskPage Component
function TaskPage({ tasks }) {
  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <h2 className="text-2xl font-bold mb-6 text-gray-900">My Tasks</h2>
      <div className="space-y-4">
        {tasks.map((task) => (
          <div key={task.id} className="bg-white shadow rounded-lg p-6 border border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">{task.title}</h3>
            <p className="mt-2 text-gray-600">{task.details}</p>
            <div className="mt-4 flex justify-between items-center">
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                task.status === 'completed' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
              }`}>
                {task.status}
              </span>
              <button 
                className="text-sm text-indigo-600 hover:text-indigo-900"
                onClick={() => console.log('Mark as completed - TODO')}
              >
                Mark as completed
              </button>
            </div>
          </div>
        ))}
        {tasks.length === 0 && (
          <div className="text-center py-12 bg-gray-50 rounded-lg">
            <p className="text-gray-500">No tasks yet. Generate some campaigns to create tasks!</p>
          </div>
        )}
      </div>
    </div>
  );
}

// Main App Component
function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [tasks, setTasks] = useState([]);

  const handleLogin = () => {
    setIsLoggedIn(true);
  };

  const addNewTask = (task) => {
    setTasks(prevTasks => [...prevTasks, task]);
  };

  if (!isLoggedIn) {
    return <LoginPage onLogin={handleLogin} />;
  }

  return (
    <div className="App min-h-screen bg-gray-50">
      {/* Tab Navigation */}
      <div className="bg-white shadow">
        <div className="max-w-4xl mx-auto">
          <div className="flex space-x-8 py-4">
            <button
              onClick={() => setActiveTab('dashboard')}
              className={`px-3 py-2 font-medium text-sm rounded-md ${
                activeTab === 'dashboard'
                  ? 'bg-indigo-100 text-indigo-700'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              Dashboard
            </button>
            <button
              onClick={() => setActiveTab('tasks')}
              className={`px-3 py-2 font-medium text-sm rounded-md ${
                activeTab === 'tasks'
                  ? 'bg-indigo-100 text-indigo-700'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              My Tasks
            </button>
          </div>
        </div>
      </div>

      {/* Content Area */}
      <div className="max-w-4xl mx-auto">
        {activeTab === 'dashboard' ? (
          <DashboardPage onTaskCreated={addNewTask} />
        ) : (
          <TaskPage tasks={tasks} />
        )}
      </div>
    </div>
  );
}

export default App;
