import { useQuery, useQueryClient } from '@tanstack/react-query';
import {
  useCallback,
  type PropsWithChildren,
} from 'react';
import { adminLogout, getAdminSession } from '../api/auth';
import { AdminAuthContext } from './adminAuth';

export function AdminAuthProvider({ children }: PropsWithChildren) {
  const queryClient = useQueryClient();
  const sessionQuery = useQuery({
    queryKey: ['admin-session'],
    queryFn: getAdminSession,
    retry: false,
  });

  const markAuthenticated = useCallback(() => {
    queryClient.setQueryData(['admin-session'], {
      authenticated: true,
      role: 'ADMIN',
    });
  }, [queryClient]);

  const logout = useCallback(async () => {
    await adminLogout();
    queryClient.clear();
  }, [queryClient]);

  return (
    <AdminAuthContext.Provider
      value={{
        authenticated: sessionQuery.isSuccess,
        checking: sessionQuery.isPending,
        markAuthenticated,
        logout,
      }}
    >
      {children}
    </AdminAuthContext.Provider>
  );
}
