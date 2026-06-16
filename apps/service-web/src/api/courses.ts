import { apiClient } from './client';
import type {
  CourseCatalogParams,
  CourseCatalogResponse,
  CourseDetail,
} from '../types/course';

interface CatalogRequest extends CourseCatalogParams {
  cursor?: number;
  limit?: number;
}

export async function getCourseCatalog({
  cursor,
  limit = 20,
  keyword,
  location,
  theme,
}: CatalogRequest) {
  const response = await apiClient.get<CourseCatalogResponse>(
    '/api/course-catalog',
    {
      params: {
        limit,
        cursor,
        keyword: keyword.trim() || undefined,
        location: location || undefined,
        theme: theme || undefined,
      },
    },
  );
  return response.data;
}

export async function getCourseDetail(courseId: number) {
  const response = await apiClient.get<CourseDetail>(
    `/api/courses/${courseId}`,
  );
  return response.data;
}
