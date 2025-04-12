import React from 'react';
import { BrowserRouter as Router, Route, Switch } from 'react-router-dom';
import AuthProvider from './contexts/AuthContext';
import ThemeProvider from './contexts/ThemeContext';
import Header from './components/layout/Header';
import Sidebar from './components/layout/Sidebar';
import Home from './components/features/Home';
import Notes from './components/features/Notes';
import Reminders from './components/features/Reminders';
import NotFound from './components/common/NotFound';

const App = () => {
    return (
        <AuthProvider>
            <ThemeProvider>
                <Router>
                    <Header />
                    <Sidebar />
                    <main>
                        <Switch>
                            <Route path="/" exact component={Home} />
                            <Route path="/notes" component={Notes} />
                            <Route path="/reminders" component={Reminders} />
                            <Route component={NotFound} />
                        </Switch>
                    </main>
                </Router>
            </ThemeProvider>
        </AuthProvider>
    );
};

export default App;