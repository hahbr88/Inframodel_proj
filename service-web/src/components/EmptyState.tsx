import { Button, Center, Stack, Text, ThemeIcon, Title } from '@mantine/core';
import { IconMapSearch, IconRefresh } from '@tabler/icons-react';

interface EmptyStateProps {
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
  error?: boolean;
}

export function EmptyState({
  title,
  description,
  actionLabel,
  onAction,
  error,
}: EmptyStateProps) {
  return (
    <Center className="empty-state">
      <Stack align="center" gap="sm">
        <ThemeIcon
          size={58}
          radius="xl"
          variant="light"
          color={error ? 'red' : 'teal'}
        >
          {error ? <IconRefresh size={28} /> : <IconMapSearch size={28} />}
        </ThemeIcon>
        <Title order={3}>{title}</Title>
        <Text c="dimmed" ta="center" maw={420}>
          {description}
        </Text>
        {actionLabel && onAction && (
          <Button mt="xs" variant="light" onClick={onAction}>
            {actionLabel}
          </Button>
        )}
      </Stack>
    </Center>
  );
}
