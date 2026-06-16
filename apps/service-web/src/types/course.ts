export interface CourseSpot {
  id: number;
  name: string;
  longitude: number;
  latitude: number;
  sequence: number;
  travel_time: number;
  indoor_type: string;
  theme: string;
}

export interface WeatherDetail {
  forecast_at: string;
  themes: string[];
  spot_area_id: number;
  spot_area_name: string;
  spot_name: string;
  temperature: number;
  wind_direction: number;
  wind_speed: number;
  sky: number;
  humidity: number;
  rain_probability: number;
}

export interface TouristIndex {
  score: number;
  grade: string;
}

export interface CourseWeatherSummary {
  forecast_at: string;
  min_temperature: number;
  max_temperature: number;
  max_rain_probability: number;
  average_humidity: number;
  worst_sky: number;
  spot_count: number;
  themes: string[];
}

export interface Course {
  id: number;
  name: string;
  location: string;
  kma_course_id: number;
  spot_count: number;
  themes: string[];
  spots: CourseSpot[];
  weather: CourseWeatherSummary | null;
  forecasts: WeatherDetail[];
  weather_available: boolean;
  tourist_index: TouristIndex | null;
  active_reservation_count: number;
  reservation_enabled: boolean;
}

export interface CourseCatalogResponse {
  status: string;
  forecast_time: string;
  count: number;
  total_count: number;
  next_cursor: number | null;
  has_next: boolean;
  courses: Course[];
}

export interface CourseDetail extends Course {
  status: string;
  forecast_time: string;
}

export interface CourseCatalogParams {
  keyword: string;
  location: string | null;
  theme: string | null;
}
