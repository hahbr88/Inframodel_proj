import '@mantine/core/styles.css';
import '@mantine/notifications/styles.css';
import './styles.css';

import { createTheme, MantineProvider } from '@mantine/core';
import { Notifications } from '@mantine/notifications';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import { AdminAuthProvider } from './context/AdminAuthContext';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider
      client={
        new QueryClient({
          defaultOptions: {
            queries: {
              retry: false,
              refetchOnWindowFocus: false,
            },
          },
        })
      }
    >
      <MantineProvider
        theme={createTheme({
          primaryColor: 'indigo',
          fontFamily:
            'Pretendard, "Noto Sans KR", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
        })}
      >
        <Notifications position="top-right" />
        <BrowserRouter basename="/admin">
          <AdminAuthProvider>
            <App />
          </AdminAuthProvider>
        </BrowserRouter>
      </MantineProvider>
    </QueryClientProvider>
  </StrictMode>,
);
