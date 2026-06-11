import { Button, Group, Select } from '@mantine/core';
import { IconAdjustments, IconRefresh } from '@tabler/icons-react';
import { LOCATION_OPTIONS, THEME_OPTIONS } from '../utils/course';

interface CourseFiltersProps {
  location: string | null;
  theme: string | null;
  onLocationChange: (value: string | null) => void;
  onThemeChange: (value: string | null) => void;
  onReset: () => void;
  hasFilters: boolean;
}

export function CourseFilters({
  location,
  theme,
  onLocationChange,
  onThemeChange,
  onReset,
  hasFilters,
}: CourseFiltersProps) {
  return (
    <Group gap="sm" className="filter-row">
      <Select
        leftSection={<IconAdjustments size={16} />}
        placeholder="지역 전체"
        data={LOCATION_OPTIONS}
        value={location}
        onChange={onLocationChange}
        clearable
        searchable
        aria-label="지역 필터"
      />
      <Select
        placeholder="테마 전체"
        data={THEME_OPTIONS}
        value={theme}
        onChange={onThemeChange}
        clearable
        searchable
        aria-label="테마 필터"
      />
      <Button
        variant="subtle"
        color="gray"
        leftSection={<IconRefresh size={16} />}
        onClick={onReset}
        disabled={!hasFilters}
      >
        전체 초기화
      </Button>
    </Group>
  );
}
