import { test, expect } from '@playwright/test';

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    // Login antes de cada teste
    await page.goto('/login');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForURL('/dashboard');
  });

  test('deve exibir dashboard com métricas', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('Dashboard');
    await expect(page.locator('text=Total de Lançamentos')).toBeVisible();
    await expect(page.locator('text=Saldo Atual')).toBeVisible();
  });

  test('deve permitir seleção de empresa', async ({ page }) => {
    const companySelect = page.locator('[role="combobox"]').first();
    await companySelect.click();
    await expect(page.locator('[role="listbox"]')).toBeVisible();
  });

  test('deve permitir seleção de ano', async ({ page }) => {
    const yearSelect = page.locator('[role="combobox"]').nth(1);
    await yearSelect.click();
    await expect(page.locator('[role="listbox"]')).toBeVisible();
  });

  test('deve exibir botão de seed de contas quando empresa selecionada', async ({ page }) => {
    await expect(page.locator('text=Seed Contas')).toBeVisible();
  });
});
