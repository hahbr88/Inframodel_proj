import { Center, Loader } from '@mantine/core';
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAdminAuth } from '../context/adminAuth';

export function ProtectedRoute() {
  const location = useLocation();
  const { authenticated, checking } = useAdminAuth();

  if (checking) {
    return (
      <Center h="100vh">
        <Loader />
      </Center>
    );
  }

  return authenticated ? (
    <Outlet />
  ) : (
    <Navigate to="/login" state={{ from: location.pathname }} replace />
  );
}
