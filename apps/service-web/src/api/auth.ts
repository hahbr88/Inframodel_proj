import { apiClient } from './client';
import type {
  CommandResponse,
  LoginRequest,
  PasswordChangeRequest,
  SignupRequest,
} from '../types/auth';

export async function login(payload: LoginRequest) {
  const response = await apiClient.post<CommandResponse>(
    '/api/auth/login',
    payload,
  );
  return response.data;
}

export async function signup(payload: SignupRequest) {
  const response = await apiClient.post<CommandResponse>(
    '/api/auth/signup',
    payload,
  );
  return response.data;
}

export async function logout() {
  const response = await apiClient.post<CommandResponse>('/api/auth/logout');
  return response.data;
}

export async function changePassword(payload: PasswordChangeRequest) {
  const response = await apiClient.patch<CommandResponse>(
    '/api/auth/me/password',
    payload,
  );
  return response.data;
}

export async function deleteAccount(payload: LoginRequest) {
  const response = await apiClient.delete<CommandResponse>('/api/auth/me', {
    data: payload,
  });
  return response.data;
}
