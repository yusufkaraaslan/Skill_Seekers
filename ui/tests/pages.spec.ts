import { test, expect } from '@playwright/test';

const skills = [{ id: 'sk-1', name: 'react-docs', dir: '/ws/output/react-docs', description: 'React 19 reference', scope: 'global', installs: ['claude'], source: 'https://react.dev', sourceType: 'docs', version: '1.2.0', sizeKb: 1400, updatedAt: '2026-09-12', quality: 91, tags: [], origin: 'seeker', editable: true }];
const clis = ['claude', 'codex'].map(id => ({ id, name: id, short: id.slice(0, 3).toUpperCase(), color: '187 92% 50%', version: '1', globalPath: `/home/t/.${id}/skills`, detected: true, skillCount: 1 }));
const payloads: Record<string, unknown> = {
  '/api/overview': { skills, jobs: [], projects: [], clis, activity: [], mcpToolCount: 40 },
  '/api/library': { sources: [], entries: [{ id: 'cfg-1', name: 'react.json', path: '/ws/configs/react.json', framework: 'react', origin: 'preset', source: 'official', version: '2.1', sources: 'documentation', description: '', status: 'ready', usedIn: [], fetched: true }], workflows: [] },
  '/api/settings': { clis, keys: [], defaults: { default_agent: 'claude', output_dir: 'output', configs_dir: 'configs' }, root: '/ws', capabilities: { targets: ['claude', 'markdown'], agents: ['claude', 'kimi'] } },
  '/api/marketplaces': { markets: [], skills: [] },
  '/api/skills/sk-1/detail': { ...skills[0], fileCount: 86, config: 'configs/react.json', qualityBreakdown: [{ label: 'frontmatter', score: 100 }], installations: [{ cli: 'claude', path: '/home/t/.claude/skills/react-docs', owned: 'true' }], enhanceStatus: null, analysis: [] },
  '/api/skills/sk-1/history': [],
  '/api/skills/sk-1/content': { content: '# react-docs\nEND', revision: 'r1', files: [] },
  '/api/configs/cfg-1': { id: 'cfg-1', name: 'react.json', path: '/ws/configs/react.json', source: 'official', origin: 'preset', framework: 'react', version: '2.1', data: { name: 'react', sources: [] }, revision: 'c1', validation: { valid: true, errors: [], warnings: [] }, usedBy: [{ id: 'sk-1', name: 'react-docs' }], sync: null, syncSettings: null, lastEstimate: null },
  '/api/workflows': [{ name: 'default', origin: 'bundled', file: 'bundled/default.yaml', yaml: 'name: default\nstages: []', steps: 4, description: 'Balanced', validation: { valid: true, error: null } }],
  '/api/analyze/recent': [],
  '/api/environment': { doctor: { checks: [{ name: 'Python', ok: true, level: 'ok', found: '3.14', hint: '', fix: '' }], ranAt: 'now' }, servers: [{ id: 'mcp-stdio', name: 'MCP · stdio', address: 'python -m …', state: 'installed', jobId: null }, { id: 'mcp-http', name: 'MCP · HTTP', address: 'http://127.0.0.1:8000/sse', state: 'stopped', jobId: null }, { id: 'embedding', name: 'Embedding server', address: 'http://127.0.0.1:8001', state: 'stopped', jobId: null }], agents: [{ id: 'claude', name: 'Claude Code', short: 'CLA', color: '24 85% 60%', detected: true, version: '2', skillInstalled: false, agentDir: '/home/t/.claude/skills' }] },
  '/api/mcp/tools': { tools: [], count: 0 },
  '/api/mcp/status': { stdio: { state: 'installed', command: 'x' }, http: { state: 'down', host: '127.0.0.1', port: 8000, url: 'http://127.0.0.1:8000/sse' } },
};

test.beforeEach(async ({ page }) => {
  await page.route('**/api/**', route => {
    const path = new URL(route.request().url()).pathname;
    return route.fulfill({ json: payloads[path] ?? { ok: true } });
  });
});

test('skills table opens the routed skill page, not a drawer', async ({ page }) => {
  await page.goto('/skills');
  await page.getByRole('button', { name: 'react-docs', exact: true }).click();
  await expect(page).toHaveURL(/\/skills\/sk-1$/);
  await expect(page.getByRole('heading', { name: 'react-docs' })).toBeVisible();
  await expect(page.getByRole('dialog')).toHaveCount(0);
});

test('new sections are routable and mcp redirects to environment', async ({ page }) => {
  for (const [path, heading] of [['/configs/cfg-1', 'react.json'], ['/workflows', 'Enhancement workflows'], ['/analyze', 'Analyze a codebase'], ['/environment', 'Doctor']]) {
    await page.goto(path);
    await expect(page.getByRole('heading', { name: heading })).toBeVisible();
  }
  await page.goto('/mcp');
  await expect(page).toHaveURL(/\/environment$/);
  await expect(page.getByRole('navigation', { name: 'Main navigation' }).getByRole('button')).toHaveCount(11);
});

test('skill page tabs cover enhance, analysis, export and history', async ({ page }) => {
  let uploaded: unknown = null;
  await page.route('**/api/skills/sk-1/upload', route => { uploaded = route.request().postDataJSON(); return route.fulfill({ json: { ok: true, job: { id: 'u' } } }); });
  await page.goto('/skills/sk-1');
  await page.getByRole('tab', { name: 'Export' }).click();
  await page.getByRole('radio', { name: 'ChromaDB' }).check();
  await page.getByRole('textbox', { name: 'persist directory' }).fill('./chroma_db');
  await page.getByRole('button', { name: /Export to ChromaDB/ }).click();
  await expect.poll(() => uploaded).toEqual({ target: 'chroma', options: { persist_directory: './chroma_db' } });
  await page.getByRole('tab', { name: 'Enhance' }).click();
  await expect(page.getByRole('button', { name: 'Run enhancement' })).toBeVisible();
  await page.getByRole('tab', { name: 'Installs' }).click();
  await expect(page.getByText('/home/t/.claude/skills/react-docs')).toBeVisible();
  await page.getByRole('tab', { name: 'History' }).click();
  await expect(page.getByText('No jobs have touched this skill yet.')).toBeVisible();
});

