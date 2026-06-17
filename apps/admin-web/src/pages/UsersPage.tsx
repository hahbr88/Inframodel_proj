import {
  ActionIcon,
  Alert,
  Badge,
  Button,
  Group,
  Loader,
  Modal,
  Paper,
  Stack,
  Table,
  Text,
  TextInput,
  Tooltip,
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { IconSearch, IconUserX } from '@tabler/icons-react';
import { useMemo, useState } from 'react';
import {
  deactivateAdminUser,
  getAdminUsers,
} from '../api/admin';
import { getApiErrorMessage } from '../api/client';
import { PageHeader } from '../components/PageHeader';
import type { AdminUser } from '../types/admin';

export function UsersPage() {
  const queryClient = useQueryClient();
  const [keyword, setKeyword] = useState('');
  const [deactivating, setDeactivating] = useState<AdminUser | null>(null);
  const usersQuery = useQuery({
    queryKey: ['admin-users'],
    queryFn: getAdminUsers,
  });

  const deactivateMutation = useMutation({
    mutationFn: () => deactivateAdminUser(deactivating!.id),
    onSuccess: () => {
      setDeactivating(null);
      queryClient.invalidateQueries({ queryKey: ['admin-users'] });
      queryClient.invalidateQueries({ queryKey: ['admin-reservations'] });
      notifications.show({
        color: 'teal',
        title: '사용자를 비활성화했습니다',
        message: '해당 계정은 더 이상 로그인할 수 없습니다.',
      });
    },
    onError: (error) =>
      notifications.show({
        color: 'red',
        title: '사용자 비활성화 실패',
        message: getApiErrorMessage(error),
      }),
  });

  const users = useMemo(() => {
    const normalized = keyword.trim().toLocaleLowerCase();
    const items = usersQuery.data?.users ?? [];
    if (!normalized) return items;
    return items.filter(
      (item) =>
        item.username.toLocaleLowerCase().includes(normalized) ||
        String(item.id).includes(normalized),
    );
  }, [keyword, usersQuery.data]);

  return (
    <>
      <PageHeader
        eyebrow="Account operations"
        title="사용자 관리"
        description="서비스 사용자 계정 상태와 예약 현황을 확인하고 비활성화합니다."
        action={
          <TextInput
            value={keyword}
            onChange={(event) => setKeyword(event.currentTarget.value)}
            placeholder="아이디 또는 사용자 번호"
            leftSection={<IconSearch size={17} />}
          />
        }
      />

      {usersQuery.isPending ? (
        <Stack align="center" py={100}>
          <Loader />
        </Stack>
      ) : usersQuery.isError ? (
        <Alert color="red">{getApiErrorMessage(usersQuery.error)}</Alert>
      ) : (
        <Paper className="content-panel table-panel" radius="lg">
          <Table.ScrollContainer minWidth={760}>
            <Table verticalSpacing="md" horizontalSpacing="lg" highlightOnHover>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>사용자</Table.Th>
                  <Table.Th>권한</Table.Th>
                  <Table.Th>상태</Table.Th>
                  <Table.Th>전체 예약</Table.Th>
                  <Table.Th>활성 예약</Table.Th>
                  <Table.Th ta="right">관리</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {users.map((user) => (
                  <Table.Tr key={user.id}>
                    <Table.Td>
                      <Text fw={700}>{user.username}</Text>
                      <Text size="xs" c="dimmed">
                        사용자 #{user.id}
                      </Text>
                    </Table.Td>
                    <Table.Td>
                      <Badge
                        color={user.role === 'ADMIN' ? 'indigo' : 'gray'}
                        variant="light"
                      >
                        {user.role === 'ADMIN' ? '관리자' : '사용자'}
                      </Badge>
                    </Table.Td>
                    <Table.Td>
                      <Badge
                        color={user.status === 'ACTIVE' ? 'teal' : 'gray'}
                        variant="light"
                      >
                        {user.status === 'ACTIVE' ? '활성' : '비활성'}
                      </Badge>
                    </Table.Td>
                    <Table.Td>{user.reservation_count.toLocaleString()}</Table.Td>
                    <Table.Td>
                      {user.active_reservation_count.toLocaleString()}
                    </Table.Td>
                    <Table.Td>
                      <Group justify="flex-end">
                        <Tooltip label="사용자 비활성화">
                          <ActionIcon
                            variant="subtle"
                            color="red"
                            disabled={
                              user.status !== 'ACTIVE' || user.role === 'ADMIN'
                            }
                            onClick={() => setDeactivating(user)}
                          >
                            <IconUserX size={18} />
                          </ActionIcon>
                        </Tooltip>
                      </Group>
                    </Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>
          </Table.ScrollContainer>
        </Paper>
      )}

      <Modal
        opened={deactivating !== null}
        onClose={() => setDeactivating(null)}
        title="사용자 비활성화"
      >
        <Text>
          <strong>{deactivating?.username}</strong> 계정을 비활성화하시겠습니까?
        </Text>
        <Group justify="flex-end" mt="xl">
          <Button variant="default" onClick={() => setDeactivating(null)}>
            닫기
          </Button>
          <Button
            color="red"
            onClick={() => deactivateMutation.mutate()}
            loading={deactivateMutation.isPending}
          >
            비활성화
          </Button>
        </Group>
      </Modal>
    </>
  );
}
