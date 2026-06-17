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
import { IconEdit, IconSearch, IconTrash } from '@tabler/icons-react';
import dayjs from 'dayjs';
import { useMemo, useState } from 'react';
import {
  cancelAdminReservation,
  getAdminReservations,
  updateAdminReservation,
} from '../api/admin';
import { getApiErrorMessage } from '../api/client';
import { PageHeader } from '../components/PageHeader';
import type { AdminReservation } from '../types/admin';

export function ReservationsPage() {
  const queryClient = useQueryClient();
  const [keyword, setKeyword] = useState('');
  const [editing, setEditing] = useState<AdminReservation | null>(null);
  const [editingDate, setEditingDate] = useState('');
  const [cancelling, setCancelling] = useState<AdminReservation | null>(null);
  const reservationsQuery = useQuery({
    queryKey: ['admin-reservations'],
    queryFn: getAdminReservations,
  });

  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: ['admin-reservations'] });
    queryClient.invalidateQueries({ queryKey: ['admin-dashboard'] });
  };

  const updateMutation = useMutation({
    mutationFn: () =>
      updateAdminReservation(
        editing!.id,
        dayjs(editingDate).format('YYYY-MM-DDTHH:mm:ssZ'),
      ),
    onSuccess: () => {
      setEditing(null);
      refresh();
      notifications.show({
        color: 'teal',
        title: '예약 일정 변경 완료',
        message: '사용자 서비스에도 변경 결과가 반영됩니다.',
      });
    },
    onError: (error) =>
      notifications.show({
        color: 'red',
        title: '예약 수정 실패',
        message: getApiErrorMessage(error),
      }),
  });

  const cancelMutation = useMutation({
    mutationFn: () => cancelAdminReservation(cancelling!.id),
    onSuccess: () => {
      setCancelling(null);
      refresh();
      notifications.show({
        color: 'teal',
        title: '예약 취소 완료',
        message: '관리자에 의해 예약이 취소되었습니다.',
      });
    },
    onError: (error) =>
      notifications.show({
        color: 'red',
        title: '예약 취소 실패',
        message: getApiErrorMessage(error),
      }),
  });

  const reservations = useMemo(() => {
    const normalized = keyword.trim().toLocaleLowerCase();
    const items = reservationsQuery.data?.reservations ?? [];
    if (!normalized) return items;
    return items.filter(
      (item) =>
        item.course_name.toLocaleLowerCase().includes(normalized) ||
        item.username.toLocaleLowerCase().includes(normalized) ||
        String(item.user_id).includes(normalized) ||
        String(item.id).includes(normalized),
    );
  }, [keyword, reservationsQuery.data]);

  return (
    <>
      <PageHeader
        eyebrow="Reservation operations"
        title="예약 관리"
        description="사용자 웹에서 생성된 전체 예약을 조회하고 일정을 변경하거나 취소합니다."
        action={
          <TextInput
            value={keyword}
            onChange={(event) => setKeyword(event.currentTarget.value)}
            placeholder="예약자, 코스명, 예약 번호"
            leftSection={<IconSearch size={17} />}
          />
        }
      />

      {reservationsQuery.isPending ? (
        <Stack align="center" py={100}>
          <Loader />
        </Stack>
      ) : reservationsQuery.isError ? (
        <Alert color="red">
          {getApiErrorMessage(reservationsQuery.error)}
        </Alert>
      ) : (
        <Paper className="content-panel table-panel" radius="lg">
          <Table.ScrollContainer minWidth={760}>
            <Table verticalSpacing="md" horizontalSpacing="lg" highlightOnHover>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>예약 번호</Table.Th>
                  <Table.Th>예약자</Table.Th>
                  <Table.Th>코스</Table.Th>
                  <Table.Th>예약 일시</Table.Th>
                  <Table.Th>상태</Table.Th>
                  <Table.Th ta="right">관리</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {reservations.map((reservation) => (
                  <Table.Tr key={reservation.id}>
                    <Table.Td>#{reservation.id}</Table.Td>
                    <Table.Td>
                      <Text fw={700}>{reservation.username}</Text>
                      <Text size="xs" c="dimmed">
                        사용자 #{reservation.user_id}
                      </Text>
                    </Table.Td>
                    <Table.Td>
                      <Text fw={700}>{reservation.course_name}</Text>
                      <Text size="xs" c="dimmed">
                        코스 #{reservation.course_id}
                      </Text>
                    </Table.Td>
                    <Table.Td>
                      {dayjs(reservation.reservation_date).format(
                        'YYYY.MM.DD HH:mm',
                      )}
                    </Table.Td>
                    <Table.Td>
                      <Badge
                        color={
                          reservation.status === 'CANCELLED' ? 'gray' : 'teal'
                        }
                        variant="light"
                      >
                        {reservation.status === 'CANCELLED'
                          ? '취소됨'
                          : '예약 완료'}
                      </Badge>
                    </Table.Td>
                    <Table.Td>
                      <Group justify="flex-end" gap={5}>
                        <Tooltip label="일정 변경">
                          <ActionIcon
                            variant="subtle"
                            disabled={reservation.status === 'CANCELLED'}
                            onClick={() => {
                              setEditing(reservation);
                              setEditingDate(
                                dayjs(reservation.reservation_date).format(
                                  'YYYY-MM-DDTHH:mm',
                                ),
                              );
                            }}
                          >
                            <IconEdit size={18} />
                          </ActionIcon>
                        </Tooltip>
                        <Tooltip label="예약 취소">
                          <ActionIcon
                            variant="subtle"
                            color="red"
                            disabled={reservation.status === 'CANCELLED'}
                            onClick={() => setCancelling(reservation)}
                          >
                            <IconTrash size={18} />
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
        opened={editing !== null}
        onClose={() => setEditing(null)}
        title="예약 일정 변경"
      >
        <Stack>
          <Text fw={700}>{editing?.course_name}</Text>
          <TextInput
            type="datetime-local"
            label="변경할 일시"
            value={editingDate}
            onChange={(event) => setEditingDate(event.currentTarget.value)}
          />
          <Button
            onClick={() => updateMutation.mutate()}
            loading={updateMutation.isPending}
            disabled={!editingDate}
          >
            변경 저장
          </Button>
        </Stack>
      </Modal>

      <Modal
        opened={cancelling !== null}
        onClose={() => setCancelling(null)}
        title="예약 취소 확인"
      >
        <Text>
          <strong>{cancelling?.course_name}</strong> 예약을 취소하시겠습니까?
        </Text>
        <Group justify="flex-end" mt="xl">
          <Button variant="default" onClick={() => setCancelling(null)}>
            닫기
          </Button>
          <Button
            color="red"
            onClick={() => cancelMutation.mutate()}
            loading={cancelMutation.isPending}
          >
            예약 취소
          </Button>
        </Group>
      </Modal>
    </>
  );
}
