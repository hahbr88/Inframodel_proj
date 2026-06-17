import {
  Alert,
  Button,
  Modal,
  PasswordInput,
  Stack,
  Tabs,
  TextInput,
} from '@mantine/core';
import { useForm } from '@mantine/form';
import { useMutation } from '@tanstack/react-query';
import { IconLogin2, IconUserPlus } from '@tabler/icons-react';
import { useState } from 'react';
import { login, signup } from '../api/auth';
import { getApiErrorMessage } from '../api/client';

interface LoginModalProps {
  opened: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export function LoginModal({
  opened,
  onClose,
  onSuccess,
}: LoginModalProps) {
  const [activeTab, setActiveTab] = useState<string | null>('login');
  const form = useForm({
    initialValues: {
      username: 'admin',
      password: '',
    },
    validate: {
      username: (value) => (value.trim() ? null : '아이디를 입력해 주세요.'),
      password: (value) =>
        value.length >= 8 ? null : '비밀번호는 8자 이상이어야 합니다.',
    },
  });

  const loginMutation = useMutation({
    mutationFn: login,
    onSuccess: () => {
      form.reset();
      onSuccess();
    },
  });

  const signupForm = useForm({
    initialValues: {
      username: '',
      password: '',
    },
    validate: {
      username: (value) =>
        value.trim().length >= 3 ? null : '아이디는 3자 이상이어야 합니다.',
      password: (value) =>
        value.length >= 8 ? null : '비밀번호는 8자 이상이어야 합니다.',
    },
  });

  const signupMutation = useMutation({
    mutationFn: signup,
    onSuccess: () => {
      signupForm.reset();
      onSuccess();
    },
  });

  return (
    <Modal
      opened={opened}
      onClose={onClose}
      title="트립키 로그인"
      centered
      radius="lg"
      size="sm"
      zIndex={1000}
    >
      <Tabs value={activeTab} onChange={setActiveTab} keepMounted={false}>
        <Tabs.List grow mb="md">
          <Tabs.Tab value="login">로그인</Tabs.Tab>
          <Tabs.Tab value="signup">회원가입</Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value="login">
          <form
            onSubmit={form.onSubmit((values) => loginMutation.mutate(values))}
          >
            <Stack>
              <TextInput
                label="아이디"
                placeholder="아이디"
                autoComplete="username"
                {...form.getInputProps('username')}
              />
              <PasswordInput
                label="비밀번호"
                placeholder="비밀번호"
                autoComplete="current-password"
                {...form.getInputProps('password')}
              />
              {loginMutation.isError && (
                <Alert color="red" variant="light">
                  {getApiErrorMessage(
                    loginMutation.error,
                    '아이디 또는 비밀번호를 확인해 주세요.',
                  )}
                </Alert>
              )}
              <Button
                type="submit"
                size="md"
                color="teal"
                leftSection={<IconLogin2 size={18} />}
                loading={loginMutation.isPending}
              >
                로그인
              </Button>
            </Stack>
          </form>
        </Tabs.Panel>

        <Tabs.Panel value="signup">
          <form
            onSubmit={signupForm.onSubmit((values) =>
              signupMutation.mutate(values),
            )}
          >
            <Stack>
              <TextInput
                label="아이디"
                placeholder="아이디"
                autoComplete="username"
                {...signupForm.getInputProps('username')}
              />
              <PasswordInput
                label="비밀번호"
                placeholder="비밀번호"
                autoComplete="new-password"
                {...signupForm.getInputProps('password')}
              />
              {signupMutation.isError && (
                <Alert color="red" variant="light">
                  {getApiErrorMessage(
                    signupMutation.error,
                    '회원가입 요청을 처리하지 못했습니다.',
                  )}
                </Alert>
              )}
              <Button
                type="submit"
                size="md"
                color="teal"
                leftSection={<IconUserPlus size={18} />}
                loading={signupMutation.isPending}
              >
                회원가입
              </Button>
            </Stack>
          </form>
        </Tabs.Panel>
      </Tabs>
    </Modal>
  );
}
