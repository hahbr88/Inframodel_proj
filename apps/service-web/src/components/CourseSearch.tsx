import { TextInput } from '@mantine/core';
import { IconSearch, IconX } from '@tabler/icons-react';

interface CourseSearchProps {
  value: string;
  onChange: (value: string) => void;
}

export function CourseSearch({ value, onChange }: CourseSearchProps) {
  return (
    <TextInput
      className="catalog-search"
      size="lg"
      radius="md"
      placeholder="어디로 떠나고 싶으세요?"
      aria-label="코스명, 지역, 테마, 관광지 검색"
      leftSection={<IconSearch size={20} />}
      rightSection={
        value ? (
          <IconX
            size={18}
            role="button"
            aria-label="검색어 지우기"
            onClick={() => onChange('')}
          />
        ) : null
      }
      value={value}
      onChange={(event) => onChange(event.currentTarget.value)}
    />
  );
}
