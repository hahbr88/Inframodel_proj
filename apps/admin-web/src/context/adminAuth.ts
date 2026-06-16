import { createContext, useContext } from 'react';

interface AdminAuthContextValue {
  authenticated: boolean;
  checking: boolean;
  markAuthenticated: () => void;
  logout: () => Promise<void>;
}

export const AdminAuthContext =
  createContext<AdminAuthContextValue | null>(null);

export function useAdminAuth() {
  const context = useContext(AdminAuthContext);
  if (!context) {
    throw new Error('useAdminAuth must be used inside AdminAuthProvider');
  }
  return context;
}
