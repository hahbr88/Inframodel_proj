import { useQuery } from '@tanstack/react-query';
import { getCourseDetail } from '../api/courses';

export function useCourseDetail(courseId: number | null) {
  return useQuery({
    queryKey: ['course-detail', courseId],
    queryFn: () => getCourseDetail(courseId as number),
    enabled: courseId !== null,
    staleTime: 30_000,
  });
}
