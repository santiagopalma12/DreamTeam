import axios from 'axios';

// Use Vite env var when available; fall back to localhost for local dev outside Docker
const BASE = import.meta?.env?.VITE_API_URL || 'http://localhost:8000';
const api = axios.create({ baseURL: BASE });

export const proposeTeam = async (params) => {
	const res = await api.post('/team/propose', params);
	return res.data;
};

export const getEmployees = async () => {
  const res = await api.get('/employees');
  return res.data?.employees ?? [];
};