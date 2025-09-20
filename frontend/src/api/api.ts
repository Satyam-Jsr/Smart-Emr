import axios from 'axios';

const API = axios.create({
  baseURL: 'http://localhost:8002',
  timeout: 30000, // Increased to 30 seconds for Q&A responses
});

export default API;
