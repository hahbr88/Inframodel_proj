import {
  Alert,
  Badge,
  Button,
  Grid,
  Group,
  Loader,
  Paper,
  SimpleGrid,
  Stack,
  Text,
  ThemeIcon,
  Title,
} from '@mantine/core';
import { useQuery } from '@tanstack/react-query';
import {
  IconCalendarCheck,
  IconCalendarEvent,
  IconCircleX,
  IconMapRoute,
  IconRefresh,
} from '@tabler/icons-react';
import { Link } from 'react-router-dom';
import { getDashboard, getAdminReservations } from '../api/admin';
import { getApiErrorMessage } from '../api/client';
import { PageHeader } from '../components/PageHeader';

const cards = [
  {
    key: 'course_count',
    label: '운영 코스',
    icon: IconMapRoute,
    color: 'indigo',
  },
  {
    key: 'active_reservation_count',
    label: '활성 예약',
    icon: IconCalendarCheck,
    color: 'teal',
  },
  {
    key: 'upcoming_reservation_count',
    label: '예정 예약',
    icon: IconCalendarEvent,
    color: 'blue',
  },
  {
    key: 'cancelled_reservation_count',
    label: '취소 예약',
    icon: IconCircleX,
    color: 'gray',
  },
] as const;

export function DashboardPage() {
  const dashboardQuery = useQuery({
    queryKey: ['admin-dashboard'],
    queryFn: getDashboard,
  });
  const reservationsQuery = useQuery({
    queryKey: ['admin-reservations'],
    queryFn: getAdminReservations,
  });

  if (dashboardQuery.isPending) {
    return (
      <Stack align="center" py={120}>
        <Loader />
        <Text c="dimmed">운영 현황을 불러오는 중입니다.</Text>
      </Stack>
    );
  }

  if (dashboardQuery.isError) {
    return (
      <Alert color="red" title="대시보드를 불러오지 못했습니다">
        {getApiErrorMessage(dashboardQuery.error)}
      </Alert>
    );
  }

  const recentReservations =
    reservationsQuery.data?.reservations.slice(0, 5) ?? [];

  return (
    <>
      <PageHeader
        eyebrow="Operations overview"
        title="운영 대시보드"
        description="사용자 웹에서 발생한 예약과 코스 운영 상태를 확인합니다."
        action={
          <Button
            variant="light"
            leftSection={<IconRefresh size={17} />}
            onClick={() => {
              dashboardQuery.refetch();
              reservationsQuery.refetch();
            }}
          >
            새로고침
          </Button>
        }
      />

      <SimpleGrid cols={{ base: 1, sm: 2, lg: 4 }} mb="xl">
        {cards.map((card) => (
          <Paper key={card.key} className="stat-card" p="lg" radius="lg">
            <Group justify="space-between" mb="lg">
              <Text c="dimmed" fw={700} size="sm">
                {card.label}
              </Text>
              <ThemeIcon color={card.color} variant="light" radius="md">
                <card.icon size={19} />
              </ThemeIcon>
            </Group>
            <Title order={2}>
              {dashboardQuery.data[card.key].toLocaleString()}
            </Title>
          </Paper>
        ))}
      </SimpleGrid>

      <Grid>
        <Grid.Col span={{ base: 12, lg: 8 }}>
          <Paper className="content-panel" p="xl" radius="lg">
            <Group justify="space-between" mb="lg">
              <div>
                <Title order={3}>최근 예약</Title>
                <Text c="dimmed" size="sm" mt={3}>
                  사용자 서비스의 최근 예약 변경 내역입니다.
                </Text>
              </div>
              <Button
                component={Link}
                to="/reservations"
                variant="subtle"
                size="compact-sm"
              >
                전체 보기
              </Button>
            </Group>
            <Stack gap="sm">
              {recentReservations.map((reservation) => (
                <Group
                  key={reservation.id}
                  justify="space-between"
                  className="dashboard-row"
                >
                  <div>
                    <Text fw={700}>{reservation.course_name}</Text>
                    <Text size="xs" c="dimmed">
                      예약 #{reservation.id} · {reservation.username}
                    </Text>
                  </div>
                  <Badge
                    color={
                      reservation.status === 'CANCELLED' ? 'gray' : 'teal'
                    }
                    variant="light"
                  >
                    {reservation.status === 'CANCELLED' ? '취소' : '활성'}
                  </Badge>
                </Group>
              ))}
              {!recentReservations.length && (
                <Text c="dimmed">표시할 예약이 없습니다.</Text>
              )}
            </Stack>
          </Paper>
        </Grid.Col>
        <Grid.Col span={{ base: 12, lg: 4 }}>
          <Paper className="content-panel" p="xl" radius="lg" h="100%">
            <Title order={3}>서비스 연결</Title>
            <Text c="dimmed" size="sm" mt={5} mb="lg">
              사용자 웹과 관리자 웹이 동일한 예약 데이터를 공유합니다.
            </Text>
            <Stack>
              <Group justify="space-between">
                <Text size="sm">통합 WAS</Text>
                <Badge color="teal">연결됨</Badge>
              </Group>
              <Group justify="space-between">
                <Text size="sm">전체 예약</Text>
                <Text fw={800}>
                  {dashboardQuery.data.reservation_count.toLocaleString()}
                </Text>
              </Group>
            </Stack>
          </Paper>
        </Grid.Col>
      </Grid>
    </>
  );
}
