import '@mantine/core/styles.css';
import '@mantine/notifications/styles.css';
import './styles.css';

import {
  createTheme,
  MantineProvider,
  type MantineColorsTuple,
} from '@mantine/core';
import { Notifications } from '@mantine/notifications';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App';

const brand: MantineColorsTuple = [
  '#e9f6f2',
  '#d8ebe5',
  '#acd6c9',
  '#7dbfaa',
  '#56aa90',
  '#3d9c7f',
  '#2d9476',
  '#1d8165',
  '#0e7358',
  '#006349',
];

const theme = createTheme({
  primaryColor: 'brand',
  colors: { brand },
  fontFamily:
    'Pretendard, "Noto Sans KR", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
  headings: {
    fontFamily:
      'Pretendard, "Noto Sans KR", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    fontWeight: '800',
  },
  defaultRadius: 'md',
  cursorType: 'pointer',
});

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <MantineProvider theme={theme}>
        <Notifications position="top-right" />
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </MantineProvider>
    </QueryClientProvider>
  </StrictMode>,
);
