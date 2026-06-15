from app.infrastructure.course_catalog import load_course_catalog


def test_city_area_id_is_derived_from_spot_area_id() -> None:
    courses = load_course_catalog()

    assert courses[1].city_area_id == "4792000000"
    assert courses[52].city_area_id == "1144000000"


def test_legacy_city_area_ids_use_supported_kma_codes() -> None:
    courses = load_course_catalog()

    assert courses[253].city_area_id == "4127100000"
    assert courses[102].city_area_id == "4511100000"
    assert courses[124].city_area_id == "4711100000"
    assert courses[132].city_area_id == "2772000000"
    assert courses[196].city_area_id == "4812100000"
    assert courses[205].city_area_id == "4812100000"
