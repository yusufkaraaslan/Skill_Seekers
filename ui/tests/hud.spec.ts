import { test, expect } from '@playwright/test';
import type { Page } from '@playwright/test';

const clis = ['claude', 'kimi', 'cursor', 'codex', 'windsurf'].map(id => ({ id, name: id, short: id.toUpperCase(), color: '187 92% 50%', version: '1.0', globalPath: `/home/test/.${id}/skills`, detected: id !== 'windsurf', skillCount: 0 }));
const skills = Array.from({ length: 60 }, (_, i) => ({ id: `sk-${i}`, name: `skill-${i}`, dir: `/workspace/output/skill-${i}`, description: 'Fixture documentation', scope: 'global', installs: [], source: 'https://example.invalid/docs', sourceType: 'docs', version: '1', sizeKb: 30, updatedAt: '2026-09-13', quality: 80, tags: [], origin: 'seeker', editable: true }));
const jobs = Array.from({ length: 60 }, (_, i) => ({ id: `job-${i}`, type: 'create', label: `Build ${i}`, detail: 'Fixture job', progress: 100, status: i === 0 ? 'running' : 'done', startedAt: '2026-09-13 12:34:56', log: ['Fixture log'], artifacts: i === 1 ? ['/workspace/output/skill', '/workspace/output/skill.zip'] : [], downloadableArtifacts: [1] }));
const sources = [{ id: 'official', name: 'official-registry', repo: 'https://example.invalid', kind: 'official', branch: 'main', configs: 2, lastFetch: 'live', autoSync: true, enabled: true, connected: true }];
const entries = ['official', 'local'].map(source => ({ id: `cfg-${source}`, name: `${source}.json`, path: `/configs/${source}.json`, framework: source, origin: 'synced', source, version: '1', sources: 'documentation', description: 'Fixture config', status: 'ready', usedIn: [], fetched: true }));
const payloads: Record<string, unknown> = {
  '/api/overview': { skills, jobs, projects: [], clis, activity: [], mcpToolCount: 1 },
  '/api/library': { sources, entries, workflows: [] },
  '/api/settings': { clis, keys: [], defaults: { default_agent: 'kimi', output_dir: 'custom-output', configs_dir: 'custom-configs' }, root: '/workspace', capabilities: { targets: ['claude', 'markdown'], agents: ['claude', 'kimi'] } },
  '/api/marketplaces': { markets: [], skills: [] },
  '/api/workflows': [{ name: 'default', origin: 'bundled', file: 'bundled/default.yaml', yaml: 'name: default\nstages: []', steps: 4, description: 'Balanced', validation: { valid: true, error: null } }],
  '/api/analyze/recent': [],
  '/api/environment': { doctor: { checks: [{ name: 'Python', ok: true, level: 'ok', found: '3.14', hint: '', fix: '' }], ranAt: '2026-09-13 12:34:56' }, servers: [], agents: [] },
  '/api/mcp/tools': { tools: [{ name: 'extract_config_patterns', category: 'Extended', desc: 'Extract patterns' }], count: 1 },
  '/api/mcp/status': { stdio: { state: 'installed', command: 'skill-seekers-mcp' }, http: { state: 'down', host: '127.0.0.1', port: 8000, url: 'http://127.0.0.1:8000/sse' } },
};
async function nav(page: Page, name: string) {
  const open = page.getByRole('button', { name: 'Open navigation', exact: true });
  if (await open.isVisible()) await open.click();
  await page.getByRole('navigation', { name: 'Main navigation' }).getByRole('button', { name: new RegExp(`^${name}`) }).click();
}
test.beforeEach(async ({ page }) => {
  await page.route('**/api/**', route => {
    const path = new URL(route.request().url()).pathname;
    const body = payloads[path] ?? (path.endsWith('/content') ? { content: '# Complete document\nEND OF DOCUMENT', revision: 'revision-1' } : { ok: true });
    return route.fulfill({ json: body });
  });
});

test('direct routes, browser history, and create drafts survive navigation', async ({ page }) => {
  await page.goto('/create');
  const input = page.getByRole('textbox', { name: /source 1/ });
  await input.fill('https://example.invalid/draft');
  await nav(page, 'Skills');
  await expect(page).toHaveURL(/\/skills$/);
  await page.goBack();
  await expect(input).toHaveValue('https://example.invalid/draft');
  await page.reload();
  await expect(input).toHaveValue('https://example.invalid/draft');
});

