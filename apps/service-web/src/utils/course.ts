import type { Course } from '../types/course';

export const LOCATION_OPTIONS = [
  '서울특별시',
  '부산광역시',
  '대구광역시',
  '인천광역시',
  '광주광역시',
  '대전광역시',
  '울산광역시',
  '세종특별자치시',
  '경기도',
  '강원특별자치도',
  '충청북도',
  '충청남도',
  '전북특별자치도',
  '전라남도',
  '경상북도',
  '경상남도',
  '제주특별자치도',
];

export const THEME_OPTIONS = [
  '문화/예술',
  '자연/힐링',
  '도시/관광',
  '체험/학습/산업',
  '레저/스포츠',
  '쇼핑/놀이',
  '역사/유적',
  '음식',
];

export function getCourseImage(course: Pick<Course, 'themes' | 'location'>) {
  const themes = course.themes.join(' ');
  if (/자연|힐링|생태/.test(themes)) return '/images/nature.svg';
  if (/체험|학습|산업|레저|스포츠/.test(themes)) {
    return '/images/experience.svg';
  }
  if (/도시|쇼핑|놀이/.test(themes) || /서울|부산|인천/.test(course.location)) {
    return '/images/city.svg';
  }
  return '/images/culture.svg';
}

export function skyLabel(code: number) {
  if (code <= 1) return '맑음';
  if (code <= 3) return '구름 많음';
  return '흐림';
}

export function climateColor(grade: string) {
  if (grade.includes('매우 좋')) return 'teal';
  if (grade.includes('좋')) return 'green';
  if (grade.includes('보통')) return 'yellow';
  return 'orange';
}
