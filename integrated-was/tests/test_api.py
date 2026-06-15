from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from app.core.config import settings
from main import app


def test_health_check() -> None:
    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["data_mode"] == "mock"


def test_local_frontend_origin_is_allowed() -> None:
    with TestClient(app) as client:
        response = client.options(
            "/api/course-catalog",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            },
        )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert response.headers["access-control-allow-credentials"] == "true"


def test_private_network_frontend_origin_is_allowed() -> None:
    with TestClient(app) as client:
        response = client.options(
            "/api/course-catalog",
            headers={
                "Origin": "http://192.168.51.70:5173",
                "Access-Control-Request-Method": "GET",
            },
        )

    assert response.status_code == 200
    assert (
        response.headers["access-control-allow-origin"] == "http://192.168.51.70:5173"
    )
    assert response.headers["access-control-allow-credentials"] == "true"


def test_local_admin_frontend_origin_is_allowed() -> None:
    with TestClient(app) as client:
        response = client.options(
            "/api/admin/dashboard",
            headers={
                "Origin": "http://localhost:5174",
                "Access-Control-Request-Method": "GET",
            },
        )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5174"
    assert response.headers["access-control-allow-credentials"] == "true"


def test_admin_api_requires_separate_admin_authentication() -> None:
    with TestClient(app) as client:
        client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "password123"},
        )
        response = client.get("/api/admin/dashboard")

    assert response.status_code == 401


def test_admin_login_dashboard_reservations_and_courses() -> None:
    with TestClient(app) as client:
        login_response = client.post(
            "/api/admin/auth/login",
            json={"username": "admin", "password": "password123"},
        )
        session_response = client.get("/api/admin/session")
        dashboard_response = client.get("/api/admin/dashboard")
        reservations_response = client.get("/api/admin/reservations")
        courses_response = client.get("/api/admin/courses", params={"limit": 2})

    assert login_response.status_code == 200
    assert "admin_access_token" in login_response.cookies
    assert session_response.status_code == 200
    assert session_response.json()["role"] == "ADMIN"
    assert dashboard_response.status_code == 200
    assert dashboard_response.json()["course_count"] == 434
    assert reservations_response.status_code == 200
    assert courses_response.status_code == 200
    assert courses_response.json()["count"] == 2


def test_login_create_and_list_reservation() -> None:
    with TestClient(app) as client:
        login_response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "password123"},
        )
        create_response = client.post(
            "/api/reservations",
            json={
                "course_id": 1,
                "reservation_date": (datetime.now() + timedelta(days=1)).isoformat(),
            },
        )
        list_response = client.get("/api/reservations")

    assert login_response.status_code == 200
    assert "access_token" in login_response.cookies
    assert create_response.status_code == 201
    assert list_response.status_code == 200
    assert list_response.json()["count"] >= 1


def test_reservation_date_can_be_updated() -> None:
    updated_date = datetime.now() + timedelta(days=3)

    with TestClient(app) as client:
        client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "password123"},
        )
        create_response = client.post(
            "/api/reservations",
            json={
                "course_id": 1,
                "reservation_date": (datetime.now() + timedelta(days=1)).isoformat(),
            },
        )
        reservation_id = create_response.json()["reservation_id"]
        update_response = client.patch(
            f"/api/reservations/{reservation_id}",
            json={"reservation_date": updated_date.isoformat()},
        )
        list_response = client.get("/api/reservations")

    updated = next(
        item
        for item in list_response.json()["reservations"]
        if item["id"] == reservation_id
    )
    assert update_response.status_code == 200
    assert datetime.fromisoformat(updated["reservation_date"]) == updated_date


def test_cancelled_reservation_is_removed_from_my_reservations() -> None:
    with TestClient(app) as client:
        client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "password123"},
        )
        create_response = client.post(
            "/api/reservations",
            json={
                "course_id": 1,
                "reservation_date": (datetime.now() + timedelta(days=2)).isoformat(),
            },
        )
        reservation_id = create_response.json()["reservation_id"]
        cancel_response = client.delete(f"/api/reservations/{reservation_id}")
        list_response = client.get("/api/reservations")

    reservation_ids = {item["id"] for item in list_response.json()["reservations"]}
    assert cancel_response.status_code == 200
    assert reservation_id not in reservation_ids


def test_past_reservation_date_is_rejected() -> None:
    with TestClient(app) as client:
        client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "password123"},
        )
        response = client.post(
            "/api/reservations",
            json={
                "course_id": 1,
                "reservation_date": (datetime.now() - timedelta(days=1)).isoformat(),
            },
        )

    assert response.status_code == 422


def test_demo_account_is_available_without_database() -> None:
    assert settings.data_mode == "mock"

    with TestClient(app) as client:
        response = client.post(
            "/api/auth/login",
            json={
                "username": settings.demo_username,
                "password": settings.demo_password,
            },
        )

    assert response.status_code == 200
    assert response.json()["message"] == "Login succeeded"
    assert "access_token" in response.cookies


def test_unknown_course_is_rejected() -> None:
    with TestClient(app) as client:
        client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "password123"},
        )
        response = client.post(
            "/api/reservations",
            json={
                "course_id": 99999,
                "reservation_date": datetime.now().isoformat(),
            },
        )

    assert response.status_code == 404


def test_reservation_requires_authentication() -> None:
    with TestClient(app) as client:
        response = client.get("/api/reservations")

    assert response.status_code == 401


