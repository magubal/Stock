import { expect, test } from '@playwright/test';

type Signal = {
  id: number;
  signal_id: string;
  rule_id: string;
  title: string;
  description: string;
  category: 'RISK' | 'SECTOR' | 'PORTFOLIO' | 'THEME';
  signal_type: string;
  confidence: number;
  data_sources: string[];
  evidence: Array<{ module: string; label: string; value: number | string }>;
  suggested_action: string;
  ai_interpretation: string | null;
  data_gaps: Array<{ module: string; reason: string; impact?: string }>;
  status: 'new' | 'reviewed' | 'accepted' | 'rejected';
  related_idea_id: number | null;
  expires_at: string | null;
  created_at: string;
  reviewed_at: string | null;
};

function createSeedSignals(): Signal[] {
  const now = Date.now();
  return [
    {
      id: 1,
      signal_id: 'SIG-RISK-20260218-001',
      rule_id: 'SIG-RISK',
      title: 'Liquidity stress accelerating',
      description: 'Cross-module risk signal detected',
      category: 'RISK',
      signal_type: 'cross',
      confidence: 0.84,
      data_sources: ['liquidity_stress', 'events'],
      evidence: [{ module: 'liquidity_stress', label: 'total_score', value: 78 }],
      suggested_action: 'Hedge beta and reduce leverage',
      ai_interpretation: null,
      data_gaps: [],
      status: 'new',
      related_idea_id: null,
      expires_at: null,
      created_at: new Date(now - 10 * 60 * 1000).toISOString(),
      reviewed_at: null,
    },
    {
      id: 2,
      signal_id: 'SIG-SECTOR-20260218-002',
      rule_id: 'SIG-SECTOR',
      title: 'Defensive rotation emerging',
      description: 'Sector leadership shift observed',
      category: 'SECTOR',
      signal_type: 'cross',
      confidence: 0.62,
      data_sources: ['sector_momentum', 'daily_work'],
      evidence: [{ module: 'sector_momentum', label: 'rotation_signal', value: 'XLU→XLK' }],
      suggested_action: 'Raise defensive allocation gradually',
      ai_interpretation: null,
      data_gaps: [],
      status: 'reviewed',
      related_idea_id: null,
      expires_at: null,
      created_at: new Date(now - 30 * 60 * 1000).toISOString(),
      reviewed_at: new Date(now - 20 * 60 * 1000).toISOString(),
    },
  ];
}

