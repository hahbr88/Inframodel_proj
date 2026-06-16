import {
  Alert,
  Badge,
  Box,
  Button,
  Divider,
  Drawer,
  Group,
  Image,
  Loader,
  Modal,
  Paper,
  ScrollArea,
  SegmentedControl,
  Select,
  SimpleGrid,
  Skeleton,
  Stack,
  Tabs,
  Text,
  TextInput,
  ThemeIcon,
  Timeline,
  Title,
} from '@mantine/core';
import { useMediaQuery } from '@mantine/hooks';
import { notifications } from '@mantine/notifications';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import dayjs from 'dayjs';
import { useNavigate } from 'react-router-dom';
import {
  IconCalendar,
  IconCircleCheck,
  IconClock,
  IconCloudRain,
  IconExternalLink,
  IconMapPin,
  IconRoute,
  IconUsers,
} from '@tabler/icons-react';
import { useEffect, useMemo, useState } from 'react';
import { createReservation } from '../api/reservations';
import { getApiErrorMessage, isUnauthorized } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { useCourseDetail } from '../hooks/useCourseDetail';
import type { WeatherDetail } from '../types/course';
import { climateColor, getCourseImage, skyLabel } from '../utils/course';
import { EmptyState } from './EmptyState';
import { WeatherSummary } from './WeatherSummary';

interface ForecastSummary {
  forecastAt: string;
  minTemperature: number;
  maxTemperature: number;
  maxRainProbability: number;
  averageHumidity: number;
  worstSky: number;
  spotCount: number;
}

interface CourseDetailDrawerProps {
  courseId: number | null;
  opened: boolean;
  onClose: () => void;
}

function defaultReservationDate() {
  return dayjs().add(1, 'day').hour(9).minute(0).second(0).format('YYYY-MM-DDTHH:mm');
}

