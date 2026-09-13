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
  '/api/analyze/recent': [{ slug: 'lazy-bird-1a2b3c4d', target: '~/dev/lazy-bird', tools: ['patterns', 'quality'], skipped: [], startedAt: '2026-09-13 09:40:00', attachedTo: null, results: { patterns: { count: 14, path: '/x' }, quality: { count: 91, path: '/y' } } }],
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

test('environment shows doctor, starts a server and installs the agent skill', async ({ page }) => {
  const hits: string[] = [];
  await page.route('**/api/environment/**', route => { hits.push(new URL(route.request().url()).pathname); return route.fulfill({ json: { ok: true, job: { id: 'x' } } }); });
  await page.goto('/environment');
  await expect(page.getByRole('heading', { name: 'Doctor' })).toBeVisible();
  await expect(page.getByText('3.14')).toBeVisible();
  await page.getByRole('button', { name: 'Start Embedding server' }).click();
  await page.getByRole('button', { name: 'Install skill into Claude Code' }).click();
  await expect.poll(() => hits).toEqual(['/api/environment/servers/embedding/start', '/api/environment/agents/claude/install']);
});

test('MCP failures show an error and do not offer a simulated execution', async ({ page }) => {
  await page.route('**/api/mcp/status', route => route.fulfill({ status: 503, json: { detail: 'Probe unavailable' } }));
  await page.goto('/environment');
  await expect(page.getByText(/Probe unavailable/)).toBeVisible();
  await expect(page.getByRole('button', { name: /play|try it/i })).toHaveCount(0);
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

test('sidebar navigation confirms before discarding an unsaved SKILL.md draft', async ({ page }) => {
  // BrowserRouter has no useBlocker: without the store's confirmLeave() guard
  // a click on the sidebar silently drops the draft.
  await page.goto('/skills/sk-1');
  await page.getByRole('tab', { name: 'SKILL.md' }).click();
  await page.getByRole('button', { name: 'Edit', exact: true }).click();
  const editor = page.getByRole('textbox', { name: 'SKILL.md content' });
  await editor.fill('My unsaved edit');
  const skillsNav = page.getByRole('navigation', { name: 'Main navigation' }).getByRole('button', { name: 'Skills' });

  page.once('dialog', d => d.dismiss());
  await skillsNav.click();
  await expect(page).toHaveURL(/\/skills\/sk-1$/);
  await expect(editor).toHaveValue('My unsaved edit');

  page.once('dialog', d => d.accept());
  await skillsNav.click();
  await expect(page).toHaveURL(/\/skills$/);
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

test('sync toggle updates the stats strip and survives a tab switch', async ({ page }) => {
  let syncSettings: unknown = null;
  await page.route('**/api/configs/cfg-1', route => route.fulfill({ json: { id: 'cfg-1', name: 'react.json', path: '/ws/configs/react.json', source: 'official', origin: 'preset', framework: 'react', version: '2.1', data: { name: 'react', sources: [] }, revision: 'c1', validation: { valid: true, errors: [], warnings: [] }, usedBy: [], sync: null, syncSettings, lastEstimate: null } }));
  await page.route('**/api/configs/cfg-1/sync', route => { syncSettings = route.request().postDataJSON(); return route.fulfill({ json: { ok: true, syncSettings } }); });
  await page.goto('/configs/cfg-1');
  await page.getByRole('tab', { name: 'Sync' }).click();
  await page.getByRole('switch', { name: 'Watch upstream docs for changes' }).click();
  // No scheduler executes the interval yet, so the panel says what it really
  // did — saved the setting — instead of claiming it is watching upstream.
  await expect(page.getByText(/watch setting saved/i).first()).toBeVisible();
  await page.getByRole('tab', { name: 'JSON' }).click();
  await page.getByRole('tab', { name: 'Sync' }).click();
  await expect(page.getByRole('switch', { name: 'Watch upstream docs for changes' })).toBeChecked();
});

test('json edits ask before discarding on tab change', async ({ page }) => {
  await page.goto('/configs/cfg-1');
  await page.getByRole('tab', { name: 'JSON' }).click();
  await page.getByRole('button', { name: 'Edit', exact: true }).click();
  const editor = page.getByRole('textbox', { name: 'Config JSON' });
  await editor.fill('{"name":"changed","sources":[]}');
  page.once('dialog', d => d.dismiss());
  await page.getByRole('tab', { name: 'Validate' }).click();
  await expect(editor).toHaveValue('{"name":"changed","sources":[]}');
});

test('library generates a config with AI from a docs URL', async ({ page }) => {
  let generated: unknown = null;
  await page.route('**/api/configs/generate', route => { generated = route.request().postDataJSON(); return route.fulfill({ json: { ok: true, job: { id: 'g1' } } }); });
  await page.goto('/configs');
  await page.getByRole('button', { name: 'Generate with AI' }).click();
  await page.getByRole('textbox', { name: 'Docs URL' }).fill('https://docs.example.com/start');
  await page.getByRole('button', { name: 'Generate config' }).click();
  await expect.poll(() => generated).toEqual({ kind: 'url', value: 'https://docs.example.com/start', probe_urls: true });
  await expect(page.getByRole('dialog')).toHaveCount(0);
});

test('workflows list selects and copies a bundled workflow', async ({ page }) => {
  let copied = false;
  await page.route('**/api/workflows/default/copy', route => { copied = true; return route.fulfill({ json: { ok: true } }); });
  await page.goto('/workflows');
  await page.getByRole('row', { name: /default/ }).click();
  await expect(page).toHaveURL(/\/workflows\/default$/);
  await expect(page.getByText('name: default')).toBeVisible();
  await page.getByRole('button', { name: 'Copy to user dir' }).click();
  await expect.poll(() => copied).toBe(true);
});

test('workflows install dialog PUTs a new user workflow and closes on success', async ({ page }) => {
  let saved: unknown = null;
  await page.route('**/api/workflows/custom', route => { saved = route.request().postDataJSON(); return route.fulfill({ json: { ok: true, path: '/ws/workflows/custom.yaml' } }); });
  await page.goto('/workflows');
  await page.getByRole('button', { name: 'Install YAML file…' }).click();
  await page.getByRole('textbox', { name: 'Workflow name' }).fill('custom');
  await page.getByRole('textbox', { name: 'YAML' }).fill('name: custom\nstages: []');
  await page.getByRole('button', { name: 'Install', exact: true }).click();
  await expect.poll(() => saved).toEqual({ yaml: 'name: custom\nstages: []' });
  await expect(page.getByRole('dialog')).toHaveCount(0);
});

test('Use in Create waits for workspace settings before stashing the create draft', async ({ page }) => {
  await page.route('**/api/settings', async route => {
    await new Promise((resolve) => setTimeout(resolve, 1500));
    return route.fulfill({ json: payloads['/api/settings'] });
  });
  await page.goto('/workflows/default');
  const button = page.getByRole('button', { name: 'Use in Create' });
  await expect(button).toBeDisabled();
  await expect(button).toBeEnabled({ timeout: 5000 });
  await button.click();
  await expect(page).toHaveURL(/\/create$/);
  const stashed = await page.evaluate(() => sessionStorage.getItem('seeker.create./ws.workflows'));
  expect(stashed).toBe('["default"]');
});

test('analyze submits the selected tools for a directory', async ({ page }) => {
  let body: unknown = null;
  await page.route('**/api/analyze', route => { body = route.request().postDataJSON(); return route.fulfill({ json: { ok: true, job: { id: 'a' } } }); });
  await page.goto('/analyze');
  // recentAnalyses fixture round-trips through AnalysisManifest — nothing
  // exercised that type until this test.
  await expect(page.getByText('lazy-bird-1a2b3c4d')).toBeVisible();
  await page.getByRole('textbox', { name: 'local path' }).fill('~/dev/lazy-bird');
  await page.getByRole('checkbox', { name: /Design patterns/ }).check();
  await page.getByRole('checkbox', { name: /Quality check/ }).check();
  const runButton = page.getByRole('button', { name: 'Run analysis' });
  const confidence = page.getByRole('spinbutton', { name: 'Minimum confidence' });
  // The number input's min/max only constrain the spinner, not typed text —
  // a typed 2 must disable the run rather than reach the backend, which
  // rejects min_confidence outside 0-1 with a 400.
  await confidence.fill('2');
  await expect(runButton).toBeDisabled();
  await confidence.fill('0.5');
  await expect(runButton).toBeEnabled();
  await runButton.click();
  await expect.poll(() => body).toMatchObject({ target: { kind: 'dir', value: '~/dev/lazy-bird' }, tools: ['patterns', 'quality'], depth: 'basic', min_confidence: 0.5 });
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
