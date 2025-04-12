import apiClient from './apiClient';

const noteService = {
    getNotes: async () => {
        const response = await apiClient.get('/notes');
        return response.data;
    },

    getNoteById: async (id) => {
        const response = await apiClient.get(`/notes/${id}`);
        return response.data;
    },

    createNote: async (noteData) => {
        const response = await apiClient.post('/notes', noteData);
        return response.data;
    },

    updateNote: async (id, noteData) => {
        const response = await apiClient.put(`/notes/${id}`, noteData);
        return response.data;
    },

    deleteNote: async (id) => {
        const response = await apiClient.delete(`/notes/${id}`);
        return response.data;
    }
};

export default noteService;