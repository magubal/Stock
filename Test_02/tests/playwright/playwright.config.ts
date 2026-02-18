import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  timeout: 30_000,
  expect: {
    timeout: 5_000,
  },
  fullyParallel: false,
  retries: 0,
  workers: 1,
  reporter: [['list']],
  use: {
    baseURL: 'http://127.0.0.1:18080',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'off',
    viewport: { width: 1440, height: 900 },
  },
  webServer: {
    command: 'python -m http.server 18080 --bind 127.0.0.1 --directory ../../dashboard',
    url: 'http://127.0.0.1:18080/index.html',
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
});

