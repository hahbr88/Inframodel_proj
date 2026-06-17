import {
  Alert,
  Button,
  Container,
  Group,
  Menu,
  Modal,
  PasswordInput,
  Stack,
  Text,
  TextInput,
} from '@mantine/core';
import { useForm } from '@mantine/form';
import { notifications } from '@mantine/notifications';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
  IconCalendarCheck,
  IconChevronDown,
  IconKey,
  IconLogout,
  IconUser,
  IconUserX,
} from '@tabler/icons-react';
import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { changePassword, deleteAccount, logout } from '../api/auth';
import { getApiErrorMessage, isUnauthorized } from '../api/client';
import { useAuth } from '../context/AuthContext';

export function AppHeader() {
  const location = useLocation();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { isAuthenticated, requestLogin, setAuthenticated } = useAuth();
  const [passwordOpened, setPasswordOpened] = useState(false);
  const [deleteOpened, setDeleteOpened] = useState(false);

  const passwordForm = useForm({
    initialValues: {
      current_password: '',
      new_password: '',
    },
    validate: {
      current_password: (value) =>
        value.length >= 8 ? null : '현재 비밀번호를 입력해 주세요.',
      new_password: (value) =>
        value.length >= 8 ? null : '새 비밀번호는 8자 이상이어야 합니다.',
    },
  });

  const deleteForm = useForm({
    initialValues: {
      username: '',
      password: '',
    },
    validate: {
      username: (value) => (value.trim() ? null : '아이디를 입력해 주세요.'),
      password: (value) =>
        value.length >= 8 ? null : '비밀번호는 8자 이상이어야 합니다.',
    },
  });

  const logoutMutation = useMutation({
    mutationFn: logout,
    onSuccess: () => {
      setAuthenticated(false);
      queryClient.removeQueries({ queryKey: ['reservations'] });
      navigate('/');
    },
  });

  const passwordMutation = useMutation({
    mutationFn: changePassword,
    onSuccess: () => {
      passwordForm.reset();
      setPasswordOpened(false);
      notifications.show({
        color: 'teal',
        title: '비밀번호가 변경되었습니다',
        message: '다음 로그인부터 새 비밀번호를 사용하세요.',
      });
    },
    onError: (error) => {
      if (isUnauthorized(error)) {
        setAuthenticated(false);
        setPasswordOpened(false);
        requestLogin();
      }
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteAccount,
    onSuccess: () => {
      deleteForm.reset();
      setDeleteOpened(false);
      setAuthenticated(false);
      queryClient.removeQueries({ queryKey: ['reservations'] });
      notifications.show({
        color: 'teal',
        title: '회원탈퇴가 완료되었습니다',
        message: '계정 세션을 종료했습니다.',
      });
      navigate('/');
    },
    onError: (error) => {
      if (isUnauthorized(error)) {
        setAuthenticated(false);
        setDeleteOpened(false);
        requestLogin();
      }
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
                <Menu.Item
                  leftSection={<IconKey size={17} />}
                  onClick={() => setPasswordOpened(true)}
                >
                  비밀번호 변경
                </Menu.Item>
                <Menu.Divider />
                <Menu.Item
                  color="red"
                  leftSection={<IconLogout size={17} />}
                  onClick={() => logoutMutation.mutate()}
                >
                  로그아웃
                </Menu.Item>
                <Menu.Item
                  color="red"
                  leftSection={<IconUserX size={17} />}
                  onClick={() => setDeleteOpened(true)}
                >
                  회원탈퇴
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
      <Modal
        opened={passwordOpened}
        onClose={() => setPasswordOpened(false)}
        title="비밀번호 변경"
        centered
        size="sm"
      >
        <form
          onSubmit={passwordForm.onSubmit((values) =>
            passwordMutation.mutate(values),
          )}
        >
          <Stack>
            <PasswordInput
              label="현재 비밀번호"
              autoComplete="current-password"
              {...passwordForm.getInputProps('current_password')}
            />
            <PasswordInput
              label="새 비밀번호"
              autoComplete="new-password"
              {...passwordForm.getInputProps('new_password')}
            />
            {passwordMutation.isError && (
              <Alert color="red" variant="light">
                {getApiErrorMessage(
                  passwordMutation.error,
                  '비밀번호를 변경하지 못했습니다.',
                )}
              </Alert>
            )}
            <Button
              type="submit"
              color="teal"
              leftSection={<IconKey size={18} />}
              loading={passwordMutation.isPending}
            >
              변경
            </Button>
          </Stack>
        </form>
      </Modal>
      <Modal
        opened={deleteOpened}
        onClose={() => setDeleteOpened(false)}
        title="회원탈퇴"
        centered
        size="sm"
      >
        <form
          onSubmit={deleteForm.onSubmit((values) =>
            deleteMutation.mutate(values),
          )}
        >
          <Stack>
            <Text c="dimmed" size="sm">
              탈퇴 후 계정으로 다시 로그인할 수 없습니다.
            </Text>
            <TextInput
              label="아이디"
              autoComplete="username"
              {...deleteForm.getInputProps('username')}
            />
            <PasswordInput
              label="비밀번호"
              autoComplete="current-password"
              {...deleteForm.getInputProps('password')}
            />
            {deleteMutation.isError && (
              <Alert color="red" variant="light">
                {getApiErrorMessage(
                  deleteMutation.error,
                  '회원탈퇴를 처리하지 못했습니다.',
                )}
              </Alert>
            )}
            <Button
              type="submit"
              color="red"
              leftSection={<IconUserX size={18} />}
              loading={deleteMutation.isPending}
            >
              탈퇴
            </Button>
          </Stack>
        </form>
      </Modal>
    </header>
  );
}
