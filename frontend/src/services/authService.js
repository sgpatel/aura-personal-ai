import apiClient from './apiClient';

const authService = {
    register: async (userData) => {
        const response = await apiClient.post('/register', userData);
        return response.data;
    },

    login: async (credentials) => {
        const response = await apiClient.post('/token', credentials);
        return response.data;
    },

    logout: async () => {
        // Implement logout logic if needed (e.g., clearing tokens)
    },

    getCurrentUser: async () => {
        const response = await apiClient.get('/users/me');
        return response.data;
    }
};

export default authService;