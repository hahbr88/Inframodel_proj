import { createContext, useContext } from 'react';

export interface AuthContextValue {
  isAuthenticated: boolean;
  setAuthenticated: (authenticated: boolean) => void;
  requestLogin: (afterLogin?: () => void) => void;
}

export const AuthContext = createContext<AuthContextValue | null>(null);

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used inside AuthContext.Provider');
  }
  return context;
}
