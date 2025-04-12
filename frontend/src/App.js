import React, { useState, useRef, useEffect, useCallback } from 'react';
// Import icons from lucide-react
import {
  Send, Mic, Settings, User, Bot, Clock, History, Loader2,
  NotebookText, Wallet, TrendingUp, HeartPulse, ChevronDown, ChevronUp,
  Menu, Sun, Moon, LogIn, LogOut // Added Login/Logout icons
} from 'lucide-react';

// --- API Client Helper (Basic Example) ---
// In a real app, consider using libraries like Axios and more robust error handling
const apiClient = {
  async fetch(url, options = {}) {
    const token = localStorage.getItem('aura_token'); // Get token from storage
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers, // Allow overriding headers
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    try {
      const response = await fetch(url, { ...options, headers });
      if (!response.ok) {
        let errorData;
        try {
          // Try to parse JSON error response from backend
          errorData = await response.json();
        } catch (e) {
          // Fallback to text if JSON parsing fails
          errorData = await response.text();
        }
        // Construct a meaningful error message
        const detail = errorData?.detail || errorData || `HTTP error ${response.status}`;
        throw new Error(String(detail));
      }
      // Handle cases where response might be empty (e.g., DELETE 204)
      if (response.status === 204) {
        return null;
      }
      return await response.json(); // Assume JSON response otherwise
    } catch (error) {
      console.error("API Client Error:", error);
      // Re-throw the error so component can handle it
      throw error;
    }
  },

  post(url, data, options = {}) {
    return this.fetch(url, { ...options, method: 'POST', body: JSON.stringify(data) });
  },

  get(url, options = {}) {
    return this.fetch(url, { ...options, method: 'GET' });
  },

  put(url, data, options = {}) {
    return this.fetch(url, { ...options, method: 'PUT', body: JSON.stringify(data) });
  },

  delete(url, options = {}) {
    return this.fetch(url, { ...options, method: 'DELETE' });
  }
};
// --- End API Client Helper ---


