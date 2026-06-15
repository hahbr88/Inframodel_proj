import type {
  AdminCourseListResponse,
  AdminDashboard,
  AdminReservationListResponse,
} from '../types/admin';
import { apiClient } from './client';

export async function getDashboard() {
  const response = await apiClient.get<AdminDashboard>('/api/admin/dashboard');
  return response.data;
}

export async function getAdminReservations() {
  const response = await apiClient.get<AdminReservationListResponse>(
    '/api/admin/reservations',
  );
  return response.data;
}

export async function updateAdminReservation(
  reservationId: number,
  reservationDate: string,
) {
  const response = await apiClient.patch(
    `/api/admin/reservations/${reservationId}`,
    { reservation_date: reservationDate },
  );
  return response.data;
}

export async function cancelAdminReservation(reservationId: number) {
  const response = await apiClient.delete(
    `/api/admin/reservations/${reservationId}`,
  );
  return response.data;
}

export async function getAdminCourses(keyword?: string) {
  const response = await apiClient.get<AdminCourseListResponse>(
    '/api/admin/courses',
    {
      params: {
        limit: 100,
        keyword: keyword?.trim() || undefined,
      },
    },
  );
  return response.data;
}
