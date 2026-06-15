import {
  Badge,
  Container,
  Group,
  Loader,
  SimpleGrid,
  Stack,
  Text,
  Title,
} from '@mantine/core';
import { IconSparkles } from '@tabler/icons-react';
import { useEffect, useMemo, useRef, useState } from 'react';
import { CourseCard } from '../components/CourseCard';
import { CourseCardSkeleton } from '../components/CourseCardSkeleton';
import { CourseDetailDrawer } from '../components/CourseDetailDrawer';
import { CourseFilters } from '../components/CourseFilters';
import { CourseSearch } from '../components/CourseSearch';
import { EmptyState } from '../components/EmptyState';
import { useCourseCatalog } from '../hooks/useCourseCatalog';
import { useDebouncedValue } from '../hooks/useDebouncedValue';

export function CourseCatalogPage() {
  const [keyword, setKeyword] = useState('');
  const [location, setLocation] = useState<string | null>(null);
  const [theme, setTheme] = useState<string | null>(null);
  const [selectedCourseId, setSelectedCourseId] = useState<number | null>(null);
  const sentinelRef = useRef<HTMLDivElement | null>(null);
  const debouncedKeyword = useDebouncedValue(keyword, 400);

  const catalogQuery = useCourseCatalog({
    keyword: debouncedKeyword,
    location,
    theme,
  });
  const {
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = catalogQuery;

  const courses = useMemo(() => {
    const unique = new Map(
      catalogQuery.data?.pages
        .flatMap((page) => page.courses)
        .map((course) => [course.id, course]),
    );
    return [...unique.values()];
  }, [catalogQuery.data?.pages]);

  useEffect(() => {
    const sentinel = sentinelRef.current;
    if (!sentinel) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (
          entry.isIntersecting &&
          hasNextPage &&
          !isFetchingNextPage
        ) {
          fetchNextPage();
        }
      },
      { rootMargin: '320px 0px' },
    );

    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [fetchNextPage, hasNextPage, isFetchingNextPage]);

  const resetFilters = () => {
    setKeyword('');
    setLocation(null);
    setTheme(null);
  };

  const hasFilters = Boolean(keyword || location || theme);
  const totalCount = catalogQuery.data?.pages[0]?.total_count;

  return (
    <>
      <main>
        <section className="catalog-hero">
          <Container size="xl">
            <Badge
              variant="light"
              color="teal"
              size="lg"
              leftSection={<IconSparkles size={14} />}
            >
              날씨 기반 여행 큐레이션
            </Badge>
            <Title className="hero-title">
              좋은 날씨를 KEY로
              <br />
              새로운 여정을
            </Title>
            <Text className="hero-copy">
              전국의 관광 코스와 실시간 예보를 한눈에 확인하고
              <br className="desktop-break" /> 가장 좋은 순간을 예약하세요.
            </Text>
            <div className="search-panel">
              <CourseSearch value={keyword} onChange={setKeyword} />
              <CourseFilters
                location={location}
                theme={theme}
                onLocationChange={setLocation}
                onThemeChange={setTheme}
                onReset={resetFilters}
                hasFilters={hasFilters}
              />
            </div>
          </Container>
        </section>

        <Container size="xl" className="catalog-content">
          <Group justify="space-between" align="flex-end" mb="xl">
            <div>
              <Text c="teal.8" fw={800} size="sm" mb={5}>
                EXPLORE COURSES
              </Text>
              <Title order={2}>지금 떠나기 좋은 코스</Title>
            </div>
            {typeof totalCount === 'number' && (
              <Text c="dimmed" size="sm">
                총 <b>{totalCount.toLocaleString()}</b>개의 코스
              </Text>
            )}
          </Group>

          {catalogQuery.isPending ? (
            <SimpleGrid cols={{ base: 1, sm: 2, lg: 3 }} spacing="xl">
              {Array.from({ length: 6 }).map((_, index) => (
                <CourseCardSkeleton key={index} />
              ))}
            </SimpleGrid>
          ) : catalogQuery.isError ? (
            <EmptyState
              error
              title="코스를 불러오지 못했습니다"
              description="백엔드 서버 연결을 확인하고 다시 시도해 주세요."
              actionLabel="다시 시도"
              onAction={() => catalogQuery.refetch()}
            />
          ) : courses.length === 0 ? (
            <EmptyState
              title="조건에 맞는 코스가 없습니다"
              description="검색어나 필터를 변경하면 더 많은 여행지를 만날 수 있습니다."
              actionLabel="필터 초기화"
              onAction={resetFilters}
            />
          ) : (
            <>
              <SimpleGrid cols={{ base: 1, sm: 2, lg: 3 }} spacing="xl">
                {courses.map((course) => (
                  <CourseCard
                    key={course.id}
                    course={course}
                    onDetail={() => setSelectedCourseId(course.id)}
                    onReserve={() => setSelectedCourseId(course.id)}
                  />
                ))}
              </SimpleGrid>
              <Stack ref={sentinelRef} align="center" py={40} gap="xs">
                {catalogQuery.isFetchingNextPage ? (
                  <>
                    <Loader color="teal" size="sm" />
                    <Text size="sm" c="dimmed">
                      다음 코스를 불러오는 중입니다
                    </Text>
                  </>
                ) : catalogQuery.hasNextPage ? (
                  <Text size="sm" c="dimmed">
                    아래로 스크롤해 더 많은 코스를 확인하세요
                  </Text>
                ) : (
                  <Text size="sm" c="dimmed">
                    모든 코스를 확인했습니다
                  </Text>
                )}
              </Stack>
            </>
          )}
        </Container>
      </main>

      <CourseDetailDrawer
        courseId={selectedCourseId}
        opened={selectedCourseId !== null}
        onClose={() => setSelectedCourseId(null)}
      />
    </>
  );
}
