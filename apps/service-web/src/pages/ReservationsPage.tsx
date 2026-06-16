import {
  Badge,
  Button,
  Container,
  Group,
  Loader,
  Modal,
  Paper,
  Stack,
  Text,
  TextInput,
  ThemeIcon,
  Title,
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import dayjs from 'dayjs';
import {
  IconCalendarCheck,
  IconClock,
  IconEdit,
  IconExclamationCircle,
  IconMapRoute,
  IconTrash,
} from '@tabler/icons-react';
import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { getApiErrorMessage, isUnauthorized } from '../api/client';
import {
  cancelReservation,
  getReservations,
  updateReservation,
} from '../api/reservations';
import { EmptyState } from '../components/EmptyState';
import { useAuth } from '../context/AuthContext';
import type {
  Reservation,
  ReservationListResponse,
} from '../types/reservation';

function isActiveReservation(status: string) {
  return status.toUpperCase() !== 'CANCELLED';
}

export function ReservationsPage() {
  const queryClient = useQueryClient();
  const loginRequested = useRef(false);
  const [editingReservation, setEditingReservation] =
    useState<Reservation | null>(null);
  const [cancellingReservation, setCancellingReservation] =
    useState<Reservation | null>(null);
  const [editingDate, setEditingDate] = useState('');
  const { requestLogin, setAuthenticated } = useAuth();
  const reservationsQuery = useQuery({
    queryKey: ['reservations'],
    queryFn: getReservations,
    retry: false,
  });

  useEffect(() => {
    if (reservationsQuery.isSuccess) {
      setAuthenticated(true);
      loginRequested.current = false;
    }
    if (
      reservationsQuery.isError &&
      isUnauthorized(reservationsQuery.error) &&
      !loginRequested.current
    ) {
      loginRequested.current = true;
      setAuthenticated(false);
      requestLogin(() => {
        loginRequested.current = false;
        reservationsQuery.refetch();
      });
    }
  }, [
    requestLogin,
    reservationsQuery,
    setAuthenticated,
  ]);

  const cancelMutation = useMutation({
    mutationFn: cancelReservation,
    onSuccess: (_, reservationId) => {
      setCancellingReservation(null);
      queryClient.setQueryData<ReservationListResponse>(
        ['reservations'],
        (current) => {
          if (!current) return current;
          const reservations = current.reservations.filter(
            (reservation) => reservation.id !== reservationId,
          );
          return {
            ...current,
            count: reservations.length,
            reservations,
          };
        },
      );
      notifications.show({
        color: 'teal',
        title: '예약이 취소되었습니다',
        message: '예약 목록에 변경 사항을 반영했습니다.',
      });
      queryClient.invalidateQueries({ queryKey: ['reservations'] });
      queryClient.invalidateQueries({ queryKey: ['course-catalog'] });
      queryClient.invalidateQueries({ queryKey: ['course-detail'] });
    },
    onError: (error) => {
      if (isUnauthorized(error)) {
        setAuthenticated(false);
        requestLogin(() => {
          if (cancellingReservation) {
            cancelMutation.mutate(cancellingReservation.id);
          }
        });
        return;
      }
      notifications.show({
        color: 'red',
        title: '예약 취소에 실패했습니다',
        message: getApiErrorMessage(error),
      });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({
      reservationId,
      reservationDate,
    }: {
      reservationId: number;
      reservationDate: string;
    }) =>
      updateReservation(reservationId, {
        reservation_date: dayjs(reservationDate).format(
          'YYYY-MM-DDTHH:mm:ssZ',
        ),
      }),
    onSuccess: () => {
      setEditingReservation(null);
      notifications.show({
        color: 'teal',
        title: '예약 일정이 변경되었습니다',
        message: '변경한 날짜와 시간을 예약 목록에 반영했습니다.',
      });
      queryClient.invalidateQueries({ queryKey: ['reservations'] });
    },
    onError: (error) => {
      if (isUnauthorized(error)) {
        setAuthenticated(false);
        requestLogin(() => {
          if (editingReservation && editingDate) {
            updateMutation.mutate({
              reservationId: editingReservation.id,
              reservationDate: editingDate,
            });
          }
        });
        return;
      }
      notifications.show({
        color: 'red',
        title: '예약 수정에 실패했습니다',
        message: getApiErrorMessage(error),
      });
    },
  });

  const openEditModal = (reservation: Reservation) => {
    setEditingReservation(reservation);
    setEditingDate(
      dayjs(reservation.reservation_date).format('YYYY-MM-DDTHH:mm'),
    );
  };

  const submitUpdate = () => {
    if (!editingReservation || !editingDate) return;
    if (!dayjs(editingDate).isAfter(dayjs())) {
      notifications.show({
        color: 'orange',
        title: '예약 날짜를 확인해 주세요',
        message: '현재 이후의 날짜와 시간을 선택해야 합니다.',
      });
      return;
    }
    updateMutation.mutate({
      reservationId: editingReservation.id,
      reservationDate: editingDate,
    });
  };

  const reservations = reservationsQuery.data?.reservations ?? [];

  return (
    <main className="reservations-page">
      <Container size="md">
        <Group justify="space-between" align="flex-end" mb={36}>
          <div>
            <Text c="teal.8" fw={800} size="sm" mb={5}>
              MY JOURNEY
            </Text>
            <Title>내 예약</Title>
            <Text c="dimmed" mt={8}>
              다가오는 여행 일정과 예약 상태를 확인하세요.
            </Text>
          </div>
          <Button component={Link} to="/" variant="light" color="teal">
            코스 더 보기
          </Button>
        </Group>

        {reservationsQuery.isPending ? (
          <Stack align="center" py={80}>
            <Loader color="teal" />
            <Text c="dimmed">예약을 불러오는 중입니다</Text>
          </Stack>
        ) : reservationsQuery.isError ? (
          !isUnauthorized(reservationsQuery.error) && (
            <EmptyState
              error
              title="예약을 불러오지 못했습니다"
              description={getApiErrorMessage(reservationsQuery.error)}
              actionLabel="다시 시도"
              onAction={() => reservationsQuery.refetch()}
            />
          )
        ) : reservations.length === 0 ? (
          <EmptyState
            title="아직 예약한 코스가 없습니다"
            description="날씨가 좋은 여행 코스를 찾아 첫 일정을 만들어 보세요."
            actionLabel="코스 둘러보기"
            onAction={() => window.location.assign('/')}
          />
        ) : (
          <Stack gap="md">
            {reservations.map((reservation) => (
              <Paper
                key={reservation.id}
                p="lg"
                radius="lg"
                className="reservation-card"
              >
                <Group justify="space-between" align="center">
                  <Group gap="md">
                    <ThemeIcon size={48} radius="md" color="teal" variant="light">
                      <IconMapRoute size={24} />
                    </ThemeIcon>
                    <div>
                      <Group gap="xs" mb={5}>
                        <Title order={3}>{reservation.course_name}</Title>
                        <Badge
                          color={
                            isActiveReservation(reservation.status)
                              ? 'teal'
                              : 'gray'
                          }
                          variant="light"
                        >
                          {isActiveReservation(reservation.status)
                            ? '예약 완료'
                            : '취소됨'}
                        </Badge>
                      </Group>
                      <Group gap="lg">
                        <Group gap={5}>
                          <IconCalendarCheck size={16} />
                          <Text size="sm">
                            {dayjs(reservation.reservation_date).format(
                              'YYYY년 M월 D일',
                            )}
                          </Text>
                        </Group>
                        <Group gap={5}>
                          <IconClock size={16} />
                          <Text size="sm">
                            {dayjs(reservation.reservation_date).format('HH:mm')}
                          </Text>
                        </Group>
                      </Group>
                    </div>
                  </Group>
                  {isActiveReservation(reservation.status) && (
                    <Group gap="xs" className="reservation-actions">
                      <Button
                        variant="light"
                        color="teal"
                        leftSection={<IconEdit size={16} />}
                        onClick={() => openEditModal(reservation)}
                      >
                        일정 수정
                      </Button>
                      <Button
                        variant="subtle"
                        color="red"
                        leftSection={<IconTrash size={16} />}
                        onClick={() => setCancellingReservation(reservation)}
                      >
                        예약 취소
                      </Button>
                    </Group>
                  )}
                </Group>
              </Paper>
            ))}
          </Stack>
        )}
      </Container>

      <Modal
        opened={editingReservation !== null}
        onClose={() => setEditingReservation(null)}
        title="예약 일정 수정"
        centered
        radius="lg"
      >
        <Stack>
          <div>
            <Text size="sm" c="dimmed">
              예약 코스
            </Text>
            <Text fw={800}>{editingReservation?.course_name}</Text>
          </div>
          <TextInput
            type="datetime-local"
            label="변경할 날짜와 시간"
            leftSection={<IconClock size={16} />}
            min={dayjs().format('YYYY-MM-DDTHH:mm')}
            value={editingDate}
            onChange={(event) => setEditingDate(event.currentTarget.value)}
          />
          <Group justify="flex-end">
            <Button
              variant="default"
              onClick={() => setEditingReservation(null)}
            >
              닫기
            </Button>
            <Button
              color="teal"
              leftSection={<IconEdit size={16} />}
              loading={updateMutation.isPending}
              onClick={submitUpdate}
            >
              변경 저장
            </Button>
          </Group>
        </Stack>
      </Modal>

      <Modal
        opened={cancellingReservation !== null}
        onClose={() => {
          if (!cancelMutation.isPending) {
            setCancellingReservation(null);
          }
        }}
        title="예약을 취소할까요?"
        centered
        radius="lg"
        closeOnClickOutside={!cancelMutation.isPending}
        closeOnEscape={!cancelMutation.isPending}
        withCloseButton={!cancelMutation.isPending}
      >
        <Stack>
          <Group align="flex-start" wrap="nowrap">
            <ThemeIcon size={44} radius="xl" color="red" variant="light">
              <IconExclamationCircle size={24} />
            </ThemeIcon>
            <div>
              <Text fw={800}>{cancellingReservation?.course_name}</Text>
              {cancellingReservation && (
                <Text size="sm" c="dimmed" mt={4}>
                  {dayjs(cancellingReservation.reservation_date).format(
                    'YYYY년 M월 D일 HH:mm',
                  )}
                </Text>
              )}
            </div>
          </Group>
          <Text size="sm">
            취소한 예약은 내 예약 목록에서 제거됩니다. 계속 진행하시겠습니까?
          </Text>
          <Group justify="flex-end">
            <Button
              variant="default"
              disabled={cancelMutation.isPending}
              onClick={() => setCancellingReservation(null)}
            >
              돌아가기
            </Button>
            <Button
              color="red"
              leftSection={<IconTrash size={16} />}
              loading={cancelMutation.isPending}
              onClick={() => {
                if (cancellingReservation) {
                  cancelMutation.mutate(cancellingReservation.id);
                }
              }}
            >
              예약 취소 확정
            </Button>
          </Group>
        </Stack>
      </Modal>
    </main>
  );
}
