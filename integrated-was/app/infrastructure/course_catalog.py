import csv
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

COURSE_SPOTS_PATH = Path(__file__).parent.parent / "data" / "tour_course_spots.csv"

REGION_NAMES = {
    "11": "서울특별시",
    "26": "부산광역시",
    "27": "대구광역시",
    "28": "인천광역시",
    "29": "광주광역시",
    "30": "대전광역시",
    "31": "울산광역시",
    "36": "세종특별자치시",
    "41": "경기도",
    "42": "강원특별자치도",
    "43": "충청북도",
    "44": "충청남도",
    "45": "전북특별자치도",
    "46": "전라남도",
    "47": "경상북도",
    "48": "경상남도",
    "50": "제주특별자치도",
}

CITY_AREA_ID_ALIASES = {
    # API reference uses consolidated or current municipality codes.
    "4127300000": "4127100000",  # Ansan
    "4511300000": "4511100000",  # Jeonju
    "4711300000": "4711100000",  # Pohang
    "4772000000": "2772000000",  # Gunwi (Gyeongbuk -> Daegu)
    "4812500000": "4812100000",  # Former Masan -> Changwon
    "4812900000": "4812100000",  # Former Jinhae -> Changwon
}


@dataclass(frozen=True)
class CourseSpot:
    id: int
    area_id: str
    name: str
    longitude: float
    latitude: float
    sequence: int
    travel_time: int
    indoor_type: str
    theme: str


@dataclass
class CatalogCourse:
    id: int
    name: str
    location: str
    kma_course_id: int
    city_area_id: str = ""
    spots: list[CourseSpot] = field(default_factory=list)

    @property
    def spot_count(self) -> int:
        return len(self.spots)

    @property
    def themes(self) -> list[str]:
        return sorted({spot.theme for spot in self.spots})


def load_course_catalog(
    path: Path = COURSE_SPOTS_PATH,
) -> dict[int, CatalogCourse]:
    grouped: dict[int, list[CourseSpot]] = {}
    with path.open(encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            course_id = int(row["코스 아이디"])
            grouped.setdefault(course_id, []).append(
                CourseSpot(
                    id=int(row["관광지 아이디"]),
                    area_id=row["지역 아이디"],
                    name=row["관광지명"],
                    longitude=float(row["경도(도)"]),
                    latitude=float(row["위도(도)"]),
                    sequence=int(row["코스순서"]),
                    travel_time=int(row["이동시간"]),
                    indoor_type=row["실내구분"],
                    theme=row["테마명"],
                )
            )

    courses: dict[int, CatalogCourse] = {}
    for course_id, spots in grouped.items():
        spots.sort(key=lambda spot: (spot.sequence, spot.id))
        courses[course_id] = CatalogCourse(
            id=course_id,
            name=_derive_course_name(spots),
            location=_derive_location(spots),
            kma_course_id=course_id,
            city_area_id=_derive_city_area_id(spots),
            spots=spots,
        )
    return courses


def _derive_course_name(spots: list[CourseSpot]) -> str:
    names = [_strip_area_prefix(spot.name) for spot in spots]
    if len(names) == 1:
        return names[0]
    suffix = f" 외 {len(names) - 2}곳" if len(names) > 2 else ""
    return f"{names[0]} → {names[1]}{suffix}"


def _derive_location(spots: list[CourseSpot]) -> str:
    region_codes = [spot.area_id[:2] for spot in spots]
    region_code = Counter(region_codes).most_common(1)[0][0]
    return REGION_NAMES.get(region_code, "지역 정보 없음")


def _derive_city_area_id(spots: list[CourseSpot]) -> str:
    city_codes = [
        CITY_AREA_ID_ALIASES.get(
            f"{spot.area_id[:5]}00000",
            f"{spot.area_id[:5]}00000",
        )
        for spot in spots
    ]
    return Counter(city_codes).most_common(1)[0][0]


def _strip_area_prefix(name: str) -> str:
    return re.sub(r"^\([^)]*\)", "", name).strip()
