import { expect, test } from '@playwright/test';

test.describe('project_status.html interactions', () => {
  test('renders summary and updates detail/checklist when list item is clicked', async ({ page }) => {
    await page.goto('/project_status.html?filter=all', { waitUntil: 'networkidle' });

    await expect(page.getByTestId('project-status-page')).toBeVisible();
    await expect(page.getByTestId('project-status-count-total')).toHaveText('3');
    await expect(page.getByTestId('project-status-count-completed')).toHaveText('2');
    await expect(page.getByTestId('project-status-count-in-progress')).toHaveText('1');
    await expect(page.getByTestId('project-status-count-pending')).toHaveText('0');

    await page.getByTestId('project-status-row-REQ-015').click();
    await expect(page.getByTestId('project-status-selected-id')).toHaveText('REQ-015');
    await expect(page.getByTestId('project-status-program-list')).toContainText('extract_moat_data.py');
    await expect(page.getByTestId('project-status-checklist-list')).toContainText('엑셀 원문 기준 파서 반영');
  });

  test('supports req query parameter preselection', async ({ page }) => {
    await page.goto('/project_status.html?req=REQ-017', { waitUntil: 'networkidle' });

    await expect(page.getByTestId('project-status-selected-id')).toHaveText('REQ-017');
    await expect(page.getByTestId('project-status-program-list')).toContainText('dashboard/project_status.html');
    await expect(page.getByTestId('project-status-checklist-list')).toContainText('문서/로그 반영 후 운영 반영');
  });
});
