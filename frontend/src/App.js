import React, { useState, useRef, useEffect, useCallback } from 'react';
// Import icons from lucide-react
import {
  Send, Mic, Settings, User, Bot, Clock, History, Loader2,
  NotebookText, Wallet, TrendingUp, HeartPulse, ChevronDown,
  Menu, Sun, Moon, LogIn, LogOut, UserPlus, RefreshCw, X // Added X
} from 'lucide-react';

// --- API Client Helper ---
// Centralized place to handle fetch requests and add auth token
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
        try { errorData = await response.json(); } catch (e) { errorData = await response.text(); }
        const detail = errorData?.detail || errorData || `HTTP error ${response.status}`;
        throw new Error(String(detail));
      }
      if (response.status === 204) return null; // Handle No Content response
      return await response.json();
    } catch (error) {
      console.error("API Client Error:", error);
      // Add specific handling for 401 Unauthorized if needed globally
      // if (error.message.includes('401')) { /* trigger logout? */ }
      throw error; // Re-throw for component-level handling
    }
  },
  post(url, data, options = {}) { return this.fetch(url, { ...options, method: 'POST', body: JSON.stringify(data) }); },
  get(url, options = {}) { return this.fetch(url, { ...options, method: 'GET' }); },
  put(url, data, options = {}) { return this.fetch(url, { ...options, method: 'PUT', body: JSON.stringify(data) }); },
  delete(url, options = {}) { return this.fetch(url, { ...options, method: 'DELETE' }); }
};
// --- End API Client Helper ---