test.describe('dashboard/idea_board.html triage v2 smoke', () => {
  test('renders purpose + filters and handles status transition without runtime errors', async ({ page }) => {
    const pageErrors: string[] = [];
    const consoleErrors: string[] = [];
    const signals = createSeedSignals();

    const fulfillJson = async (route: any, body: unknown, status = 200) => {
      await route.fulfill({
        status,
        headers: {
          'content-type': 'application/json',
          'access-control-allow-origin': '*',
        },
        body: JSON.stringify(body),
      });
    };

    await page.route('http://localhost:8000/api/v1/signals**', async (route) => {
      const req = route.request();
      const url = new URL(req.url());
      const path = url.pathname;
      const method = req.method();

      if (path === '/api/v1/signals/generate' && method === 'POST') {
        await fulfillJson(route, {
          generated_at: new Date().toISOString(),
          signals_count: signals.length,
          signals,
        });
        return;
      }

      if (path === '/api/v1/signals' && method === 'GET') {
        const statusParam = url.searchParams.get('status');
        const categoryParam = url.searchParams.get('category');
        const minConfidenceParam = url.searchParams.get('min_confidence');
        const limitParam = Number(url.searchParams.get('limit') || '50');

        let filtered = [...signals];
        if (statusParam) {
          const statuses = statusParam.split(',').map((s) => s.trim());
          filtered = filtered.filter((s) => statuses.includes(s.status));
        }
        if (categoryParam) {
          filtered = filtered.filter((s) => s.category === categoryParam);
        }
        if (minConfidenceParam) {
          const threshold = Number(minConfidenceParam);
          filtered = filtered.filter((s) => s.confidence >= threshold);
        }

        await fulfillJson(route, {
          total: filtered.length,
          signals: filtered.slice(0, limitParam),
        });
        return;
      }

      const detailMatch = path.match(/^\/api\/v1\/signals\/(\d+)$/);
      if (detailMatch && method === 'GET') {
        const id = Number(detailMatch[1]);
        const signal = signals.find((s) => s.id === id);
        if (!signal) {
          await fulfillJson(route, { detail: 'Signal not found' }, 404);
          return;
        }
        await fulfillJson(route, signal);
        return;
      }

      const gapsMatch = path.match(/^\/api\/v1\/signals\/(\d+)\/gaps$/);
      if (gapsMatch && method === 'GET') {
        const id = Number(gapsMatch[1]);
        const signal = signals.find((s) => s.id === id);
        await fulfillJson(route, {
          signal_id: signal?.signal_id ?? '',
          gaps: {
            gaps: [],
            recommendations: [],
            enrichments: [],
          },
        });
        return;
      }

      const interpretMatch = path.match(/^\/api\/v1\/signals\/(\d+)\/interpret$/);
      if (interpretMatch && method === 'POST') {
        const id = Number(interpretMatch[1]);
        const signal = signals.find((s) => s.id === id);
        if (signal) {
          signal.ai_interpretation = JSON.stringify({
            interpretation: 'Interpretation ready',
            actions: ['Monitor leverage'],
          });
        }
        await fulfillJson(route, { ok: true });
        return;
      }

      const statusMatch = path.match(/^\/api\/v1\/signals\/(\d+)\/status$/);
      if (statusMatch && method === 'PUT') {
        const id = Number(statusMatch[1]);
        const payload = req.postDataJSON() as { status: Signal['status'] };
        const signal = signals.find((s) => s.id === id);
        if (signal) {
          signal.status = payload.status;
          signal.reviewed_at = new Date().toISOString();
          await fulfillJson(route, signal);
          return;
        }
        await fulfillJson(route, { detail: 'Signal not found' }, 404);
        return;
      }

      const acceptMatch = path.match(/^\/api\/v1\/signals\/(\d+)\/accept$/);
      if (acceptMatch && method === 'POST') {
        const id = Number(acceptMatch[1]);
        const signal = signals.find((s) => s.id === id);
        if (!signal) {
          await fulfillJson(route, { detail: 'Signal not found' }, 404);
          return;
        }
        signal.status = 'accepted';
        signal.related_idea_id = 101;
        signal.reviewed_at = new Date().toISOString();
        await fulfillJson(route, {
          signal_id: signal.signal_id,
          status: 'accepted',
          idea: {
            id: 101,
            title: `${signal.title} idea`,
          },
        });
        return;
      }

      await fulfillJson(route, { detail: 'Unhandled route' }, 404);
    });

    page.on('pageerror', (err) => pageErrors.push(String(err)));
    page.on('console', (msg) => {
      if (msg.type() === 'error' && !msg.text().includes('ReactDOM.render is no longer supported')) {
        consoleErrors.push(msg.text());
      }
    });

    await page.goto('/idea_board.html', { waitUntil: 'networkidle' });

    await expect(page.getByText('Purpose')).toBeVisible();
    await expect(page.getByText('교차 데이터 시그널을 빠르게 검토해 실제 투자 아이디어로 전환하는 전략가 데스크입니다.')).toBeVisible();
    await expect(page.locator('#filterConfidence')).toBeVisible();
    await expect(page.locator('#sortBy')).toBeVisible();
    await expect(page.locator('#filterSearch')).toBeVisible();

    await expect(page.locator('.signal-card')).toHaveCount(2);
    await expect(page.locator('#feedSummary')).toContainText('2 shown');

    await page.locator('#filterSearch').fill('Liquidity');
    await page.waitForTimeout(350);
    await expect(page.locator('.signal-card')).toHaveCount(1);

    await page.locator('.signal-card').first().click();
    await expect(page.getByText('AI Strategist Interpretation')).toBeVisible();

    await page.getByRole('button', { name: 'Mark Reviewed' }).click();
    await expect(page.locator('.signal-card .badge.badge-gray').first()).toContainText('reviewed');

    expect(pageErrors).toEqual([]);
    expect(consoleErrors).toEqual([]);
  });
});