test('official filter uses source identity and skills paginate', async ({ page }) => {
  await page.goto('/library');
  await expect(page.locator('tbody tr')).toHaveCount(2);
  await page.getByText('official-registry', { exact: true }).click();
  await expect(page.locator('tbody tr')).toHaveCount(1);
  await expect(page.locator('tbody')).toContainText('official.json');
  await nav(page, 'Skills');
  await expect(page.locator('tbody tr')).toHaveCount(25);
  await page.getByRole('button', { name: 'Next page' }).click();
  await expect(page.locator('tbody')).toContainText('skill-25');
});

test('failed project submission keeps dialog and input', async ({ page }) => {
  await page.route('**/api/projects', route => route.fulfill({ status: 400, json: { detail: 'Directory unavailable' } }));
  await page.goto('/projects');
  await page.getByRole('button', { name: /add project/i }).click();
  const dialog = page.getByRole('dialog');
  await dialog.getByRole('textbox').fill('/missing/project');
  await dialog.getByRole('button', { name: /scan/i }).click();
  await expect(page.getByText('Directory unavailable', { exact: true })).toBeVisible();
  await expect(dialog).toBeVisible();
  await expect(dialog.getByRole('textbox')).toHaveValue('/missing/project');
});

test('job history, timestamps, cancellation, and only file download links', async ({ page }) => {
  let cancelled = false;
  await page.route('**/api/jobs/job-0/cancel', route => { cancelled = true; return route.fulfill({ json: { ok: true } }); });
  await page.goto('/jobs');
  await expect(page.locator('main')).toContainText('60 retained jobs');
  await expect(page.locator('time').first()).toHaveText('2026-09-13 12:34:56');
  await expect(page.getByRole('link', { name: 'Download file' })).toHaveCount(1);
  await page.getByRole('button', { name: 'Cancel', exact: true }).click();
  await expect.poll(() => cancelled).toBe(true);
  await page.getByRole('button', { name: 'Next page' }).click();
  await expect(page.getByText('Build 25', { exact: true })).toBeVisible();
});

for (const width of [390, 768, 1024]) {
  test(`all screens fit viewport at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    await page.emulateMedia({ reducedMotion: 'reduce' });
    const errors: string[] = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto('/');
    for (const name of ['Overview', 'Skills', 'Create', 'Projects', 'Marketplace', 'Configs', 'Workflows', 'Analyze', 'Environment', 'Jobs', 'Settings']) {
      await nav(page, name);
      await expect(page.locator('main')).not.toContainText('Loading screen');
      const widthDelta = await page.locator('main').evaluate(el => el.scrollWidth - el.clientWidth);
      expect(widthDelta, `${name} overflows horizontally`).toBeLessThanOrEqual(1);
    }
    expect(errors).toEqual([]);
  });
}

test('install dialog only offers detected CLIs', async ({ page }) => {
  await page.goto('/skills');
  await page.getByRole('button', { name: 'Actions for skill-0', exact: true }).click();
  await page.getByRole('menuitem', { name: /Port to CLI/ }).click();
  const options = page.getByRole('dialog').locator('#install-cli option');
  await expect(options).toHaveCount(4);
  await expect(options.filter({ hasText: 'windsurf' })).toHaveCount(0);
});

test('a mutation refetches after an in-flight poll instead of keeping stale rows', async ({ page }) => {
  let overviewCalls = 0;
  let deleted = false;
  await page.route('**/api/overview', async route => {
    overviewCalls += 1;
    // Snapshot BEFORE delaying so a slow poll really carries pre-mutation data.
    // No running jobs: polling is 10 s apart, so only an explicit post-mutation
    // refetch can remove the row inside the assertion window.
    const body = { ...(payloads['/api/overview'] as object), jobs: [], skills: deleted ? skills.slice(1) : skills };
    if (overviewCalls > 1) await new Promise(resolve => setTimeout(resolve, 1000));
    await route.fulfill({ json: body });
  });
  await page.route('**/api/skills/delete', route => { deleted = true; return route.fulfill({ json: { ok: true } }); });
  await page.goto('/skills');
  await page.waitForRequest(request => request.url().endsWith('/api/overview') && overviewCalls === 2);
  await page.getByRole('button', { name: 'Actions for skill-0', exact: true }).click();
  await page.getByRole('menuitem', { name: 'Delete' }).click();
  await page.getByRole('alertdialog').getByRole('button', { name: 'Delete', exact: true }).click();
  const row = page.getByRole('button', { name: 'skill-0', exact: true });
  await expect(row).toHaveCount(0, { timeout: 6000 });
  await page.waitForTimeout(2000);
  await expect(row).toHaveCount(0);
});
