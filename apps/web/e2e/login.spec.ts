import { test, expect } from '@playwright/test';

test.describe('Login Flow', () => {
  test('should display login page', async ({ page }) => {
    await page.goto('/login');
    await expect(page).toHaveTitle(/Login/);
    await expect(page.locator('input[name="username"]')).toBeVisible();
    await expect(page.locator('input[name="password"]')).toBeVisible();
  });

  test('should login with valid credentials', async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'admin123');
    await page.click('button[type="submit"]');
    
    // Should redirect to dashboard
    await expect(page).toHaveURL(/dashboard/);
  });

  test('should show error with invalid credentials', async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[name="username"]', 'invalid');
    await page.fill('input[name="password"]', 'invalid');
    await page.click('button[type="submit"]');
    
    // Should show error message
    await expect(page.locator('text=credenciais inválidas')).toBeVisible();
  });
});

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/login');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForURL(/dashboard/);
  });

  test('should display dashboard', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('Dashboard');
  });

  test('should navigate to documents page', async ({ page }) => {
    await page.click('text=Documentos');
    await expect(page).toHaveURL(/documents/);
  });
});
