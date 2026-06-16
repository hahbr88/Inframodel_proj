import { Alert, Button, Modal, PasswordInput, Stack, TextInput } from '@mantine/core';
import { useForm } from '@mantine/form';
import { useMutation } from '@tanstack/react-query';
import { IconLogin2 } from '@tabler/icons-react';
import { login } from '../api/auth';
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
    </Modal>
  );
}
