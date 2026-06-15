import {
  AppShell,
  Burger,
  Button,
  Group,
  NavLink,
  Stack,
  Text,
  ThemeIcon,
} from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import {
  IconCalendarEvent,
  IconLayoutDashboard,
  IconLogout,
  IconMapRoute,
  IconShieldCheck,
} from '@tabler/icons-react';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { useAdminAuth } from '../context/adminAuth';

const navigation = [
  { label: '대시보드', path: '/', icon: IconLayoutDashboard },
  { label: '예약 관리', path: '/reservations', icon: IconCalendarEvent },
  { label: '코스 현황', path: '/courses', icon: IconMapRoute },
];

export function AdminLayout() {
  const [opened, { toggle, close }] = useDisclosure();
  const location = useLocation();
  const navigate = useNavigate();
  const { logout } = useAdminAuth();

  const handleLogout = async () => {
    await logout();
    navigate('/login', { replace: true });
  };

  return (
    <AppShell
      header={{ height: 68 }}
      navbar={{
        width: 250,
        breakpoint: 'sm',
        collapsed: { mobile: !opened },
      }}
      padding="lg"
    >
      <AppShell.Header px="lg">
        <Group h="100%" justify="space-between">
          <Group>
            <Burger opened={opened} onClick={toggle} hiddenFrom="sm" size="sm" />
            <ThemeIcon size={38} radius="md" variant="gradient">
              <IconShieldCheck size={22} />
            </ThemeIcon>
            <div>
              <Text fw={900}>TripKey Admin</Text>
              <Text size="xs" c="dimmed">
                운영 관리 시스템
              </Text>
            </div>
          </Group>
          <Button
            variant="subtle"
            color="gray"
            leftSection={<IconLogout size={17} />}
            onClick={handleLogout}
          >
            로그아웃
          </Button>
        </Group>
      </AppShell.Header>

      <AppShell.Navbar p="md">
        <Stack gap={6}>
          {navigation.map((item) => (
            <NavLink
              key={item.path}
              label={item.label}
              leftSection={<item.icon size={19} />}
              active={location.pathname === item.path}
              onClick={() => {
                navigate(item.path);
                close();
              }}
              variant="filled"
            />
          ))}
        </Stack>
      </AppShell.Navbar>

      <AppShell.Main>
        <Outlet />
      </AppShell.Main>
    </AppShell>
  );
}
