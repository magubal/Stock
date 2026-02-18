import { expect, test } from '@playwright/test';

const REQUIRED_TEXTS = [
  'Stock Research ONE',
  '투자자 심리 분석',
  '시장 모니터링',
  '프로젝트 현황',
  '오늘의 공시',
  '해자 분석 대시보드',
];

const REQUIRED_LINKS = [
  'monitor_disclosures.html',
  'liquidity_stress.html',
  'crypto_trends.html',
  'moat_analysis.html',
  'idea_board.html',
];

test.describe('dashboard/index.html core regression', () => {
  test('renders core sections and monitoring links without runtime errors', async ({ page }) => {
    const pageErrors: string[] = [];
    const consoleErrors: string[] = [];

    // Avoid backend API dependency and CORS noise during static dashboard regression tests.
    await page.route('http://localhost:8000/api/v1/**', async (route) => {
      await route.fulfill({
        status: 200,
        headers: {
          'content-type': 'application/json',
          'access-control-allow-origin': '*',
        },
        body: '{}',
      });
    });

    page.on('pageerror', (err) => pageErrors.push(String(err)));
    page.on('console', (msg) => {
      if (msg.type() === 'error' && !msg.text().includes('ReactDOM.render is no longer supported')) {
        consoleErrors.push(msg.text());
      }
    });

    await page.goto('/index.html', { waitUntil: 'networkidle' });
    await page.waitForTimeout(500);

    const rootText = await page.locator('#root').innerText();
    for (const text of REQUIRED_TEXTS) {
      expect(rootText).toContain(text);
    }

    const hrefs = await page.locator('a[href]').evaluateAll((nodes) =>
      nodes.map((node) => node.getAttribute('href') || '')
    );
    for (const href of REQUIRED_LINKS) {
      expect(hrefs).toContain(href);
    }

    const cardCount = await page.locator('.dashboard-card').count();
    expect(cardCount).toBeGreaterThanOrEqual(8);

    // v2: Progress bar + active cards + view-all link
    await expect(page.locator('.project-progress-bar')).toBeVisible();

    const viewAllLink = page.getByTestId('project-status-open-default');
    await expect(viewAllLink).toHaveAttribute('href', 'project_status.html');

    await Promise.all([
      page.waitForURL('**/project_status.html'),
      viewAllLink.click(),
    ]);
    await expect(page.getByTestId('project-status-page')).toBeVisible();

    // Default filter is '개발중' — switch to '전체' to see all items including REQ-017
    const allFilterTab = page.locator('.filter-tab', { hasText: /^전체/ });
    await allFilterTab.click();

    // Select REQ-017 on detail page and verify
    const req017Row = page.getByTestId('project-status-row-REQ-017');
    await req017Row.click();
    await expect(page.getByTestId('project-status-selected-id')).toHaveText('REQ-017');

    expect(pageErrors).toEqual([]);
    expect(consoleErrors).toEqual([]);
  });
});