export function CourseDetailDrawer({
  courseId,
  opened,
  onClose,
}: CourseDetailDrawerProps) {
  const isMobile = useMediaQuery('(max-width: 48em)');
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const { isAuthenticated, requestLogin, setAuthenticated } = useAuth();
  const [reservationDate, setReservationDate] = useState(defaultReservationDate);
  const [selectedForecastDate, setSelectedForecastDate] = useState<
    string | null
  >(null);
  const [forecastView, setForecastView] = useState<'summary' | 'spot'>(
    'summary',
  );
  const [selectedSpotName, setSelectedSpotName] = useState<string | null>(
    null,
  );
  const [reservationConfirmOpened, setReservationConfirmOpened] =
    useState(false);
  const detailQuery = useCourseDetail(opened ? courseId : null);

  useEffect(() => {
    if (opened) setReservationDate(defaultReservationDate());
  }, [opened, courseId]);

  const reserveMutation = useMutation({
    mutationFn: createReservation,
    onSuccess: () => {
      setReservationConfirmOpened(false);
      onClose();
      setAuthenticated(true);
      const notificationId = notifications.show({
        color: 'teal',
        title: '예약이 완료되었습니다',
        autoClose: 7000,
        message: (
          <Stack gap="xs">
            <Text size="sm">
              내 예약 메뉴에서 일정을 확인할 수 있습니다.
            </Text>
            <Button
              size="compact-xs"
              variant="light"
              color="teal"
              onClick={() => {
                notifications.hide(notificationId);
                navigate('/reservations');
              }}
            >
              내 예약 보기
            </Button>
          </Stack>
        ),
      });
      queryClient.invalidateQueries({ queryKey: ['course-catalog'] });
      queryClient.invalidateQueries({ queryKey: ['course-detail', courseId] });
      queryClient.invalidateQueries({ queryKey: ['reservations'] });
    },
    onError: (error) => {
      if (isUnauthorized(error)) {
        setReservationConfirmOpened(false);
        setAuthenticated(false);
        requestLogin();
        return;
      }
      notifications.show({
        color: 'red',
        title: '예약에 실패했습니다',
        message: getApiErrorMessage(error),
      });
    },
  });

  const detailForecasts = detailQuery.data?.forecasts;
  const forecastSpotNames = useMemo(
    () =>
      [
        ...new Set(
          (detailForecasts ?? []).map((forecast) => forecast.spot_name),
        ),
      ].sort((left, right) => left.localeCompare(right, 'ko')),
    [detailForecasts],
  );

  const forecastDays = useMemo(() => {
    const byTime = new Map<string, WeatherDetail[]>();

    for (const forecast of detailForecasts ?? []) {
      const items = byTime.get(forecast.forecast_at) ?? [];
      items.push(forecast);
      byTime.set(forecast.forecast_at, items);
    }

    const byDate = new Map<string, ForecastSummary[]>();
    for (const [forecastAt, items] of byTime) {
      const temperatures = items.map((item) => item.temperature);
      const date = forecastAt.slice(0, 10);
      const summaries = byDate.get(date) ?? [];
      summaries.push({
        forecastAt,
        minTemperature: Math.min(...temperatures),
        maxTemperature: Math.max(...temperatures),
        maxRainProbability: Math.max(
          ...items.map((item) => item.rain_probability),
        ),
        averageHumidity: Math.round(
          items.reduce((sum, item) => sum + item.humidity, 0) / items.length,
        ),
        worstSky: Math.max(...items.map((item) => item.sky)),
        spotCount: new Set(items.map((item) => item.spot_name)).size,
      });
      byDate.set(date, summaries);
    }

    return [...byDate.entries()]
      .sort(([left], [right]) => left.localeCompare(right))
      .map(([date, summaries]) => ({
        date,
        summaries: summaries.sort((left, right) =>
          left.forecastAt.localeCompare(right.forecastAt),
        ),
      }));
  }, [detailForecasts]);

  useEffect(() => {
    setSelectedForecastDate(forecastDays[0]?.date ?? null);
    setForecastView('summary');
    setSelectedSpotName(forecastSpotNames[0] ?? null);
  }, [courseId, forecastDays, forecastSpotNames]);

  const handleReserve = () => {
    if (!courseId || !reservationDate) return;
    if (!isAuthenticated) {
      requestLogin();
      return;
    }
    if (dayjs(reservationDate).isBefore(dayjs())) {
      notifications.show({
        color: 'orange',
        title: '예약 날짜를 확인해 주세요',
        message: '현재 이후의 날짜와 시간을 선택해야 합니다.',
      });
      return;
    }
    setReservationConfirmOpened(true);
  };

  const confirmReservation = () => {
    if (!courseId || !reservationDate) return;
    if (!isAuthenticated) {
      setReservationConfirmOpened(false);
      requestLogin();
      return;
    }
    reserveMutation.mutate({
      course_id: courseId,
      reservation_date: dayjs(reservationDate).format('YYYY-MM-DDTHH:mm:ssZ'),
    });
  };

  return (
    <>
      <Drawer
        opened={opened}
        onClose={onClose}
        position={isMobile ? 'bottom' : 'right'}
        size={isMobile ? '92%' : 600}
        radius={isMobile ? 'lg lg 0 0' : 0}
        title="코스 상세"
        scrollAreaComponent={ScrollArea.Autosize}
        overlayProps={{ backgroundOpacity: 0.35, blur: 2 }}
        zIndex={200}
      >
        {detailQuery.isPending ? (
          <Stack>
            <Skeleton height={240} radius="lg" />
            <Skeleton height={30} width="80%" />
            <Skeleton height={80} />
            <Skeleton height={180} />
          </Stack>
        ) : detailQuery.isError ? (
          <EmptyState
            error
            title="상세 정보를 불러오지 못했습니다"
            description="잠시 후 다시 시도해 주세요."
            actionLabel="다시 시도"
            onAction={() => detailQuery.refetch()}
          />
        ) : detailQuery.data ? (
          <Stack gap="xl" pb="xl">
          <Box className="drawer-hero">
            <Image
              src={getCourseImage(detailQuery.data)}
              height={240}
              radius="lg"
              alt=""
            />
            <Badge
              className="drawer-location"
              color="dark"
              leftSection={<IconMapPin size={12} />}
            >
              {detailQuery.data.location}
            </Badge>
          </Box>

          <div>
            <Title order={2}>{detailQuery.data.name}</Title>
            <Group gap={7} mt="sm">
              {detailQuery.data.themes.map((theme) => (
                <Badge key={theme} variant="light" color="teal">
                  {theme}
                </Badge>
              ))}
            </Group>
          </div>

          <Paper p="md" radius="md" className="detail-summary">
            <WeatherSummary weather={detailQuery.data.weather} />
            <Divider my="md" />
            <Group justify="space-between">
              {detailQuery.data.tourist_index && (
                <Badge
                  size="lg"
                  variant="light"
                  color={climateColor(detailQuery.data.tourist_index.grade)}
                >
                  관광기후지수 {detailQuery.data.tourist_index.grade} ·{' '}
                  {detailQuery.data.tourist_index.score}
                </Badge>
              )}
              <Group gap={5}>
                <IconUsers size={17} />
                <Text size="sm">
                  활성 예약 {detailQuery.data.active_reservation_count}건
                </Text>
              </Group>
            </Group>
          </Paper>

          <section>
            <Group mb="md">
              <ThemeIcon variant="light" color="teal">
                <IconRoute size={18} />
              </ThemeIcon>
              <Title order={3}>방문 순서</Title>
            </Group>
            <Timeline active={detailQuery.data.spots.length} bulletSize={30}>
              {[...detailQuery.data.spots]
                .sort((a, b) => a.sequence - b.sequence)
                .map((spot) => (
                  <Timeline.Item
                    key={spot.id}
                    bullet={spot.sequence}
                    title={spot.name}
                  >
                    <Group gap={6} mt={5}>
                      <Badge size="sm" variant="outline" color="gray">
                        {spot.indoor_type}
                      </Badge>
                      <Badge size="sm" variant="light" color="teal">
                        {spot.theme}
                      </Badge>
                    </Group>
                    <Group gap={5} mt={7}>
                      <Text
                        component="a"
                        href={`https://map.naver.com/?${new URLSearchParams({
                          lng: String(spot.longitude),
                          lat: String(spot.latitude),
                          title: spot.name,
                        }).toString()}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        size="xs"
                        c="teal.7"
                        fw={700}
                      >
                        네이버 지도에서 보기
                      </Text>
                      <IconExternalLink
                        size={13}
                        color="var(--mantine-color-teal-7)"
                      />
                      {spot.travel_time > 0 && (
                        <Text size="xs" c="dimmed">
                          · 다음 장소까지 {spot.travel_time}분
                        </Text>
                      )}
                    </Group>
                  </Timeline.Item>
                ))}
            </Timeline>
          </section>

          <section>
            <Group mb="md">
              <ThemeIcon variant="light" color="blue">
                <IconCloudRain size={18} />
              </ThemeIcon>
              <Title order={3}>시간대별 예보</Title>
            </Group>
            {forecastDays.length ? (
              <Stack gap="md">
                <Group justify="space-between" align="flex-end">
                  <SegmentedControl
                    value={forecastView}
                    onChange={(value) =>
                      setForecastView(value as 'summary' | 'spot')
                    }
                    data={[
                      { label: '코스 요약', value: 'summary' },
                      { label: '장소별', value: 'spot' },
                    ]}
                    color="teal"
                  />
                  {forecastView === 'spot' && (
                    <Select
                      label="관광지"
                      data={forecastSpotNames}
                      value={selectedSpotName}
                      onChange={setSelectedSpotName}
                      searchable
                      allowDeselect={false}
                      flex={1}
                      maw={280}
                    />
                  )}
                </Group>

                <Tabs
                  value={selectedForecastDate}
                  onChange={setSelectedForecastDate}
                  color="teal"
                >
                  <Tabs.List className="forecast-tabs">
                    {forecastDays.map(({ date }) => (
                      <Tabs.Tab key={date} value={date}>
                        {dayjs(date).isSame(dayjs(), 'day')
                          ? '오늘'
                          : dayjs(date).isSame(dayjs().add(1, 'day'), 'day')
                            ? '내일'
                            : dayjs(date).format('M월 D일')}
                        <Text component="span" size="xs" c="dimmed" ml={5}>
                          {dayjs(date).format('ddd')}
                        </Text>
                      </Tabs.Tab>
                    ))}
                  </Tabs.List>

                  {forecastDays.map(({ date, summaries }) => {
                    const spotForecasts = (detailForecasts ?? [])
                      .filter(
                        (forecast) =>
                          forecast.forecast_at.startsWith(date) &&
                          forecast.spot_name === selectedSpotName,
                      )
                      .sort((left, right) =>
                        left.forecast_at.localeCompare(right.forecast_at),
                      );

                    return (
                      <Tabs.Panel key={date} value={date} pt="md">
                        <SimpleGrid cols={{ base: 1, sm: 2 }}>
                          {forecastView === 'summary'
                            ? summaries.map((forecast) => (
                                <Paper
                                  key={forecast.forecastAt}
                                  p="sm"
                                  radius="md"
                                  withBorder
                                >
                                  <Group justify="space-between" mb={5}>
                                    <Text size="sm" fw={700}>
                                      {dayjs(forecast.forecastAt).format(
                                        'HH:mm',
                                      )}
                                    </Text>
                                    <Text size="sm" fw={800} c="orange.8">
                                      {forecast.minTemperature ===
                                      forecast.maxTemperature
                                        ? `${forecast.minTemperature}°C`
                                        : `${forecast.minTemperature}~${forecast.maxTemperature}°C`}
                                    </Text>
                                  </Group>
                                  <Text size="xs" c="dimmed">
                                    관광지 {forecast.spotCount}곳 기준
                                  </Text>
                                  <Text size="xs" mt={5}>
                                    {skyLabel(forecast.worstSky)} · 최대 강수{' '}
                                    {forecast.maxRainProbability}% · 평균 습도{' '}
                                    {forecast.averageHumidity}%
                                  </Text>
                                </Paper>
                              ))
                            : spotForecasts.map((forecast) => (
                                <Paper
                                  key={`${forecast.forecast_at}-${forecast.spot_name}`}
                                  p="sm"
                                  radius="md"
                                  withBorder
                                >
                                  <Group justify="space-between" mb={5}>
                                    <Text size="sm" fw={700}>
                                      {dayjs(forecast.forecast_at).format(
                                        'HH:mm',
                                      )}
                                    </Text>
                                    <Text size="sm" fw={800} c="orange.8">
                                      {forecast.temperature}°C
                                    </Text>
                                  </Group>
                                  <Text size="xs" c="dimmed" lineClamp={1}>
                                    {forecast.spot_name}
                                  </Text>
                                  <Text size="xs" mt={5}>
                                    {skyLabel(forecast.sky)} · 강수{' '}
                                    {forecast.rain_probability}% · 습도{' '}
                                    {forecast.humidity}%
                                  </Text>
                                </Paper>
                              ))}
                        </SimpleGrid>
                        {forecastView === 'spot' &&
                          spotForecasts.length === 0 && (
                            <Text size="sm" c="dimmed" py="md">
                              선택한 관광지의 해당 날짜 예보가 없습니다.
                            </Text>
                          )}
                      </Tabs.Panel>
                    );
                  })}
                </Tabs>
              </Stack>
            ) : (
              <Text c="dimmed" size="sm">
                상세 예보를 준비 중입니다.
              </Text>
            )}
          </section>

          <Paper p="lg" radius="lg" className="reservation-panel">
            <Group mb="md">
              <ThemeIcon color="teal" variant="filled">
                <IconCalendar size={18} />
              </ThemeIcon>
              <div>
                <Text fw={800}>이 코스 예약하기</Text>
                <Text size="xs" c="dimmed">
                  방문할 날짜와 시간을 선택하세요.
                </Text>
              </div>
            </Group>
            {!detailQuery.data.reservation_enabled && (
              <Alert color="orange" mb="md">
                현재 이 코스는 예약할 수 없습니다.
              </Alert>
            )}
            <Group align="flex-end">
              <TextInput
                type="datetime-local"
                label="예약 일시"
                leftSection={<IconClock size={16} />}
                min={dayjs().format('YYYY-MM-DDTHH:mm')}
                value={reservationDate}
                onChange={(event) => setReservationDate(event.currentTarget.value)}
                flex={1}
              />
              <Button
                color="teal"
                onClick={handleReserve}
                disabled={!detailQuery.data.reservation_enabled}
              >
                {isAuthenticated ? '예약 확정' : '로그인 후 예약'}
              </Button>
            </Group>
          </Paper>
          </Stack>
        ) : (
          <Loader />
        )}
      </Drawer>

      <Modal
        opened={reservationConfirmOpened}
        onClose={() => {
          if (!reserveMutation.isPending) {
            setReservationConfirmOpened(false);
          }
        }}
        title="예약을 확정하시겠습니까?"
        centered
        radius="lg"
        zIndex={500}
        closeOnClickOutside={!reserveMutation.isPending}
        closeOnEscape={!reserveMutation.isPending}
        withCloseButton={!reserveMutation.isPending}
      >
        <Stack>
          <Group align="flex-start" wrap="nowrap">
            <ThemeIcon size={46} radius="xl" color="teal" variant="light">
              <IconCircleCheck size={26} />
            </ThemeIcon>
            <div>
              <Text size="xs" c="dimmed">
                예약 코스
              </Text>
              <Text fw={800}>{detailQuery.data?.name}</Text>
              <Text size="sm" c="dimmed" mt={3}>
                {detailQuery.data?.location}
              </Text>
            </div>
          </Group>

          <Paper p="md" radius="md" withBorder>
            <Group gap="xs">
              <IconCalendar
                size={18}
                color="var(--mantine-color-teal-7)"
              />
              <div>
                <Text size="xs" c="dimmed">
                  예약 일시
                </Text>
                <Text fw={700}>
                  {dayjs(reservationDate).format(
                    'YYYY년 M월 D일 HH:mm',
                  )}
                </Text>
              </div>
            </Group>
          </Paper>

          <Text size="sm" c="dimmed">
            코스와 예약 일시를 확인한 후 예약을 확정해 주세요.
          </Text>

          <Group justify="flex-end">
            <Button
              variant="default"
              disabled={reserveMutation.isPending}
              onClick={() => setReservationConfirmOpened(false)}
            >
              돌아가기
            </Button>
            <Button
              color="teal"
              leftSection={<IconCircleCheck size={17} />}
              loading={reserveMutation.isPending}
              onClick={confirmReservation}
            >
              예약 확정
            </Button>
          </Group>
        </Stack>
      </Modal>
    </>
  );
}
