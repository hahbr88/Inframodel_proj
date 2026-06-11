from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CourseSpotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    longitude: float
    latitude: float
    sequence: int
    travel_time: int
    indoor_type: str
    theme: str


class CourseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    location: str
    kma_course_id: int
    city_area_id: str
    spot_count: int = 0
    themes: list[str] = Field(default_factory=list)
    spots: list[CourseSpotResponse] = Field(default_factory=list)


class CourseListResponse(BaseModel):
    status: str = "success"
    count: int
    courses: list[CourseResponse]


class ReservationResponse(BaseModel):
    id: int
    course_id: int
    course_name: str
    reservation_date: datetime
    status: str


class ReservationListResponse(BaseModel):
    status: str = "success"
    count: int
    reservations: list[ReservationResponse]


class WeatherDetail(BaseModel):
    forecast_at: str
    themes: list[str]
    spot_area_id: int
    spot_area_name: str
    spot_name: str
    temperature: float
    wind_direction: int
    wind_speed: float
    sky: int
    humidity: int
    rain_probability: int


class TouristIndex(BaseModel):
    score: float
    grade: str


class CourseWeatherSummary(BaseModel):
    forecast_at: str
    min_temperature: float
    max_temperature: float
    max_rain_probability: int
    average_humidity: int
    worst_sky: int
    spot_count: int
    themes: list[str]


class CourseCatalogItem(BaseModel):
    id: int
    name: str
    location: str
    kma_course_id: int
    spot_count: int
    themes: list[str]
    spots: list[CourseSpotResponse]
    weather: CourseWeatherSummary | None
    forecasts: list[WeatherDetail] = Field(default_factory=list)
    weather_available: bool
    tourist_index: TouristIndex | None
    active_reservation_count: int
    reservation_enabled: bool


class CourseCatalogResponse(BaseModel):
    status: str = "success"
    forecast_time: str
    count: int
    total_count: int
    next_cursor: int | None = None
    has_next: bool
    courses: list[CourseCatalogItem]


class CourseDetailResponse(CourseCatalogItem):
    status: str = "success"
    forecast_time: str


class VillageForecastResponse(BaseModel):
    status: str = "success"
    source_api: str = "getTourStnVilageFcst1"
    course_id: int
    location: str
    forecast_time: str
    count: int
    forecasts: list[WeatherDetail]


class ClimateIndexResponse(BaseModel):
    status: str = "success"
    source_api: str = "getCityTourClmIdx1"
    course_id: int
    location: str
    forecast_time: str
    tourist_index: TouristIndex


class WeatherResponse(BaseModel):
    status: str = "success"
    source_apis: list[str] = Field(
        default_factory=lambda: [
            "getTourStnVilageFcst1",
            "getCityTourClmIdx1",
        ]
    )
    course_id: int
    location: str
    forecast_time: str
    forecast_count: int
    forecasts: list[WeatherDetail]
    tourist_index: TouristIndex | None = None
