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
