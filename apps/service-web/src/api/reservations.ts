import { apiClient } from './client';
import type {
  ReservationCreate,
  ReservationCreatedResponse,
  ReservationListResponse,
  ReservationUpdate,
} from '../types/reservation';

export async function getReservations() {
  const response = await apiClient.get<ReservationListResponse>(
    '/api/reservations',
  );
  return response.data;
}

export async function createReservation(payload: ReservationCreate) {
  const response = await apiClient.post<ReservationCreatedResponse>(
    '/api/reservations',
    payload,
  );
  return response.data;
}

export async function cancelReservation(reservationId: number) {
  const response = await apiClient.delete(
    `/api/reservations/${reservationId}`,
  );
  return response.data;
}

export async function updateReservation(
  reservationId: number,
  payload: ReservationUpdate,
) {
  const response = await apiClient.patch(
    `/api/reservations/${reservationId}`,
    payload,
  );
  return response.data;
}
