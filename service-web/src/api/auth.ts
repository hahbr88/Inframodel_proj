import { apiClient } from './client';
import type { CommandResponse, LoginRequest } from '../types/auth';

export async function login(payload: LoginRequest) {
  const response = await apiClient.post<CommandResponse>(
    '/api/auth/login',
    payload,
  );
  return response.data;
}

export async function logout() {
  const response = await apiClient.post<CommandResponse>('/api/auth/logout');
  return response.data;
}
