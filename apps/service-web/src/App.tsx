import { useCallback, useMemo, useRef, useState } from 'react';
import { Route, Routes } from 'react-router-dom';
import { AppHeader } from './components/AppHeader';
import { LoginModal } from './components/LoginModal';
import { AuthContext } from './context/AuthContext';
import { CourseCatalogPage } from './pages/CourseCatalogPage';
import { ReservationsPage } from './pages/ReservationsPage';

export default function App() {
  const [isAuthenticated, setAuthenticated] = useState(false);
  const [loginOpened, setLoginOpened] = useState(false);
  const afterLoginRef = useRef<(() => void) | null>(null);

  const requestLogin = useCallback((afterLogin?: () => void) => {
    afterLoginRef.current = afterLogin ?? null;
    setLoginOpened(true);
  }, []);

  const handleLoginSuccess = useCallback(() => {
    setAuthenticated(true);
    setLoginOpened(false);
    const pendingAction = afterLoginRef.current;
    afterLoginRef.current = null;
    pendingAction?.();
  }, []);

  const authValue = useMemo(
    () => ({
      isAuthenticated,
      setAuthenticated,
      requestLogin,
    }),
    [isAuthenticated, requestLogin],
  );

  return (
    <AuthContext.Provider value={authValue}>
      <AppHeader />
      <Routes>
        <Route path="/" element={<CourseCatalogPage />} />
        <Route path="/reservations" element={<ReservationsPage />} />
      </Routes>
      <LoginModal
        opened={loginOpened}
        onClose={() => setLoginOpened(false)}
        onSuccess={handleLoginSuccess}
      />
    </AuthContext.Provider>
  );
}
