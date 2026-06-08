import { test, expect } from '@playwright/test';

test.describe('External tests', () => {
  test('has title', async ({ page }) => {
    await page.goto('https://playwright.dev/');

    // Expect a title "to contain" a substring.
    await expect(page).toHaveTitle(/Playwright/);
  });

  test('get started link', async ({ page }) => {
    await page.goto('https://playwright.dev/');

    // Click the get started link.
    await page.getByRole('link', { name: 'Get started' }).click();

    // Expects page to have a heading with the name of Installation.
    await expect(page.getByRole('heading', { name: 'Installation' })).toBeVisible();
  });
});

test.describe('LocalGPT App Tests', () => {
  // These tests require the frontend dev server running on localhost:5173
  // and the backend running on localhost:8000
  // Run with: npm run dev (from frontend/) and python main.py (from backend/)
  
  test.skip('frontend loads successfully', async ({ page }) => {
    // Skipped by default - run manually with servers
    await page.goto('http://localhost:5173/');
    await expect(page).toHaveTitle(/LocalGPT|Vite/);
  });

  test.skip('backend API health check', async ({ page }) => {
    // Skipped by default - run manually with servers
    const response = await page.request.get('http://localhost:8000/health');
    expect(response.status()).toBeLessThan(500);
  });
});
