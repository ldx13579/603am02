import axios from 'axios';

const API_KEY = import.meta.env.VITE_API_KEY || 'changeme-secret-key';

const client = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': API_KEY,
  },
});

export default client;
