import { Card, Group, Skeleton, Stack } from '@mantine/core';

export function CourseCardSkeleton() {
  return (
    <Card radius="lg" padding={0} className="course-card">
      <Skeleton height={220} radius={0} />
      <Stack p="lg" gap="md">
        <Skeleton height={12} width="35%" />
        <Skeleton height={26} width="85%" />
        <Skeleton height={14} width="60%" />
        <Group>
          <Skeleton height={28} width={90} radius="xl" />
          <Skeleton height={28} width={110} radius="xl" />
        </Group>
        <Skeleton height={42} radius="md" />
      </Stack>
    </Card>
  );
}
