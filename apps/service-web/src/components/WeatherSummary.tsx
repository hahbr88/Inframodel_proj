import { Group, Text, ThemeIcon } from '@mantine/core';
import {
  IconCloudRain,
  IconDroplet,
  IconTemperature,
} from '@tabler/icons-react';
import type { CourseWeatherSummary } from '../types/course';

interface WeatherSummaryProps {
  weather: CourseWeatherSummary | null;
  compact?: boolean;
}

export function WeatherSummary({ weather, compact }: WeatherSummaryProps) {
  if (!weather) {
    return (
      <Text c="dimmed" size="sm">
        날씨 정보 준비 중
      </Text>
    );
  }

  return (
    <Group gap={compact ? 'sm' : 'md'} wrap="wrap">
      <Group gap={5}>
        <ThemeIcon variant="light" color="orange" size="sm">
          <IconTemperature size={14} />
        </ThemeIcon>
        <Text size="sm" fw={600}>
          {weather.min_temperature}~{weather.max_temperature}°C
        </Text>
      </Group>
      <Group gap={5}>
        <IconCloudRain size={16} color="var(--mantine-color-blue-6)" />
        <Text size="sm">강수 {weather.max_rain_probability}%</Text>
      </Group>
      <Group gap={5}>
        <IconDroplet size={15} color="var(--mantine-color-cyan-6)" />
        <Text size="sm">습도 {weather.average_humidity}%</Text>
      </Group>
    </Group>
  );
}
