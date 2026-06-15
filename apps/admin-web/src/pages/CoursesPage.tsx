import {
  Alert,
  Badge,
  Group,
  Loader,
  Paper,
  Stack,
  Table,
  Text,
  TextInput,
} from '@mantine/core';
import { useDebouncedValue } from '@mantine/hooks';
import { useQuery } from '@tanstack/react-query';
import { IconSearch } from '@tabler/icons-react';
import { useState } from 'react';
import { getAdminCourses } from '../api/admin';
import { getApiErrorMessage } from '../api/client';
import { PageHeader } from '../components/PageHeader';

export function CoursesPage() {
  const [keyword, setKeyword] = useState('');
  const [debouncedKeyword] = useDebouncedValue(keyword, 300);
  const coursesQuery = useQuery({
    queryKey: ['admin-courses', debouncedKeyword],
    queryFn: () => getAdminCourses(debouncedKeyword),
  });

  return (
    <>
      <PageHeader
        eyebrow="Course operations"
        title="코스 현황"
        description="사용자 웹에 제공되는 코스, 날씨 데이터, 활성 예약 수를 확인합니다."
        action={
          <TextInput
            value={keyword}
            onChange={(event) => setKeyword(event.currentTarget.value)}
            placeholder="코스명, 지역, 테마 검색"
            leftSection={<IconSearch size={17} />}
          />
        }
      />

      {coursesQuery.isPending ? (
        <Stack align="center" py={100}>
          <Loader />
          <Text c="dimmed">코스와 날씨 현황을 불러오는 중입니다.</Text>
        </Stack>
      ) : coursesQuery.isError ? (
        <Alert color="red">{getApiErrorMessage(coursesQuery.error)}</Alert>
      ) : (
        <>
          <Group mb="md">
            <Badge variant="light" size="lg">
              검색 결과 {coursesQuery.data.total_count.toLocaleString()}개
            </Badge>
            <Text size="sm" c="dimmed">
              기준 예보 {coursesQuery.data.forecast_time}
            </Text>
          </Group>
          <Paper className="content-panel table-panel" radius="lg">
            <Table.ScrollContainer minWidth={900}>
              <Table
                verticalSpacing="md"
                horizontalSpacing="lg"
                highlightOnHover
              >
                <Table.Thead>
                  <Table.Tr>
                    <Table.Th>코스</Table.Th>
                    <Table.Th>지역</Table.Th>
                    <Table.Th>관광지</Table.Th>
                    <Table.Th>날씨</Table.Th>
                    <Table.Th>활성 예약</Table.Th>
                  </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                  {coursesQuery.data.courses.map((course) => (
                    <Table.Tr key={course.id}>
                      <Table.Td>
                        <Text fw={700}>{course.name}</Text>
                        <Text size="xs" c="dimmed">
                          #{course.id} · {course.themes.slice(0, 2).join(', ')}
                        </Text>
                      </Table.Td>
                      <Table.Td>{course.location}</Table.Td>
                      <Table.Td>{course.spot_count}개</Table.Td>
                      <Table.Td>
                        {course.weather ? (
                          <Stack gap={2}>
                            <Text size="sm" fw={700}>
                              {course.weather.min_temperature}-
                              {course.weather.max_temperature}°C
                            </Text>
                            <Text size="xs" c="dimmed">
                              강수 {course.weather.max_rain_probability}%
                            </Text>
                          </Stack>
                        ) : (
                          <Badge color="gray" variant="light">
                            미제공
                          </Badge>
                        )}
                      </Table.Td>
                      <Table.Td>
                        <Badge
                          color={
                            course.active_reservation_count > 0
                              ? 'teal'
                              : 'gray'
                          }
                          variant="light"
                        >
                          {course.active_reservation_count}건
                        </Badge>
                      </Table.Td>
                    </Table.Tr>
                  ))}
                </Table.Tbody>
              </Table>
            </Table.ScrollContainer>
          </Paper>
        </>
      )}
    </>
  );
}