test('editor loads full content and preserves a conflicted draft', async ({ page }) => {
  await page.route('**/api/skills/sk-1/content', route => route.request().method() === 'PUT'
    ? route.fulfill({ status: 409, json: { detail: 'Skill changed since it was opened; reload before saving' } })
    : route.fulfill({ json: { content: '# Full text\nEND OF DOCUMENT', revision: 'revision-1', files: [] } }));
  await page.goto('/skills/sk-1');
  await page.getByRole('tab', { name: 'SKILL.md' }).click();
  await expect(page.getByText(/END OF DOCUMENT/)).toBeVisible();
  await page.getByRole('button', { name: 'Edit', exact: true }).click();
  const editor = page.getByRole('textbox', { name: 'SKILL.md content' });
  await editor.fill('My unsaved edit');
  await page.getByRole('button', { name: 'Save', exact: true }).click();
  await expect(page.getByText(/Skill changed since/)).toBeVisible();
  await expect(editor).toHaveValue('My unsaved edit');
});

test('vector export only offers the databases upload can reach', async ({ page }) => {
  let uploaded: unknown = null;
  await page.route('**/api/skills/sk-1/upload', route => { uploaded = route.request().postDataJSON(); return route.fulfill({ json: { ok: true, job: { id: 'u' } } }); });
  await page.goto('/skills/sk-1');
  await page.getByRole('tab', { name: 'Export' }).click();
  // FAISS and Qdrant have no uploading adaptor — offering them queues a job that
  // dies in argparse.
  await expect(page.getByRole('radio', { name: 'FAISS' })).toBeDisabled();
  await expect(page.getByRole('radio', { name: 'Qdrant' })).toBeDisabled();
  await page.getByRole('radio', { name: 'Weaviate' }).check();
  await page.getByRole('textbox', { name: 'cluster url' }).fill('http://localhost:8080');
  await page.getByRole('button', { name: /Export to Weaviate/ }).click();
  // weaviate_url, not cluster_url: the adaptor only reads cluster_url on its
  // Weaviate Cloud branch.
  await expect.poll(() => uploaded).toEqual({ target: 'weaviate', options: { weaviate_url: 'http://localhost:8080' } });
});

test('skill history opens the worker log of a failed job', async ({ page }) => {
  await page.route('**/api/skills/sk-1/history', route => route.fulfill({ json: [{ id: 'job-9', type: 'enhance', label: 'react-docs', detail: 'level 2 · claude', progress: 40, status: 'failed', startedAt: '2026-09-13 09:02:40', log: ['line one', '\u2717 failed'], error: 'agent exited 1', artifacts: [] }] }));
  await page.goto('/skills/sk-1');
  await page.getByRole('tab', { name: 'History' }).click();
  await expect(page.getByText('line one')).toBeVisible();
});

test('config page validates, edits with revision, and toggles sync', async ({ page }) => {
  let saved: unknown = null; let sync: unknown = null;
  await page.route('**/api/configs/cfg-1', route => route.request().method() === 'PUT' ? (saved = route.request().postDataJSON(), route.fulfill({ json: { ok: true, revision: 'c2' } })) : route.fulfill({ json: payloads['/api/configs/cfg-1'] }));
  await page.route('**/api/configs/cfg-1/sync', route => { sync = route.request().postDataJSON(); return route.fulfill({ json: { ok: true, syncSettings: sync } }); });
  await page.goto('/configs/cfg-1');
  await page.getByRole('tab', { name: 'JSON' }).click();
  await page.getByRole('button', { name: 'Edit', exact: true }).click();
  await page.getByRole('textbox', { name: 'Config JSON' }).fill('{"name":"react","sources":[],"description":"edited"}');
  await page.getByRole('button', { name: 'Save', exact: true }).click();
  await expect.poll(() => saved).toEqual({ data: { name: 'react', sources: [], description: 'edited' }, revision: 'c1' });
  await page.getByRole('tab', { name: 'Sync' }).click();
  await page.getByRole('switch', { name: 'Watch upstream docs for changes' }).click();
  await expect.poll(() => sync).toMatchObject({ enabled: true, interval: 'daily' });
  await page.getByRole('tab', { name: 'Validate' }).click();
  await expect(page.getByText(/valid/i).first()).toBeVisible();
});

// The skill page packs eight tabs of tables, chip rows and card grids into the
// same column the nav sections use; every one of them has to fit the narrow
// viewports hud.spec.ts pins for the rest of the HUD.
for (const width of [390, 768]) {
  test(`skill page tabs fit ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    const errors: string[] = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto('/skills/sk-1');
    for (const name of ['Overview', 'SKILL.md', 'Files', 'Installs', 'Enhance', 'Analysis', 'Export', 'History']) {
      await page.getByRole('tab', { name }).click();
      const delta = await page.locator('main').evaluate(el => el.scrollWidth - el.clientWidth);
      expect(delta, `${name} tab overflows by ${delta}px`).toBeLessThanOrEqual(0);
    }
    expect(errors).toEqual([]);
  });
}
