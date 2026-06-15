import axios, { AxiosError } from 'axios';

const defaultApiBaseUrl = window.location.origin;

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || defaultApiBaseUrl,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

interface ApiErrorBody {
  detail?: string;
  message?: string;
}

export function getApiErrorMessage(
  error: unknown,
  fallback = '요청을 처리하지 못했습니다.',
) {
  if (!axios.isAxiosError(error)) return fallback;
  const axiosError = error as AxiosError<ApiErrorBody>;
  return (
    axiosError.response?.data?.detail ??
    axiosError.response?.data?.message ??
    fallback
  );
}
