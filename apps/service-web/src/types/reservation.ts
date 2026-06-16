export interface Reservation {
  id: number;
  course_id: number;
  course_name: string;
  reservation_date: string;
  status: string;
}

export interface ReservationListResponse {
  status: string;
  count: number;
  reservations: Reservation[];
}

export interface ReservationCreate {
  course_id: number;
  reservation_date: string;
}

export interface ReservationUpdate {
  reservation_date: string;
}

export interface ReservationCreatedResponse {
  status: string;
  message: string;
  reservation_id: number;
}
