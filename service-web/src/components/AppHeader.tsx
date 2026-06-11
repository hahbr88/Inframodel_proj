import {
  Button,
  Container,
  Group,
  Menu,
  Text,
} from '@mantine/core';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
  IconCalendarCheck,
  IconChevronDown,
  IconLogout,
  IconUser,
} from '@tabler/icons-react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { logout } from '../api/auth';
import { useAuth } from '../context/AuthContext';

export function AppHeader() {
  const location = useLocation();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { isAuthenticated, requestLogin, setAuthenticated } = useAuth();

  const logoutMutation = useMutation({
    mutationFn: logout,
    onSuccess: () => {
      setAuthenticated(false);
      queryClient.removeQueries({ queryKey: ['reservations'] });
      navigate('/');
    },
  });

  return (
    <header className="app-header">
      <Container size="xl" className="header-inner">
        <Link to="/" className="brand">
          <img
            src="/favicon.svg"
            width={38}
            height={38}
            alt=""
            className="brand-mark"
          />
          <div>
            <Text fw={900} size="lg" lh={1}>
              트립키
            </Text>
            <Text size="xs" c="dimmed" mt={4}>
              tripkey.shop
            </Text>
          </div>
        </Link>

        <Group gap="xs">
          {isAuthenticated ? (
            <Menu position="bottom-end" shadow="md" width={180}>
              <Menu.Target>
                <Button
                  variant="subtle"
                  color="dark"
                  leftSection={<IconUser size={17} />}
                  rightSection={<IconChevronDown size={14} />}
                >
                  내 메뉴
                </Button>
              </Menu.Target>
              <Menu.Dropdown>
                <Menu.Item
                  leftSection={<IconCalendarCheck size={17} />}
                  onClick={() => navigate('/reservations')}
                >
                  내 예약
                </Menu.Item>
                <Menu.Divider />
                <Menu.Item
                  color="red"
                  leftSection={<IconLogout size={17} />}
                  onClick={() => logoutMutation.mutate()}
                >
                  로그아웃
                </Menu.Item>
              </Menu.Dropdown>
            </Menu>
          ) : (
            <>
              <Button
                visibleFrom="sm"
                variant={location.pathname === '/reservations' ? 'light' : 'subtle'}
                color="dark"
                leftSection={<IconCalendarCheck size={17} />}
                onClick={() => navigate('/reservations')}
              >
                내 예약
              </Button>
              <Button color="teal" onClick={() => requestLogin()}>
                로그인
              </Button>
            </>
          )}
        </Group>
      </Container>
    </header>
  );
}
