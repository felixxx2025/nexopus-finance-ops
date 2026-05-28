import { test, expect } from '@playwright/test';

test.describe('Autenticação', () => {
  test('deve exibir página de login', async ({ page }) => {
    await page.goto('/login');
    await expect(page).toHaveTitle(/Nexopus Finance Ops/);
    await expect(page.locator('h1')).toContainText('Login');
  });

  test('deve validar campos obrigatórios', async ({ page }) => {
    await page.goto('/login');
    await page.click('button[type="submit"]');
    await expect(page.locator('text=Username é obrigatório')).toBeVisible();
  });

  test('deve redirecionar para dashboard após login bem-sucedido', async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'admin123');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL('/dashboard');
  });
});