// --- Collapsible Section Component ---
// Added isOpen prop and onToggle callback for external control if needed later
const CollapsibleSection = ({ title, icon: Icon, children, isOpen: externalOpen, onToggle }) => {
  const [internalOpen, setInternalOpen] = useState(false);
  // Allow external control if isOpen prop is provided, otherwise use internal state
  const isOpen = externalOpen !== undefined ? externalOpen : internalOpen;
  const toggle = () => {
    if (onToggle) {
      onToggle(!isOpen); // Call external handler if provided
    } else {
      setInternalOpen(!internalOpen); // Use internal state otherwise
    }
  };

  return (
    <div className="mb-2 border-b border-gray-700 pb-2">
      <button onClick={toggle} className="flex justify-between items-center w-full p-2 rounded hover:bg-gray-700 text-left transition-colors duration-200">
        <div className="flex items-center"><Icon size={18} className="mr-3 flex-shrink-0" /><span>{title}</span></div>
        <ChevronDown size={18} className={`transform transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} />
      </button>
       {/* Increased max-h for potentially longer lists */}
      <div className={`overflow-hidden transition-all duration-300 ease-in-out ${isOpen ? 'max-h-[300px] opacity-100 py-2 overflow-y-auto' : 'max-h-0 opacity-0'}`}> {/* Increased max-h, added overflow-y */}
        <div className="pl-4 pr-2 text-sm text-gray-300 space-y-2">
          {children}
        </div>
      </div>
    </div>
  );
};

// --- Login Form Component ---
const LoginForm = ({ onLoginSuccess, authError, setAuthError, switchToRegister }) => {
    const [email, setEmail] = useState('user@example.com'); // Default for easier testing
    const [password, setPassword] = useState('password'); // Default for easier testing
    const [isLoading, setIsLoading] = useState(false);
    const BACKEND_URL = 'http://localhost:8000/api/v1';

    const handleSubmit = async (e) => {
        e.preventDefault(); setIsLoading(true); setAuthError('');
        const formData = new URLSearchParams();
        formData.append('username', email); formData.append('password', password);
        try {
            const response = await fetch(`${BACKEND_URL}/auth/token`, { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body: formData.toString() });
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || `Login failed: ${response.status}`);
            onLoginSuccess(data.access_token);
        } catch (error) { console.error("Login failed:", error); setAuthError(error.message || "Login failed."); }
        finally { setIsLoading(false); }
    };

    return (
        <div className="flex items-center justify-center h-screen bg-gray-100 dark:bg-gray-900">
            <form onSubmit={handleSubmit} className="p-8 bg-white dark:bg-gray-800 rounded-lg shadow-md w-full max-w-sm">
                <h2 className="text-2xl font-semibold text-center mb-6 text-gray-700 dark:text-gray-200">Login to Aura</h2>
                {authError && (<p className="mb-4 text-center text-sm text-red-500 dark:text-red-400 bg-red-100 dark:bg-red-900 dark:bg-opacity-30 border border-red-300 dark:border-red-700 p-2 rounded">{authError}</p>)}
                <div className="mb-4">
                    <label className="block text-sm font-medium mb-1 text-gray-600 dark:text-gray-400" htmlFor="email">Email</label>
                    <input type="email" id="email" value={email} onChange={(e) => setEmail(e.target.value)} required className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100" placeholder="user@example.com" />
                </div>
                <div className="mb-6">
                     <label className="block text-sm font-medium mb-1 text-gray-600 dark:text-gray-400" htmlFor="password">Password</label>
                    <input type="password" id="password" value={password} onChange={(e) => setPassword(e.target.value)} required className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100" placeholder="********" />
                </div>
                <button type="submit" disabled={isLoading} className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 flex items-center justify-center">
                    {isLoading ? <Loader2 className="animate-spin mr-2" size={20} /> : <LogIn className="mr-2" size={18} />} {isLoading ? 'Logging in...' : 'Login'}
                </button>
                <p className="mt-4 text-center text-sm text-gray-600 dark:text-gray-400"> Don't have an account?{' '} <button type="button" onClick={switchToRegister} className="font-medium text-blue-600 hover:text-blue-500 dark:text-blue-400 dark:hover:text-blue-300"> Register here </button> </p>
            </form>
        </div>
    );
};

// --- Registration Form Component ---
const RegisterForm = ({ onRegisterSuccess, authError, setAuthError, switchToLogin }) => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [fullName, setFullName] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const BACKEND_URL = 'http://localhost:8000/api/v1';

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (password !== confirmPassword) { setAuthError("Passwords do not match."); return; }
        setIsLoading(true); setAuthError('');
        const userData = { email: email, password: password, full_name: fullName || null };
        try {
            const data = await apiClient.post(`${BACKEND_URL}/auth/register/`, userData);
            console.log("Registration successful:", data);
            onRegisterSuccess(); // Notify App component
        } catch (error) { console.error("Registration failed:", error); setAuthError(error.message || "Registration failed."); }
        finally { setIsLoading(false); }
    };

    return (
         <div className="flex items-center justify-center h-screen bg-gray-100 dark:bg-gray-900">
            <form onSubmit={handleSubmit} className="p-8 bg-white dark:bg-gray-800 rounded-lg shadow-md w-full max-w-sm">
                <h2 className="text-2xl font-semibold text-center mb-6 text-gray-700 dark:text-gray-200">Register for Aura</h2>
                {authError && (<p className="mb-4 text-center text-sm text-red-500 dark:text-red-400 bg-red-100 dark:bg-red-900 dark:bg-opacity-30 border border-red-300 dark:border-red-700 p-2 rounded">{authError}</p>)}
                <div className="mb-4">
                    <label className="block text-sm font-medium mb-1 text-gray-600 dark:text-gray-400" htmlFor="reg-email">Email</label>
                    <input type="email" id="reg-email" value={email} onChange={(e) => setEmail(e.target.value)} required className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100" placeholder="user@example.com" />
                </div>
                 <div className="mb-4">
                    <label className="block text-sm font-medium mb-1 text-gray-600 dark:text-gray-400" htmlFor="reg-fullname">Full Name (Optional)</label>
                    <input type="text" id="reg-fullname" value={fullName} onChange={(e) => setFullName(e.target.value)} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100" placeholder="Jane Doe" />
                </div>
                <div className="mb-4">
                     <label className="block text-sm font-medium mb-1 text-gray-600 dark:text-gray-400" htmlFor="reg-password">Password</label>
                    <input type="password" id="reg-password" value={password} onChange={(e) => setPassword(e.target.value)} required className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100" placeholder="********" />
                </div>
                 <div className="mb-6">
                     <label className="block text-sm font-medium mb-1 text-gray-600 dark:text-gray-400" htmlFor="reg-confirm-password">Confirm Password</label>
                    <input type="password" id="reg-confirm-password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} required className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100" placeholder="********" />
                </div>
                <button type="submit" disabled={isLoading} className="w-full bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50 flex items-center justify-center">
                    {isLoading ? <Loader2 className="animate-spin mr-2" size={20} /> : <UserPlus className="mr-2" size={18} />} {isLoading ? 'Registering...' : 'Register'}
                </button>
                <p className="mt-4 text-center text-sm text-gray-600 dark:text-gray-400"> Already have an account?{' '} <button type="button" onClick={switchToLogin} className="font-medium text-blue-600 hover:text-blue-500 dark:text-blue-400 dark:hover:text-blue-300"> Login here </button> </p>
            </form>
        </div>
    );
};
// --- End Registration Form Component ---

// --- New Profile Modal Component ---
const ProfileModal = ({ isOpen, onClose, currentUser, refreshUser }) => {
  const [editableFullName, setEditableFullName] = useState('');
  const [isUpdating, setIsUpdating] = useState(false);
  const [updateError, setUpdateError] = useState('');
  const [updateSuccess, setUpdateSuccess] = useState('');
  const BACKEND_URL = 'http://localhost:8000/api/v1';

  // Update editable name when currentUser data changes (e.g., on modal open or refresh)
  useEffect(() => {
      if (currentUser) {
          setEditableFullName(currentUser.full_name || '');
      }
  }, [currentUser]);

  const handleProfileUpdate = async (e) => {
      e.preventDefault();
      setIsUpdating(true);
      setUpdateError('');
      setUpdateSuccess('');

      try {
          const updatedData = { full_name: editableFullName };
          // Use apiClient to make the authenticated PUT request
          const updatedUser = await apiClient.put(`${BACKEND_URL}/users/me`, updatedData);
          setUpdateSuccess("Profile updated successfully!");
          refreshUser(); // Refresh user data in the App component
          // Close modal after a short delay
          setTimeout(() => {
               onClose();
               setUpdateSuccess(''); // Clear success message
          }, 1500);

      } catch (error) {
          console.error("Profile update failed:", error);
          setUpdateError(error.message || "Failed to update profile.");
      } finally {
          setIsUpdating(false);
      }
  };

  // Close modal if isOpen becomes false
  if (!isOpen) {
      return null;
  }

  return (
      // Modal backdrop
      <div className="fixed inset-0 bg-black bg-opacity-60 z-40 flex items-center justify-center p-4">
          {/* Modal content */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-md p-6 relative">
              {/* Close button */}
              <button
                  onClick={onClose}
                  className="absolute top-3 right-3 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
                  aria-label="Close profile modal"
              >
                  <X size={20} />
              </button>

              <h2 className="text-xl font-semibold mb-4 text-gray-800 dark:text-gray-100">Your Profile</h2>

              {/* Display Update Status */}
               {updateError && (<p className="mb-3 text-sm text-red-500 dark:text-red-400">{updateError}</p>)}
               {updateSuccess && (<p className="mb-3 text-sm text-green-500 dark:text-green-400">{updateSuccess}</p>)}

              <form onSubmit={handleProfileUpdate}>
                  {/* Email (Read-only) */}
                  <div className="mb-4">
                      <label className="block text-sm font-medium mb-1 text-gray-600 dark:text-gray-400" htmlFor="prof-email">Email</label>
                      <input
                          type="email" id="prof-email"
                          value={currentUser?.email || 'Loading...'}
                          readOnly
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400 cursor-not-allowed"
                      />
                  </div>

                  {/* Full Name (Editable) */}
                  <div className="mb-6">
                      <label className="block text-sm font-medium mb-1 text-gray-600 dark:text-gray-400" htmlFor="prof-fullname">Full Name</label>
                      <input
                          type="text" id="prof-fullname"
                          value={editableFullName}
                          onChange={(e) => setEditableFullName(e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                          placeholder="Enter your full name"
                      />
                  </div>

                  {/* Action Buttons */}
                  <div className="flex justify-end space-x-3">
                      <button
                          type="button"
                          onClick={onClose}
                          className="px-4 py-2 rounded-md border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-gray-500"
                      >
                          Cancel
                      </button>
                      <button
                          type="submit"
                          disabled={isUpdating}
                          className="px-4 py-2 rounded-md bg-blue-600 text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 flex items-center justify-center"
                      >
                           {isUpdating ? <Loader2 className="animate-spin mr-2" size={18} /> : null}
                           {isUpdating ? 'Saving...' : 'Save Changes'}
                      </button>
                  </div>
              </form>
          </div>
      </div>
  );
};
// --- End Profile Modal Component ---


// --- Main App Component ---
function App() {
  // State variables
  const [inputText, setInputText] = useState('');
  const [log, setLog] = useState([]);
  const [isLoading, setIsLoading] = useState(false); // Chat processing loading
  const [isListening, setIsListening] = useState(false);
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isDarkMode, setIsDarkMode] = useState(() => { /* ... */ });

  // --- Authentication State ---
  const [token, setToken] = useState(localStorage.getItem('aura_token'));
  const [isAuthenticated, setIsAuthenticated] = useState(!!token);
  const [authError, setAuthError] = useState('');
  const [authMode, setAuthMode] = useState('login');

  // --- State for Fetched Data ---
  const [globalNotes, setGlobalNotes] = useState([]);
  const [isLoadingGlobalNotes, setIsLoadingGlobalNotes] = useState(false);
  const [globalNotesError, setGlobalNotesError] = useState('');
  const [reminders, setReminders] = useState([]);
  const [isLoadingReminders, setIsLoadingReminders] = useState(false);
  const [remindersError, setRemindersError] = useState('');
  const [spendingLogs, setSpendingLogs] = useState([]);
  const [isLoadingSpending, setIsLoadingSpending] = useState(false);
  const [spendingError, setSpendingError] = useState('');
  const [spendingTotal, setSpendingTotal] = useState(null);
  // ** New State for Investments **
  const [investmentNotes, setInvestmentNotes] = useState([]);
  const [isLoadingInvestmentNotes, setIsLoadingInvestmentNotes] = useState(false);
  const [investmentNotesError, setInvestmentNotesError] = useState('');
  // ** New State for Medical **
  const [medicalLogs, setMedicalLogs] = useState([]);
  const [isLoadingMedicalLogs, setIsLoadingMedicalLogs] = useState(false);
  const [medicalLogsError, setMedicalLogsError] = useState('');

  const [currentUser, setCurrentUser] = useState(null); // Store user details {id, email, full_name, is_active}
  const [isLoadingUser, setIsLoadingUser] = useState(false);
  const [isProfileModalOpen, setIsProfileModalOpen] = useState(false);


  const logEndRef = useRef(null);
  const BACKEND_URL = 'http://localhost:8000/api/v1';

  // --- Theme Effect ---
  useEffect(() => { if (isDarkMode) { document.documentElement.classList.add('dark'); localStorage.theme = 'dark'; } else { document.documentElement.classList.remove('dark'); localStorage.theme = 'light'; } }, [isDarkMode]);
  // --- Scroll Effect ---
  useEffect(() => { logEndRef.current?.scrollIntoView({ behavior: "smooth" }); }, [log]);

  // --- Login/Logout/Register Handlers ---
  const handleLoginSuccess = (newToken) => { localStorage.setItem('aura_token', newToken); setToken(newToken); setIsAuthenticated(true); setAuthError(''); console.log("Login Success."); };
  const handleLogout = useCallback(() => {
      localStorage.removeItem('aura_token'); setToken(null); setIsAuthenticated(false); setLog([]);
      // Reset all fetched data states
      setGlobalNotes([]); setGlobalNotesError('');
      setReminders([]); setRemindersError('');
      setSpendingLogs([]); setSpendingError(''); setSpendingTotal(null);
      setInvestmentNotes([]); setInvestmentNotesError(''); // Reset investments
      setMedicalLogs([]); setMedicalLogsError(''); // Reset medical
      setCurrentUser(null); // Clear current user data
      setIsLoadingUser(false); // Reset loading state
      console.log("User logged out");
  }, []); // Added investment/medical reset
  const handleRegisterSuccess = () => { console.log("Registration successful! Please login."); setAuthError(''); setAuthMode('login'); };

  // --- handleSend Function (Chat Processing) ---
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

  // --- Voice Input Placeholder ---
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

  // --- Sidebar Action Implementations ---
   // --- Sidebar Action Implementations ---
   const handleFetchHistoricalSummary = async () => {
    // ... (Implementation using apiClient as before) ...
    console.log(`Fetching summary for date: ${selectedDate}`);
    setLog(prevLog => [...prevLog, { type: 'aura', text: `Fetching summary for ${selectedDate}...` }]);
    try {
        const data = await apiClient.get(`${BACKEND_URL}/summary/${selectedDate}`);
        setLog(prevLog => [...prevLog, { type: 'aura', text: data.summary || `Summary for ${selectedDate} unavailable.` }]);
    } catch (error) {
        console.error("Error fetching summary:", error);
        setLog(prevLog => [...prevLog, { type: 'aura', text: `Error fetching summary: ${error.message}`, isError: true }]);
        if (error.message.includes('401')) handleLogout();
    }
};
const handleFetchImportantNotes = async () => {
    // ... (Implementation using apiClient as before) ...
     console.log(`Fetching important notes for date: ${selectedDate}`);
    setLog(prevLog => [...prevLog, { type: 'aura', text: `Fetching notes for ${selectedDate}...` }]);
     try {
        const data = await apiClient.get(`${BACKEND_URL}/notes/important/${selectedDate}`);
        const notesText = data.notes && data.notes.length > 0 ? data.notes.map(note => `- ${note.content.substring(0, 50)}...`).join('\n') : `No important notes found for ${selectedDate}.`;
        setLog(prevLog => [...prevLog, { type: 'aura', text: `Notes for ${selectedDate}:\n${notesText}` }]);
    } catch (error) {
        console.error("Error fetching notes:", error);
        setLog(prevLog => [...prevLog, { type: 'aura', text: `Error fetching notes: ${error.message}`, isError: true }]);
        if (error.message.includes('401')) handleLogout();
    }
};

 // --- Fetch Current User Function ---
 const fetchCurrentUser = useCallback(async () => {
  if (!isAuthenticated) return;
  console.log("Fetching current user data...");
  setIsLoadingUser(true); // Optional: add loading state for user fetch
  try {
      const userData = await apiClient.get(`${BACKEND_URL}/users/me`);
      setCurrentUser(userData);
      console.log("Current user data:", userData);
  } catch (error) {
      console.error("Failed to fetch current user:", error);
      // If fetching user fails (e.g., invalid token), log out
      if (error.message.includes('401') || error.message.includes('validate credentials')) {
          handleLogout();
      }
  } finally {
      setIsLoadingUser(false);
  }
}, [isAuthenticated, handleLogout]); // Re-fetch if auth state changes

  // --- Fetch Data Functions ---
  const fetchGlobalNotes = useCallback(async () => {
    if (!isAuthenticated) return; // Don't fetch if not logged in
    console.log("Fetching global notes...");
    setIsLoadingGlobalNotes(true);
    setGlobalNotesError('');
    try {
        const data = await apiClient.get(`${BACKEND_URL}/notes/global`);
        setGlobalNotes(data.notes || []); // Assuming response is { notes: [...] }
    } catch (error) {
        console.error("Error fetching global notes:", error);
        setGlobalNotesError(`Failed to load notes: ${error.message}`);
        if (error.message.includes('401')) handleLogout();
    } finally {
        setIsLoadingGlobalNotes(false);
    }
  }, [isAuthenticated, handleLogout]);

   const fetchReminders = useCallback(async (activeOnly = true) => {
    if (!isAuthenticated) return;
    console.log("Fetching reminders...");
    setIsLoadingReminders(true);
    setRemindersError('');
    try {
        // Fetch active reminders by default, adjust query param if needed
        const data = await apiClient.get(`${BACKEND_URL}/reminders/?active_only=${activeOnly}`);
        setReminders(data.reminders || []); // Assuming response is { reminders: [...] }
    } catch (error) {
        console.error("Error fetching reminders:", error);
        setRemindersError(`Failed: ${error.message}`);
        if (error.message.includes('401')) handleLogout();
    } finally {
        setIsLoadingReminders(false);
    }
  }, [isAuthenticated, handleLogout]); // Dependencies
  
  const fetchSpendingLogs = useCallback(async (date = null) => { // Allow filtering by date
    if (!isAuthenticated) return;
    const filterDate = date || new Date().toISOString().split('T')[0]; // Default to today if no date passed
    console.log(`Fetching spending logs for date: ${filterDate}`);
    setIsLoadingSpending(true);
    setSpendingError('');
    try {
        // Construct URL with query parameters for filtering (example for today)
        // TODO: Add date range filters later if needed
        const url = `${BACKEND_URL}/spending/?start_date=${filterDate}&end_date=${filterDate}`;
        const data = await apiClient.get(url);
        setSpendingLogs(data.spending_logs || []);
        setSpendingTotal(data.total_amount); // Backend needs to calculate and return this
    } catch (error) {
        console.error("Error fetching spending logs:", error);
        setSpendingError(`Failed: ${error.message}`);
        if (error.message.includes('401')) handleLogout();
    } finally {
        setIsLoadingSpending(false);
    }
  }, [isAuthenticated, handleLogout]); // Dependencies
  
  // --- Fetch Investment Notes Implementation ---
  const fetchInvestmentNotes = useCallback(async () => {
    if (!isAuthenticated) return;
    console.log("Fetching investment notes...");
    setIsLoadingInvestmentNotes(true);
    setInvestmentNotesError('');
    try {
        const data = await apiClient.get(`${BACKEND_URL}/investments/`); // Assuming GET /investments/ endpoint exists
        setInvestmentNotes(data.investment_notes || []); // Adjust based on actual API response structure
        // Log fetched data for debugging until UI is built
        console.log("Fetched Investment Notes:", data.investment_notes);
    } catch (error) {
        console.error("Error fetching investment notes:", error);
        setInvestmentNotesError(`Failed: ${error.message}`);
        if (error.message.includes('401')) handleLogout();
    } finally {
        setIsLoadingInvestmentNotes(false);
    }
  }, [isAuthenticated, handleLogout]); // Dependencies

  // --- Fetch Medical Logs Implementation ---
  const fetchMedicalLogs = useCallback(async () => {
    if (!isAuthenticated) return;
    console.log("Fetching medical logs...");
    setIsLoadingMedicalLogs(true);
    setMedicalLogsError('');
    try {
        // Assuming GET /medical/ endpoint exists, potentially add filters like date range later
        const data = await apiClient.get(`${BACKEND_URL}/medical/`);
        setMedicalLogs(data.medical_logs || []); // Adjust based on actual API response structure
        // Log fetched data for debugging until UI is built
         console.log("Fetched Medical Logs:", data.medical_logs);
    } catch (error) {
        console.error("Error fetching medical logs:", error);
        setMedicalLogsError(`Failed: ${error.message}`);
        if (error.message.includes('401')) handleLogout();
    } finally {
        setIsLoadingMedicalLogs(false);
    }
  }, [isAuthenticated, handleLogout]); // Dependencies


  // Fetch initial data on mount after authentication
  useEffect(() => {
    if (isAuthenticated) {
        fetchGlobalNotes();
        fetchReminders();
        fetchSpendingLogs();
        fetchInvestmentNotes(); // Fetch investments
        fetchMedicalLogs(); // Fetch medical logs
    }
    // Clear data on logout (handled in handleLogout)
  }, [isAuthenticated, fetchGlobalNotes, fetchReminders, fetchSpendingLogs, fetchInvestmentNotes, fetchMedicalLogs]); // Add new fetch functions

  // --- Theme Toggle ---
  const toggleTheme = () => { setIsDarkMode(!isDarkMode); };


  // --- Conditional Rendering for Auth ---
  if (!isAuthenticated) {
    return authMode === 'login' ? ( <LoginForm onLoginSuccess={handleLoginSuccess} authError={authError} setAuthError={setAuthError} switchToRegister={() => { setAuthMode('register'); setAuthError(''); }} /> )
           : ( <RegisterForm onRegisterSuccess={handleRegisterSuccess} authError={authError} setAuthError={setAuthError} switchToLogin={() => { setAuthMode('login'); setAuthError(''); }} /> );
  }

  // --- Render Main Authenticated UI ---
  return (
    <div className={`${isDarkMode ? 'dark' : ''}`}>
      <div className="flex h-screen font-sans bg-gray-100 dark:bg-gray-900 text-gray-900 dark:text-gray-100">
        {/* Sidebar Overlay */}
        {isSidebarOpen && ( <div className="fixed inset-0 bg-black bg-opacity-50 z-10 md:hidden" onClick={() => setIsSidebarOpen(false)}></div> )}

        {/* Sidebar */}
        <aside className={`fixed inset-y-0 left-0 w-72 bg-gray-800 text-white p-4 flex flex-col overflow-y-auto transition-transform duration-300 ease-in-out z-20 md:static md:translate-x-0 ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}>
            {/* Header */}
            <div className="flex items-center justify-between mb-6 border-b border-gray-700 pb-3"> <h2 className="text-xl font-semibold text-center">Aura Dashboard</h2> <button onClick={() => setIsSidebarOpen(false)} className="md:hidden p-1 text-gray-400 hover:text-white"> &times; </button> </div>

            {/* Historical Data Section */}
            <CollapsibleSection title="Historical Data" icon={History}>
                 <label htmlFor="historicalDate" className="block mb-1 font-medium text-sm">Select Date:</label>
                <input type="date" id="historicalDate" value={selectedDate} onChange={(e) => setSelectedDate(e.target.value)} className="w-full p-1.5 rounded bg-gray-600 border border-gray-500 text-white focus:outline-none focus:ring-1 focus:ring-indigo-400 appearance-none" style={{colorScheme: 'dark'}} />
                <button onClick={handleFetchHistoricalSummary} className="w-full mt-2 p-1.5 bg-indigo-600 rounded hover:bg-indigo-700 text-xs transition-colors duration-200"> Get Day Summary </button>
                <button onClick={handleFetchImportantNotes} className="w-full mt-1 p-1.5 bg-purple-600 rounded hover:bg-purple-700 text-xs transition-colors duration-200"> Get Important Notes </button>
            </CollapsibleSection>

            {/* Global Notes Section - Integrated */}
            <CollapsibleSection title="Global Notes" icon={NotebookText}>
                <div className="flex justify-between items-center mb-1"> <p className="text-xs italic">General notes.</p> <button onClick={fetchGlobalNotes} disabled={isLoadingGlobalNotes} title="Refresh Notes" className="p-1 text-gray-400 hover:text-white disabled:opacity-50"> {isLoadingGlobalNotes ? <Loader2 size={14} className="animate-spin"/> : <RefreshCw size={14} />} </button> </div>
                {isLoadingGlobalNotes && <p className="text-xs text-center">Loading notes...</p>}
                {globalNotesError && <p className="text-xs text-red-400">{globalNotesError}</p>}
                {!isLoadingGlobalNotes && !globalNotesError && ( globalNotes.length > 0 ? ( <ul className="list-disc pl-4 mt-1 text-xs space-y-1 max-h-40 overflow-y-auto"> {globalNotes.map(note => ( <li key={note.id} title={note.content}> {note.content.substring(0, 40)}{note.content.length > 40 ? '...' : ''} </li> ))} </ul> ) : ( <p className="text-xs text-gray-400 italic">No global notes found.</p> ) )}
            </CollapsibleSection>

            {/* Reminders Section - Integrated */}
            <CollapsibleSection title="Reminders" icon={Clock}>
                 <div className="flex justify-between items-center mb-1"> <p className="text-xs italic">Upcoming active reminders.</p> <button onClick={() => fetchReminders(true)} disabled={isLoadingReminders} title="Refresh Reminders" className="p-1 text-gray-400 hover:text-white disabled:opacity-50"> {isLoadingReminders ? <Loader2 size={14} className="animate-spin"/> : <RefreshCw size={14} />} </button> </div>
                 {isLoadingReminders && <p className="text-xs text-center">Loading reminders...</p>}
                 {remindersError && <p className="text-xs text-red-400">{remindersError}</p>}
                 {!isLoadingReminders && !remindersError && ( reminders.length > 0 ? ( <ul className="list-disc pl-4 mt-1 text-xs space-y-1 max-h-40 overflow-y-auto"> {reminders.map(reminder => ( <li key={reminder.id} title={`${new Date(reminder.remind_at).toLocaleString()} - ${reminder.content}`}> <span className="font-medium">{new Date(reminder.remind_at).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}:</span>{' '} {reminder.content.substring(0, 30)}{reminder.content.length > 30 ? '...' : ''} </li> ))} </ul> ) : ( <p className="text-xs text-gray-400 italic">No active reminders found.</p> ) )}
                 <button className="w-full mt-2 p-1.5 bg-gray-600 rounded hover:bg-gray-500 text-xs transition-colors duration-200">Manage Reminders</button>
            </CollapsibleSection>

            {/* Spending Section - Integrated */}
            <CollapsibleSection title="Daily Spending" icon={Wallet}>
                 <div className="flex justify-between items-center mb-1"> <p className="text-xs italic">Today's spending.</p> <button onClick={() => fetchSpendingLogs()} disabled={isLoadingSpending} title="Refresh Spending" className="p-1 text-gray-400 hover:text-white disabled:opacity-50"> {isLoadingSpending ? <Loader2 size={14} className="animate-spin"/> : <RefreshCw size={14} />} </button> </div>
                  <p className="font-medium text-sm mb-1"> Today: {isLoadingSpending ? '...' : spendingTotal !== null ? `$${spendingTotal.toFixed(2)}` : '$--.--'} </p>
                 {isLoadingSpending && <p className="text-xs text-center">Loading spending...</p>}
                 {spendingError && <p className="text-xs text-red-400">{spendingError}</p>}
                 {!isLoadingSpending && !spendingError && ( spendingLogs.length > 0 ? ( <ul className="list-disc pl-4 mt-1 text-xs space-y-1 max-h-40 overflow-y-auto"> {spendingLogs.map(log => ( <li key={log.id} title={`${log.description} - $${log.amount.toFixed(2)}`}> {log.description.substring(0, 25)}{log.description.length > 25 ? '...' : ''}: <span className="font-medium">${log.amount.toFixed(2)}</span> </li> ))} </ul> ) : ( <p className="text-xs text-gray-400 italic">No spending logged today.</p> ) )}
                 <button className="w-full mt-2 p-1.5 bg-gray-600 rounded hover:bg-gray-500 text-xs transition-colors duration-200">View Full Log</button>
            </CollapsibleSection>

            {/* Investment Section - Integrated (Basic Display) */}
            <CollapsibleSection title="Investment Details" icon={TrendingUp}>
                 <div className="flex justify-between items-center mb-1">
                     <p className="text-xs italic">Recent investment notes.</p>
                     <button onClick={fetchInvestmentNotes} disabled={isLoadingInvestmentNotes} title="Refresh Investment Notes" className="p-1 text-gray-400 hover:text-white disabled:opacity-50">
                        {isLoadingInvestmentNotes ? <Loader2 size={14} className="animate-spin"/> : <RefreshCw size={14} />}
                     </button>
                 </div>
                 {isLoadingInvestmentNotes && <p className="text-xs text-center">Loading notes...</p>}
                 {investmentNotesError && <p className="text-xs text-red-400">{investmentNotesError}</p>}
                 {!isLoadingInvestmentNotes && !investmentNotesError && (
                    investmentNotes.length > 0 ? (
                        // Basic display: Show count or list first few titles/content snippets
                        <ul className="list-disc pl-4 mt-1 text-xs space-y-1 max-h-40 overflow-y-auto">
                            {investmentNotes.slice(0, 5).map(note => ( // Show first 5
                                <li key={note.id} title={note.content}>
                                    {note.title ? `${note.title.substring(0,30)}...` : note.content.substring(0, 30)}{note.content.length > 30 ? '...' : ''}
                                </li>
                            ))}
                            {investmentNotes.length > 5 && <li className="italic text-gray-400">... and more</li>}
                        </ul>
                        // <p className="text-xs">{investmentNotes.length} investment note(s) loaded.</p>
                    ) : (
                         <p className="text-xs text-gray-400 italic">No investment notes found.</p>
                    )
                 )}
                 <button className="w-full mt-2 p-1.5 bg-gray-600 rounded hover:bg-gray-500 text-xs transition-colors duration-200">View Investment Notes</button>
            </CollapsibleSection>

            {/* Medical Section - Integrated (Basic Display) */}
            <CollapsibleSection title="Medical Details" icon={HeartPulse}>
                 <div className="flex justify-between items-center mb-1">
                     <p className="text-xs italic">Recent medical logs.</p>
                     <button onClick={fetchMedicalLogs} disabled={isLoadingMedicalLogs} title="Refresh Medical Logs" className="p-1 text-gray-400 hover:text-white disabled:opacity-50">
                        {isLoadingMedicalLogs ? <Loader2 size={14} className="animate-spin"/> : <RefreshCw size={14} />}
                     </button>
                 </div>
                  {isLoadingMedicalLogs && <p className="text-xs text-center">Loading logs...</p>}
                 {medicalLogsError && <p className="text-xs text-red-400">{medicalLogsError}</p>}
                 {!isLoadingMedicalLogs && !medicalLogsError && (
                    medicalLogs.length > 0 ? (
                        // Basic display: Show count or list first few log types/content snippets
                         <ul className="list-disc pl-4 mt-1 text-xs space-y-1 max-h-40 overflow-y-auto">
                            {medicalLogs.slice(0, 5).map(log => ( // Show first 5
                                <li key={log.id} title={log.content}>
                                    <span className="font-medium">{log.log_type}:</span> {log.content.substring(0, 30)}{log.content.length > 30 ? '...' : ''}
                                </li>
                            ))}
                            {medicalLogs.length > 5 && <li className="italic text-gray-400">... and more</li>}
                        </ul>
                        // <p className="text-xs">{medicalLogs.length} medical log(s) loaded.</p>
                    ) : (
                         <p className="text-xs text-gray-400 italic">No medical logs found.</p>
                    )
                 )}
                 <button className="w-full mt-2 p-1.5 bg-gray-600 rounded hover:bg-gray-500 text-xs transition-colors duration-200">View Medical Log</button>
            </CollapsibleSection>

            <div className="flex-grow"></div>

            {/* Settings, Profile, Logout */}
            <div className="mt-auto border-t border-gray-700 pt-3 space-y-1">
               <button onClick={toggleTheme} className="flex items-center w-full p-2 rounded hover:bg-gray-700 text-left transition-colors duration-200"> {isDarkMode ? <Sun size={18} className="mr-3" /> : <Moon size={18} className="mr-3" />} {isDarkMode ? "Light Mode" : "Dark Mode"} </button>
               <button type="button" onClick={() => console.log("Settings Clicked (TODO)")} className="flex items-center w-full p-2 rounded hover:bg-gray-700 text-left transition-colors duration-200"> <Settings size={18} className="mr-3" /> Settings </button>
               
               {/* --- Updated Profile Button --- */}
               <button
                    type="button"
                    onClick={() => setIsProfileModalOpen(true)} // Open the modal
                    className="flex items-center w-full p-2 rounded hover:bg-gray-700 text-left transition-colors duration-200"
                >
                    <User size={18} className="mr-3" /> Profile
                    {/* Optionally display name: {currentUser?.full_name || currentUser?.email} */}
               </button>
               {/* --- End Updated Profile Button --- */}

               <button onClick={handleLogout} className="flex items-center w-full p-2 rounded hover:bg-red-800 hover:bg-opacity-80 text-left transition-colors duration-200 text-red-300"> <LogOut size={18} className="mr-3" /> Logout </button>
            </div>
        </aside>

        {/* Main Chat Area */}
        <main className="flex-1 flex flex-col h-screen">
            <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-4 shadow-sm flex items-center justify-between flex-shrink-0"> <div className="flex items-center"> <button onClick={() => setIsSidebarOpen(!isSidebarOpen)} className="mr-4 p-2 rounded md:hidden hover:bg-gray-200 dark:hover:bg-gray-700 focus:outline-none" aria-label="Toggle sidebar"> <Menu size={20} /> </button> <h1 className="text-xl font-semibold text-gray-700 dark:text-gray-200">Aura Assistant</h1> </div> </header>
            {/* Conversation Area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-white dark:bg-gray-800"> {log.length === 0 && isAuthenticated && ( <div className="text-center text-gray-500 dark:text-gray-400 mt-10"> Welcome! How can I help you today? </div> )} {log.map((entry, index) => ( <div key={index} className={`flex ${entry.type === 'user' ? 'justify-end' : 'justify-start'}`}> <div className={`flex items-start max-w-xl lg:max-w-2xl ${entry.type === 'user' ? 'flex-row-reverse' : ''}`}> <div className={`flex-shrink-0 h-8 w-8 rounded-full flex items-center justify-center text-white ${entry.type === 'user' ? 'bg-blue-500 ml-2' : 'bg-indigo-500 mr-2'}`}> {entry.type === 'user' ? <User size={18} /> : <Bot size={18} />} </div> <div className={`px-4 py-2 rounded-lg shadow-md ${entry.type === 'user' ? 'bg-blue-500 text-white' : entry.isError ? 'bg-red-100 dark:bg-red-900 dark:bg-opacity-30 text-red-700 dark:text-red-300 border border-red-300 dark:border-red-700' : 'bg-gray-200 text-gray-800 dark:bg-gray-700 dark:text-gray-200'}`}> <p className="whitespace-pre-wrap">{entry.text}</p> </div> </div> </div> ))} <div ref={logEndRef} /> </div>
            {/* Loading Indicator */}
            {isLoading && ( <div className="px-4 pb-2 flex items-center justify-center text-gray-500 dark:text-gray-400 flex-shrink-0"> <Loader2 size={18} className="animate-spin mr-2" /> <span>Aura is thinking...</span> </div> )}
            {/* Input Area */}
            <div className="bg-gray-50 dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700 p-4 flex-shrink-0"> <div className="flex items-center bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg shadow-sm px-2 py-1 focus-within:ring-2 focus-within:ring-blue-500"> <textarea rows="1" value={inputText} onChange={(e) => { setInputText(e.target.value); e.target.style.height = 'auto'; e.target.style.height = `${e.target.scrollHeight}px`; }} onKeyPress={handleKeyPress} placeholder="Type your command or note... (Shift+Enter for newline)" className="flex-grow p-2 border-none focus:ring-0 resize-none overflow-y-auto text-sm bg-transparent dark:text-gray-200 placeholder-gray-400 dark:placeholder-gray-500" style={{ maxHeight: '120px' }} disabled={isLoading || isListening} /> <button onClick={handleVoiceInput} className={`ml-2 p-2 rounded-full hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-300 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-indigo-500 transition-colors duration-200 ${isListening ? 'text-red-500 animate-pulse' : ''}`} disabled={isLoading} title="Voice Input (Placeholder)"> <Mic size={20} /> </button> <button onClick={() => handleSend()} className="ml-2 p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200" disabled={isLoading || !inputText.trim()} aria-label="Send message"> <Send size={20} /> </button> </div> </div>
        </main>
        {/* Render Profile Modal Conditionally */}
        <ProfileModal
            isOpen={isProfileModalOpen}
            onClose={() => setIsProfileModalOpen(false)}
            currentUser={currentUser}
            refreshUser={fetchCurrentUser} // Pass function to refresh user data after update
        />
      </div>
    </div>
  );
}

export default App;