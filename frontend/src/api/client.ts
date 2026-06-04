import axios from 'axios';
import type { AxiosInstance } from 'axios';

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

export interface User {
  id: number;
  email: string;
  created_at: string;
}

export interface Session {
  id: number;
  session_id?: string;
  status: string;
  container_name: string;
  created_at: string;
  last_activity: string;
  url: string;
}

export interface FileInfo {
  filename: string;
  size: number;
  modified_at: string;
}

/* ------------------------------------------------------------------ */
/*  Axios Instance                                                     */
/* ------------------------------------------------------------------ */

const baseURL = import.meta.env.VITE_API_URL || '';

const api: AxiosInstance = axios.create({
  baseURL,
  headers: { 'Content-Type': 'application/json' },
});

// ---- Request interceptor: attach JWT ----
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ---- Response interceptor: handle 401 ----
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      // Only redirect if not already on login/register
      const path = window.location.pathname;
      if (path !== '/login' && path !== '/register') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  },
);

/* ------------------------------------------------------------------ */
/*  Auth helpers                                                       */
/* ------------------------------------------------------------------ */

export async function login(email: string, password: string): Promise<AuthResponse> {
  const { data } = await api.post<AuthResponse>('/api/login', { email, password });
  return data;
}

export async function register(email: string, password: string): Promise<AuthResponse> {
  const { data } = await api.post<AuthResponse>('/api/register', { email, password });
  return data;
}

export async function getMe(): Promise<User> {
  const { data } = await api.get<User>('/api/me');
  return data;
}

/* ------------------------------------------------------------------ */
/*  Session helpers                                                    */
/* ------------------------------------------------------------------ */

export async function createSession(): Promise<Session> {
  const { data } = await api.post<Session>('/api/sessions');
  return data;
}

export async function getSessions(): Promise<Session[]> {
  const { data } = await api.get<Session[]>('/api/sessions');
  return data;
}

export async function getSession(id: number): Promise<Session> {
  const { data } = await api.get<Session>(`/api/sessions/${id}`);
  return data;
}

export async function deleteSession(id: number): Promise<void> {
  await api.delete(`/api/sessions/${id}`);
}

export async function heartbeatSession(id: number): Promise<void> {
  await api.post(`/api/sessions/${id}/heartbeat`);
}

/* ------------------------------------------------------------------ */
/*  File helpers                                                       */
/* ------------------------------------------------------------------ */

export async function getFiles(): Promise<FileInfo[]> {
  const { data } = await api.get<FileInfo[]>('/api/files');
  return data;
}

export async function uploadFile(
  file: File,
  onProgress?: (pct: number) => void,
): Promise<{ filename: string; size: number }> {
  const form = new FormData();
  form.append('file', file);
  const { data } = await api.post<{ filename: string; size: number }>(
    '/api/files/upload',
    form,
    {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (e) => {
        if (e.total && onProgress) {
          onProgress(Math.round((e.loaded * 100) / e.total));
        }
      },
    },
  );
  return data;
}

export async function downloadFile(filename: string): Promise<void> {
  const { data } = await api.get(`/api/files/download/${encodeURIComponent(filename)}`, {
    responseType: 'blob',
  });
  const url = window.URL.createObjectURL(data as Blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}

export async function deleteFile(filename: string): Promise<void> {
  await api.delete(`/api/files/${encodeURIComponent(filename)}`);
}

export default api;