// Enhanced Collapsible Section (No changes needed)
const CollapsibleSection = ({ title, icon: Icon, children }) => {
  const [isOpen, setIsOpen] = useState(false);
  return (
    <div className="mb-2 border-b border-gray-700 pb-2">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex justify-between items-center w-full p-2 rounded hover:bg-gray-700 text-left transition-colors duration-200"
      >
        <div className="flex items-center">
          <Icon size={18} className="mr-3 flex-shrink-0" />
          <span>{title}</span>
        </div>
        <ChevronDown size={18} className={`transform transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} />
      </button>
      <div className={`overflow-hidden transition-all duration-300 ease-in-out ${isOpen ? 'max-h-96 opacity-100 py-2' : 'max-h-0 opacity-0'}`}>
        <div className="pl-4 pr-2 text-sm text-gray-300 space-y-2">
          {children}
        </div>
      </div>
    </div>
  );
};

// Simple Login Form Component
const LoginForm = ({ onLoginSuccess, setAuthError }) => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const BACKEND_URL = 'http://localhost:8000/api/v1'; // Make sure this matches

    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsLoading(true);
        setAuthError(''); // Clear previous errors

        // Use FormData for OAuth2PasswordRequestForm compatibility
        const formData = new URLSearchParams();
        formData.append('username', email);
        formData.append('password', password);

        try {
            // Directly fetch for login as apiClient expects JSON, but /token expects form data
            const response = await fetch(`${BACKEND_URL}/auth/token`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: formData.toString(),
            });

            const data = await response.json(); // Always try to parse JSON

            if (!response.ok) {
                 // Use detail from FastAPI's HTTPExceptions if available
                throw new Error(data.detail || `Login failed with status: ${response.status}`);
            }

            onLoginSuccess(data.access_token); // Pass token up on success

        } catch (error) {
            console.error("Login failed:", error);
            setAuthError(error.message || "Login failed. Please check credentials.");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="flex items-center justify-center h-screen bg-gray-100 dark:bg-gray-900">
            <form
                onSubmit={handleSubmit}
                className="p-8 bg-white dark:bg-gray-800 rounded-lg shadow-md w-full max-w-sm"
            >
                <h2 className="text-2xl font-semibold text-center mb-6 text-gray-700 dark:text-gray-200">Login to Aura</h2>
                <div className="mb-4">
                    <label className="block text-sm font-medium mb-1 text-gray-600 dark:text-gray-400" htmlFor="email">Email</label>
                    <input
                        type="email"
                        id="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                        placeholder="user@example.com"
                    />
                </div>
                <div className="mb-6">
                     <label className="block text-sm font-medium mb-1 text-gray-600 dark:text-gray-400" htmlFor="password">Password</label>
                    <input
                        type="password"
                        id="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                        placeholder="********"
                    />
                </div>
                <button
                    type="submit"
                    disabled={isLoading}
                    className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 flex items-center justify-center"
                >
                    {isLoading ? <Loader2 className="animate-spin mr-2" size={20} /> : <LogIn className="mr-2" size={18} />}
                    {isLoading ? 'Logging in...' : 'Login'}
                </button>
                 {/* TODO: Add link to Register component */}
            </form>
        </div>
    );
};


// Main App Component - Integrated Auth and API calls
function App() {
  // State variables
  const [inputText, setInputText] = useState('');
  const [log, setLog] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isDarkMode, setIsDarkMode] = useState(() => {
    if (localStorage.theme === 'dark') return true;
    if (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches) return true;
    return false;
  });

  // --- Authentication State ---
  const [token, setToken] = useState(localStorage.getItem('aura_token')); // Load token on init
  const [isAuthenticated, setIsAuthenticated] = useState(!!token); // Check if token exists
  const [authError, setAuthError] = useState(''); // For login errors
  // const [currentUser, setCurrentUser] = useState(null); // Optional: Store user details

  const logEndRef = useRef(null);
  const BACKEND_URL = 'http://localhost:8000/api/v1';

  // --- Theme Effect ---
  useEffect(() => {
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
      localStorage.theme = 'dark';
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.theme = 'light';
    }
  }, [isDarkMode]);

  // --- Scroll Effect ---
  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [log]);

  // --- Fetch User Details on Auth Change (Optional) ---
  // useEffect(() => {
  //   const fetchUser = async () => {
  //     if (isAuthenticated) {
  //       try {
  //         const user = await apiClient.get(`${BACKEND_URL}/users/me`);
  //         setCurrentUser(user);
  //       } catch (error) {
  //         console.error("Failed to fetch user details:", error);
  //         handleLogout(); // Logout if token is invalid
  //       }
  //     } else {
  //       setCurrentUser(null);
  //     }
  //   };
  //   fetchUser();
  // }, [isAuthenticated]); // Re-run when auth state changes

  // --- Login Handler ---
  const handleLoginSuccess = (newToken) => {
    localStorage.setItem('aura_token', newToken); // Store token
    setToken(newToken);
    setIsAuthenticated(true);
    setAuthError(''); // Clear any previous errors
    // Optionally fetch user details right after login
  };

  // --- Logout Handler ---
  const handleLogout = useCallback(() => {
    localStorage.removeItem('aura_token'); // Remove token
    setToken(null);
    setIsAuthenticated(false);
    // setCurrentUser(null); // Clear user details
    setLog([]); // Clear chat log on logout
    console.log("User logged out");
  }, []); // useCallback ensures function identity doesn't change unnecessarily


  // --- Function to handle sending text data to the backend (Updated) ---
  const handleSend = async (textToSend = inputText) => {
    const trimmedText = textToSend.trim();
    if (!trimmedText || isLoading || !isAuthenticated) return; // Check auth

    setIsLoading(true);
    setLog(prevLog => [...prevLog, { type: 'user', text: trimmedText }]);
    setInputText('');

    try {
      // Use API Client which includes token automatically
      const data = await apiClient.post(`${BACKEND_URL}/process/`, { text: trimmedText });
      setLog(prevLog => [...prevLog, { type: 'aura', text: data.reply || 'No reply received.' }]);
    } catch (error) {
      console.error("Error sending message:", error);
      const errorMsg = `Error: ${error.message}`;
      setLog(prevLog => [...prevLog, { type: 'aura', text: errorMsg, isError: true }]);
      // Handle specific errors, e.g., logout on 401 Unauthorized
      if (error.message.includes('401')) {
        handleLogout();
      }
    } finally {
      setIsLoading(false);
    }
  };

  // --- Placeholder Function for Voice Input (Unchanged) ---
  const handleVoiceInput = () => {
    setIsListening(!isListening);
    console.log("Voice input toggled (implementation pending)");
     if (!isListening) {
       setInputText("Listening...");
       setTimeout(() => {
            const simulatedTranscript = "Simulated voice: Summarize my notes tagged #ProjectX";
            setInputText(simulatedTranscript);
            setIsListening(false);
       }, 2500);
     } else {
        setInputText("");
     }
  };

  // Handle Enter key press (Unchanged)
  const handleKeyPress = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        handleSend();
    }
  };

  // --- Sidebar Actions (Updated with API Client placeholders) ---
  const handleFetchHistoricalSummary = async () => {
      console.log(`Fetching summary for date: ${selectedDate}`);
      setLog(prevLog => [...prevLog, { type: 'aura', text: `Fetching summary for ${selectedDate}...` }]);
      try {
          // Example: Use API Client for authenticated GET request
          // Note: The backend endpoint /summary/{date_str} needs to be created first
          const data = await apiClient.get(`${BACKEND_URL}/summary/${selectedDate}`); // Assuming this endpoint exists
          setLog(prevLog => [...prevLog, { type: 'aura', text: data.summary || `Summary for ${selectedDate} unavailable.` }]);
      } catch (error) {
          console.error("Error fetching summary:", error);
          setLog(prevLog => [...prevLog, { type: 'aura', text: `Error fetching summary: ${error.message}`, isError: true }]);
          if (error.message.includes('401')) handleLogout();
      }
  };

  const handleFetchImportantNotes = async () => {
      console.log(`Fetching important notes for date: ${selectedDate}`);
      setLog(prevLog => [...prevLog, { type: 'aura', text: `Fetching notes for ${selectedDate}...` }]);
       try {
          // Example: Use API Client for authenticated GET request
          const data = await apiClient.get(`${BACKEND_URL}/notes/important/${selectedDate}`);
          // Process and display notes - data.notes should be an array
          const notesText = data.notes && data.notes.length > 0
             ? data.notes.map(note => `- ${note.content.substring(0, 50)}...`).join('\n')
             : `No important notes found for ${selectedDate}.`;
          setLog(prevLog => [...prevLog, { type: 'aura', text: `Notes for ${selectedDate}:\n${notesText}` }]);
      } catch (error) {
          console.error("Error fetching notes:", error);
          setLog(prevLog => [...prevLog, { type: 'aura', text: `Error fetching notes: ${error.message}`, isError: true }]);
          if (error.message.includes('401')) handleLogout();
      }
  };

  // --- Theme Toggle Handler (Unchanged) ---
  const toggleTheme = () => {
    setIsDarkMode(!isDarkMode);
  };

  // --- Conditional Rendering based on Auth ---
  if (!isAuthenticated) {
    return <LoginForm onLoginSuccess={handleLoginSuccess} setAuthError={setAuthError} />;
    // Display auth error message on the login form if needed
  }

  // --- Render Main Authenticated UI ---
  return (
    <div className={`${isDarkMode ? 'dark' : ''}`}>
      <div className="flex h-screen font-sans bg-gray-100 dark:bg-gray-900 text-gray-900 dark:text-gray-100">

        {/* Sidebar Overlay for Mobile */}
        {isSidebarOpen && (
            <div
                className="fixed inset-0 bg-black bg-opacity-50 z-10 md:hidden"
                onClick={() => setIsSidebarOpen(false)}
            ></div>
        )}

        {/* Sidebar */}
        <aside className={`fixed inset-y-0 left-0 w-72 bg-gray-800 text-white p-4 flex flex-col overflow-y-auto transition-transform duration-300 ease-in-out z-20 md:static md:translate-x-0 ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}>
            <div className="flex items-center justify-between mb-6 border-b border-gray-700 pb-3">
                 <h2 className="text-xl font-semibold text-center">Aura Dashboard</h2>
                 <button onClick={() => setIsSidebarOpen(false)} className="md:hidden p-1 text-gray-400 hover:text-white">
                     &times;
                 </button>
            </div>

            {/* Feature Sections (Add onClick handlers to trigger API calls) */}
            <CollapsibleSection title="Historical Data" icon={History}>
                {/* ... (input and buttons - onClick handlers updated above) ... */}
                 <label htmlFor="historicalDate" className="block mb-1 font-medium text-sm">Select Date:</label>
                <input
                    type="date"
                    id="historicalDate"
                    value={selectedDate}
                    onChange={(e) => setSelectedDate(e.target.value)}
                    className="w-full p-1.5 rounded bg-gray-600 border border-gray-500 text-white focus:outline-none focus:ring-1 focus:ring-indigo-400 appearance-none"
                    style={{colorScheme: 'dark'}}
                />
                <button
                    onClick={handleFetchHistoricalSummary} // Updated handler
                    className="w-full mt-2 p-1.5 bg-indigo-600 rounded hover:bg-indigo-700 text-xs transition-colors duration-200"
                >
                    Get Day Summary
                </button>
                <button
                    onClick={handleFetchImportantNotes} // Updated handler
                    className="w-full mt-1 p-1.5 bg-purple-600 rounded hover:bg-purple-700 text-xs transition-colors duration-200"
                >
                    Get Important Notes
                </button>
            </CollapsibleSection>
            {/* Add onClick handlers calling API functions for other sections */}
            <CollapsibleSection title="Global Notes" icon={NotebookText}>
                <p className="text-xs italic">View or add general notes.</p>
                <button className="w-full mt-2 p-1.5 bg-gray-600 rounded hover:bg-gray-500 text-xs transition-colors duration-200">View All Notes</button>
            </CollapsibleSection>
            <CollapsibleSection title="Reminders" icon={Clock}>
                 <p className="text-xs italic">View upcoming reminders.</p>
                 <ul className="list-disc pl-4 mt-1 text-xs space-y-1">
                     <li>Call Mom @ 5 PM (Placeholder)</li>
                     <li>Project Deadline (Placeholder)</li>
                 </ul>
                 <button className="w-full mt-2 p-1.5 bg-gray-600 rounded hover:bg-gray-500 text-xs transition-colors duration-200">Manage Reminders</button>
            </CollapsibleSection>
             {/* ... Other sections ... */}
             <CollapsibleSection title="Daily Spending" icon={Wallet}>
                 <p className="text-xs italic">Log and view today's spending.</p>
                 <p className="font-medium">Today: $45.50 (Placeholder)</p>
                 <button className="w-full mt-2 p-1.5 bg-gray-600 rounded hover:bg-gray-500 text-xs transition-colors duration-200">View Spending Log</button>
            </CollapsibleSection>
            <CollapsibleSection title="Investment Details" icon={TrendingUp}>
                 <p className="text-xs italic">Notes and details about investments.</p>
                 <button className="w-full mt-2 p-1.5 bg-gray-600 rounded hover:bg-gray-500 text-xs transition-colors duration-200">View Investment Notes</button>
            </CollapsibleSection>
            <CollapsibleSection title="Medical Details" icon={HeartPulse}>
                 <p className="text-xs italic">Log symptoms, appointments, meds.</p>
                 <button className="w-full mt-2 p-1.5 bg-gray-600 rounded hover:bg-gray-500 text-xs transition-colors duration-200">View Medical Log</button>
            </CollapsibleSection>

            <div className="flex-grow"></div>

            {/* Settings, Profile, Logout */}
            <div className="mt-auto border-t border-gray-700 pt-3 space-y-1">
               <button onClick={toggleTheme} className="flex items-center w-full p-2 rounded hover:bg-gray-700 text-left transition-colors duration-200">
                    {isDarkMode ? <Sun size={18} className="mr-3" /> : <Moon size={18} className="mr-3" />}
                    {isDarkMode ? "Light Mode" : "Dark Mode"}
               </button>
               <a href="#" className="flex items-center p-2 rounded hover:bg-gray-700 transition-colors duration-200">
                    <Settings size={18} className="mr-3" /> Settings
               </a>
               <a href="#" className="flex items-center p-2 rounded hover:bg-gray-700 transition-colors duration-200">
                    <User size={18} className="mr-3" /> Profile {/* Maybe display currentUser?.email */}
               </a>
               <button onClick={handleLogout} className="flex items-center w-full p-2 rounded hover:bg-red-800 hover:bg-opacity-80 text-left transition-colors duration-200 text-red-300">
                    <LogOut size={18} className="mr-3" /> Logout
               </button>
            </div>
        </aside>

        {/* Main Chat Area (Structure mostly unchanged) */}
        <main className="flex-1 flex flex-col h-screen">
          <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-4 shadow-sm flex items-center justify-between flex-shrink-0">
            <div className="flex items-center">
              <button
                onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                className="mr-4 p-2 rounded md:hidden hover:bg-gray-200 dark:hover:bg-gray-700 focus:outline-none"
                aria-label="Toggle sidebar"
              >
                <Menu size={20} />
              </button>
              <h1 className="text-xl font-semibold text-gray-700 dark:text-gray-200">Aura Assistant</h1>
            </div>
          </header>

          <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-white dark:bg-gray-800">
            {/* Welcome message or initial state */}
             {log.length === 0 && isAuthenticated && (
              <div className="text-center text-gray-500 dark:text-gray-400 mt-10">
                Welcome! How can I help you today?
              </div>
            )}
            {/* Log rendering (unchanged) */}
            {log.map((entry, index) => (
              <div key={index} className={`flex ${entry.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`flex items-start max-w-xl lg:max-w-2xl ${entry.type === 'user' ? 'flex-row-reverse' : ''}`}>
                  <div className={`flex-shrink-0 h-8 w-8 rounded-full flex items-center justify-center text-white ${entry.type === 'user' ? 'bg-blue-500 ml-2' : 'bg-indigo-500 mr-2'}`}>
                    {entry.type === 'user' ? <User size={18} /> : <Bot size={18} />}
                  </div>
                  <div className={`px-4 py-2 rounded-lg shadow-md ${entry.type === 'user'
                      ? 'bg-blue-500 text-white'
                      : entry.isError ? 'bg-red-100 dark:bg-red-900 dark:bg-opacity-30 text-red-700 dark:text-red-300 border border-red-300 dark:border-red-700' : 'bg-gray-200 text-gray-800 dark:bg-gray-700 dark:text-gray-200'
                    }`}>
                    <p className="whitespace-pre-wrap">{entry.text}</p>
                  </div>
                </div>
              </div>
            ))}
            <div ref={logEndRef} />
          </div>

          {/* Loading Indicator (unchanged) */}
          {isLoading && (
            <div className="px-4 pb-2 flex items-center justify-center text-gray-500 dark:text-gray-400 flex-shrink-0">
                <Loader2 size={18} className="animate-spin mr-2" />
                <span>Aura is thinking...</span>
            </div>
          )}

          {/* Input Area (unchanged) */}
          <div className="bg-gray-50 dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700 p-4 flex-shrink-0">
            <div className="flex items-center bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg shadow-sm px-2 py-1 focus-within:ring-2 focus-within:ring-blue-500">
              <textarea
                rows="1"
                value={inputText}
                onChange={(e) => {
                    setInputText(e.target.value);
                    e.target.style.height = 'auto';
                    e.target.style.height = `${e.target.scrollHeight}px`;
                }}
                onKeyPress={handleKeyPress}
                placeholder="Type your command or note... (Shift+Enter for newline)"
                className="flex-grow p-2 border-none focus:ring-0 resize-none overflow-y-auto text-sm bg-transparent dark:text-gray-200 placeholder-gray-400 dark:placeholder-gray-500"
                style={{ maxHeight: '120px' }}
                disabled={isLoading || isListening}
              />
              <button
                onClick={handleVoiceInput}
                className={`ml-2 p-2 rounded-full hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-300 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-indigo-500 transition-colors duration-200 ${isListening ? 'text-red-500 animate-pulse' : ''}`}
                disabled={isLoading}
                title="Voice Input (Placeholder)"
              >
                <Mic size={20} />
              </button>
              <button
                onClick={() => handleSend()}
                className="ml-2 p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
                disabled={isLoading || !inputText.trim()}
                aria-label="Send message"
              >
                <Send size={20} />
              </button>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;
