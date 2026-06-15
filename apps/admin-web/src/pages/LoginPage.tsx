import {
  Alert,
  Button,
  Center,
  Paper,
  PasswordInput,
  Stack,
  Text,
  TextInput,
  ThemeIcon,
  Title,
} from '@mantine/core';
import { useForm } from '@mantine/form';
import { IconAlertCircle, IconShieldLock } from '@tabler/icons-react';
import { useState } from 'react';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import { adminLogin } from '../api/auth';
import { getApiErrorMessage } from '../api/client';
import { useAdminAuth } from '../context/adminAuth';

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { authenticated, markAuthenticated } = useAdminAuth();
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const form = useForm({
    initialValues: {
      username: 'admin',
      password: '',
    },
    validate: {
      username: (value) => (!value ? '아이디를 입력해 주세요.' : null),
      password: (value) =>
        value.length < 8 ? '비밀번호는 8자 이상이어야 합니다.' : null,
    },
  });

  if (authenticated) return <Navigate to="/" replace />;

  const handleSubmit = form.onSubmit(async (values) => {
    setSubmitting(true);
    setError('');
    try {
      await adminLogin(values);
      markAuthenticated();
      const from =
        (location.state as { from?: string } | null)?.from ?? '/';
      navigate(from, { replace: true });
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, '관리자 로그인에 실패했습니다.'));
    } finally {
      setSubmitting(false);
    }
  });

  return (
    <Center className="login-page">
      <Paper className="login-panel" radius="xl" p={36}>
        <ThemeIcon size={54} radius="lg" variant="gradient" mb="lg">
          <IconShieldLock size={29} />
        </ThemeIcon>
        <Title order={2}>관리자 로그인</Title>
        <Text c="dimmed" mt={8} mb="xl">
          운영 데이터와 예약 현황에 접근하려면 관리자 인증이 필요합니다.
        </Text>

        <form onSubmit={handleSubmit}>
          <Stack>
            {error && (
              <Alert color="red" icon={<IconAlertCircle size={18} />}>
                {error}
              </Alert>
            )}
            <TextInput
              label="관리자 아이디"
              placeholder="admin"
              {...form.getInputProps('username')}
            />
            <PasswordInput
              label="비밀번호"
              placeholder="8자 이상 입력"
              {...form.getInputProps('password')}
            />
            <Button type="submit" size="md" loading={submitting} mt="sm">
              관리자 로그인
            </Button>
          </Stack>
        </form>
      </Paper>
    </Center>
  );
}
