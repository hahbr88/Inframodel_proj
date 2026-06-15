import { apiClient } from './client';

export interface AdminLoginRequest {
  username: string;
  password: string;
}

export async function adminLogin(payload: AdminLoginRequest) {
  const response = await apiClient.post('/api/admin/auth/login', payload);
  return response.data;
}

export async function adminLogout() {
  const response = await apiClient.post('/api/admin/auth/logout');
  return response.data;
}

export async function getAdminSession() {
  const response = await apiClient.get('/api/admin/session');
  return response.data;
}
