export interface AdminDashboard {
  status: string;
  course_count: number;
  reservation_count: number;
  active_reservation_count: number;
  cancelled_reservation_count: number;
  upcoming_reservation_count: number;
}

export interface AdminReservation {
  id: number;
  course_id: number;
  course_name: string;
  reservation_date: string;
  status: string;
}

export interface AdminReservationListResponse {
  status: string;
  count: number;
  reservations: AdminReservation[];
}

export interface WeatherSummary {
  forecast_at: string;
  min_temperature: number;
  max_temperature: number;
  max_rain_probability: number;
  average_humidity: number;
}

export interface AdminCourse {
  id: number;
  name: string;
  location: string;
  spot_count: number;
  themes: string[];
  weather: WeatherSummary | null;
  weather_available: boolean;
  active_reservation_count: number;
  reservation_enabled: boolean;
}

export interface AdminCourseListResponse {
  status: string;
  forecast_time: string;
  count: number;
  total_count: number;
  next_cursor: number | null;
  has_next: boolean;
  courses: AdminCourse[];
}
