import axios from 'axios';

// API base URL (will use proxy in development, direct in production)
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const demoAPI = {
  // Create demo session
  createDemoSession: async (phone, language, voice, greeting, prompt) => {
    const response = await apiClient.post('/demo/session', {
      phone,
      language,
      voice,
      greeting,
      prompt,
    });
    return response.data;
  },

  // Get demo session status
  getDemoSessionStatus: async (sessionId) => {
    const response = await apiClient.get(`/demo/session/${sessionId}`);
    return response.data;
  },

  // Get demo session analytics (transcript, analysis, follow-up)
  getDemoAnalytics: async (sessionId) => {
    const response = await apiClient.get(`/demo/analytics/${sessionId}`);
    return response.data;
  },

  // Get analytics
  getAnalytics: async () => {
    const response = await apiClient.get('/demo/analytics');
    return response.data;
  },

  // Get all interactions
  getInteractions: async () => {
    const response = await apiClient.get('/demo/interactions');
    return response.data;
  },

  // Get interaction detail
  getInteractionDetail: async (interactionId) => {
    const response = await apiClient.get(`/demo/interaction/${interactionId}`);
    return response.data;
  },
};

export default apiClient;