def test_mock_weather_does_not_require_kma_key() -> None:
    with TestClient(app) as client:
        response = client.get("/api/courses/1/weather")

    assert response.status_code == 200
    body = response.json()
    assert body["course_id"] == 1
    assert body["source_apis"] == [
        "getTourStnVilageFcst1",
        "getCityTourClmIdx1",
    ]
    assert body["forecast_count"] == 2
    assert body["forecasts"][0]["temperature"] == 24.2
    assert body["forecasts"][0]["themes"] == ["문화/예술", "자연/힐링"]
    assert body["tourist_index"]["grade"] == "좋음"


def test_two_kma_operations_can_be_queried_separately() -> None:
    with TestClient(app) as client:
        forecast_response = client.get("/api/courses/1/village-forecast")
        climate_response = client.get("/api/courses/1/climate-index")

    assert forecast_response.status_code == 200
    assert forecast_response.json()["source_api"] == "getTourStnVilageFcst1"
    assert forecast_response.json()["count"] == 2
    assert climate_response.status_code == 200
    assert climate_response.json()["source_api"] == "getCityTourClmIdx1"


def test_course_catalog_combines_course_weather_and_reservations() -> None:
    with TestClient(app) as client:
        response = client.get(
            "/api/course-catalog",
            params={
                "include_spots": "true",
                "include_forecasts": "true",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 20
    assert body["total_count"] == 434
    assert body["next_cursor"] == 20
    assert body["has_next"] is True

    first_course = next(course for course in body["courses"] if course["id"] == 1)
    assert first_course["name"] == "남호고택에서의 하룻밤"
    assert first_course["weather"]["forecast_at"] == "2026-06-10 18:00"
    assert first_course["weather"]["spot_count"] == 1
    assert first_course["weather"]["themes"] == [
        "문화/예술",
        "자연/힐링",
    ]
    assert first_course["tourist_index"]["grade"] == "좋음"
    assert first_course["active_reservation_count"] >= 1
    assert first_course["weather_available"] is True
    assert first_course["reservation_enabled"] is True
    assert first_course["spot_count"] == 4
    assert len(first_course["spots"]) == 4
    assert len(first_course["forecasts"]) == 2

    course_without_mock_weather = next(
        course for course in body["courses"] if course["id"] == 2
    )
    assert course_without_mock_weather["weather"] is None
    assert course_without_mock_weather["weather_available"] is False
    assert course_without_mock_weather["reservation_enabled"] is True


def test_course_catalog_can_exclude_full_forecasts() -> None:
    with TestClient(app) as client:
        response = client.get(
            "/api/course-catalog",
            params={"include_forecasts": "false"},
        )

    assert response.status_code == 200
    first_course = next(
        course for course in response.json()["courses"] if course["id"] == 1
    )
    assert first_course["forecasts"] == []
    assert first_course["spots"] == []


def test_course_catalog_supports_cursor_pagination() -> None:
    with TestClient(app) as client:
        first_response = client.get(
            "/api/course-catalog",
            params={"limit": 2},
        )
        second_response = client.get(
            "/api/course-catalog",
            params={
                "limit": 2,
                "cursor": first_response.json()["next_cursor"],
            },
        )

    assert first_response.status_code == 200
    assert [item["id"] for item in first_response.json()["courses"]] == [1, 2]
    assert [item["id"] for item in second_response.json()["courses"]] == [3, 4]


def test_course_catalog_supports_keyword_search() -> None:
    with TestClient(app) as client:
        response = client.get(
            "/api/course-catalog",
            params={"keyword": "홍대"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["total_count"] >= 1
    assert any("홍대" in item["name"] for item in body["courses"])


def test_course_catalog_supports_location_and_theme_filters() -> None:
    with TestClient(app) as client:
        response = client.get(
            "/api/course-catalog",
            params={
                "location": "서울특별시",
                "theme": "문화/예술",
                "limit": 100,
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["total_count"] >= 1
    assert all(
        item["location"] == "서울특별시" and "문화/예술" in item["themes"]
        for item in body["courses"]
    )


def test_course_detail_combines_spots_weather_and_reservations() -> None:
    with TestClient(app) as client:
        response = client.get("/api/courses/1")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == 1
    assert body["spot_count"] == 4
    assert len(body["spots"]) == 4
    assert len(body["forecasts"]) == 2
    assert body["weather_available"] is True
    assert body["active_reservation_count"] >= 1
    assert body["forecast_time"]


def test_unknown_course_detail_returns_not_found() -> None:
    with TestClient(app) as client:
        response = client.get("/api/courses/99999")

    assert response.status_code == 404


def test_course_list_is_loaded_from_kma_reference_csv() -> None:
    with TestClient(app) as client:
        response = client.get("/api/courses")

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 434
    assert body["courses"][0]["id"] == 1
    assert body["courses"][0]["city_area_id"] == "4792000000"
    assert body["courses"][0]["spot_count"] == 4
    assert len(body["courses"][0]["spots"]) == 4


def test_database_mode_repository_wiring(monkeypatch) -> None:
    monkeypatch.setattr(settings, "data_mode", "database")

    with TestClient(app) as client:
        login_response = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "password123"},
        )
        courses_response = client.get("/api/courses")

    assert login_response.status_code == 200
    assert courses_response.status_code == 200
    assert courses_response.json()["count"] == 434
