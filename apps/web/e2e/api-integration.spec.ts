import { test, expect } from '@playwright/test';

test.describe('Integração de API', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForURL('/dashboard');
  });

  test('deve carregar Audit Logs da API', async ({ page }) => {
    await page.goto('/audit-logs');
    await expect(page.locator('text=Audit Logs')).toBeVisible();
    await expect(page.locator('table')).toBeVisible();
  });

  test('deve carregar Documents da API', async ({ page }) => {
    await page.goto('/documents');
    await expect(page.locator('text=Documentos')).toBeVisible();
    await expect(page.locator('table')).toBeVisible();
  });

  test('deve carregar Lançamentos Pendentes da API', async ({ page }) => {
    await page.goto('/entries-pending');
    await expect(page.locator('text=Lançamentos Pendentes')).toBeVisible();
    await expect(page.locator('table')).toBeVisible();
  });

  test('deve carregar Gestão de Usuários da API', async ({ page }) => {
    await page.goto('/admin/users');
    await expect(page.locator('text=Gestão de Usuários')).toBeVisible();
    await expect(page.locator('table')).toBeVisible();
  });

  test('deve carregar Base de Conhecimento da API', async ({ page }) => {
    await page.goto('/knowledge');
    await expect(page.locator('text=Base de Conhecimento')).toBeVisible();
    await expect(page.locator('text=Artigos')).toBeVisible();
  });
});
