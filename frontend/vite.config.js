import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  base: './',
  plugins: [react()],
  server: {
    port: 3000,
    host: true,
    allowedHosts: ['interpro.qzz.io', '.qzz.io'],
    proxy: {
      '/health': 'http://127.0.0.1:8000',
      '/scenarios': 'http://127.0.0.1:8000',
      '/analyze': 'http://127.0.0.1:8000',
      '/evidence': 'http://127.0.0.1:8000',
      '/evaluate': 'http://127.0.0.1:8000',
      '/ingest': 'http://127.0.0.1:8000',
    },
  },
});
