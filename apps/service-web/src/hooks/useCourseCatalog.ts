import { useInfiniteQuery } from '@tanstack/react-query';
import { getCourseCatalog } from '../api/courses';
import type { CourseCatalogParams } from '../types/course';

export function useCourseCatalog(params: CourseCatalogParams) {
  return useInfiniteQuery({
    queryKey: [
      'course-catalog',
      params.keyword,
      params.location,
      params.theme,
    ],
    queryFn: ({ pageParam }) =>
      getCourseCatalog({ ...params, cursor: pageParam }),
    initialPageParam: undefined as number | undefined,
    getNextPageParam: (lastPage) =>
      lastPage.has_next ? (lastPage.next_cursor ?? undefined) : undefined,
    staleTime: 30_000,
  });
}
