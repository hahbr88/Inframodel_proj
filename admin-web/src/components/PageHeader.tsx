import { Group, Text, Title } from '@mantine/core';
import type { ReactNode } from 'react';

interface PageHeaderProps {
  eyebrow: string;
  title: string;
  description: string;
  action?: ReactNode;
}

export function PageHeader({
  eyebrow,
  title,
  description,
  action,
}: PageHeaderProps) {
  return (
    <Group justify="space-between" align="flex-end" mb="xl">
      <div>
        <Text size="xs" fw={800} c="indigo" tt="uppercase" mb={5}>
          {eyebrow}
        </Text>
        <Title order={1}>{title}</Title>
        <Text c="dimmed" mt={6}>
          {description}
        </Text>
      </div>
      {action}
    </Group>
  );
}
