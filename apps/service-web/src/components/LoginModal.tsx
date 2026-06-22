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

const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function validateEmail(value: string) {
  return emailPattern.test(value.trim())
    ? null
    : '이메일 형식으로 입력해 주세요.';
}

export function LoginModal({
  opened,
  onClose,
  onSuccess,
}: LoginModalProps) {
  const [activeTab, setActiveTab] = useState<string | null>('login');
  const form = useForm({
    initialValues: {
      username: '',
      password: '',
    },
    validate: {
      username: validateEmail,
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
      username: validateEmail,
      password: (value) =>
        /[A-Z]/.test(value) && value.length >= 8
          ? null
          : '비밀번호는 8자 이상이며 대문자를 포함해야 합니다.',
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
                label="이메일"
                placeholder="user@example.com"
                autoComplete="email"
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
                    '이메일 또는 비밀번호를 확인해 주세요.',
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
                label="이메일"
                placeholder="user@example.com"
                autoComplete="email"
                {...signupForm.getInputProps('username')}
              />
              <PasswordInput
                label="비밀번호"
                placeholder="8자 이상, 대문자 포함"
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
