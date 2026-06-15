import {
  ActionIcon,
  Badge,
  Button,
  Card,
  Group,
  Image,
  Stack,
  Text,
  Title,
} from '@mantine/core';
import {
  IconArrowUpRight,
  IconBookmark,
  IconMapPin,
  IconRoute,
  IconUsers,
} from '@tabler/icons-react';
import type { Course } from '../types/course';
import { climateColor, getCourseImage } from '../utils/course';
import { WeatherSummary } from './WeatherSummary';

interface CourseCardProps {
  course: Course;
  onDetail: () => void;
  onReserve: () => void;
}

export function CourseCard({
  course,
  onDetail,
  onReserve,
}: CourseCardProps) {
  return (
    <Card
      radius="lg"
      padding={0}
      className="course-card"
      data-testid={`course-${course.id}`}
    >
      <div className="course-card-image">
        <Image src={getCourseImage(course)} height={220} alt="" />
        <Badge
          className="location-badge"
          variant="filled"
          color="dark"
          leftSection={<IconMapPin size={12} />}
        >
          {course.location}
        </Badge>
        <ActionIcon
          className="bookmark-button"
          variant="white"
          color="dark"
          radius="xl"
          aria-label="코스 저장"
        >
          <IconBookmark size={18} />
        </ActionIcon>
      </div>

      <Stack p="lg" gap="md" className="course-card-body">
        <div>
          <Group gap={7} mb={7}>
            <IconRoute size={16} color="var(--mantine-color-teal-7)" />
            <Text size="xs" fw={700} c="teal.8" tt="uppercase">
              관광지 {course.spot_count}곳
            </Text>
          </Group>
          <Title order={3} lineClamp={2} className="course-title">
            {course.name}
          </Title>
        </div>

        <Group gap={7}>
          {course.themes.slice(0, 3).map((theme) => (
            <Badge key={theme} variant="light" color="gray" radius="sm">
              {theme}
            </Badge>
          ))}
        </Group>

        <WeatherSummary weather={course.weather} compact />

        <Group justify="space-between" className="card-meta">
          <Group gap="xs">
            {course.tourist_index && (
              <Badge
                color={climateColor(course.tourist_index.grade)}
                variant="light"
                radius="sm"
              >
                관광지수 {course.tourist_index.grade}
              </Badge>
            )}
          </Group>
          <Group gap={5}>
            <IconUsers size={15} />
            <Text size="xs" c="dimmed">
              예약 {course.active_reservation_count}
            </Text>
          </Group>
        </Group>

        <Group grow>
          <Button
            variant="default"
            rightSection={<IconArrowUpRight size={16} />}
            onClick={onDetail}
          >
            상세 보기
          </Button>
          <Button
            color="teal"
            onClick={onReserve}
            disabled={!course.reservation_enabled}
          >
            {course.reservation_enabled ? '예약하기' : '예약 불가'}
          </Button>
        </Group>
      </Stack>
    </Card>
  );
}
