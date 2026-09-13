// ── API client for the Seeker HUD backend (skill_seekers.web) ───────────────

const BASE = '/api';

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    signal: AbortSignal.timeout(30000),
    ...init,
  });
  if (!res.ok) {
    let detail = `${res.status}`;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {
      /* non-json error */
    }
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
  }
  return res.json() as Promise<T>;
}

const post = <T>(path: string, body?: unknown) =>
  req<T>(path, { method: 'POST', body: JSON.stringify(body ?? {}) });
const put = <T>(path: string, body: unknown) =>
  req<T>(path, { method: 'PUT', body: JSON.stringify(body) });
const del = <T>(path: string) => req<T>(path, { method: 'DELETE' });

import type {
  Activity, Cli, ConfigEntry, ConfigSource, Job, MarketSkill, Marketplace, McpTool, Project, Skill, Workflow,
} from '@/lib/data';

export interface OverviewPayload {
  skills: Skill[];
  jobs: Job[];
  clis: Cli[];
  projects: Project[];
  activity: Activity[];
  mcpToolCount: number;
}

export interface LibraryPayload {
  sources: ConfigSource[];
  entries: ConfigEntry[];
  workflows: Workflow[];
}

export interface MarketPayload {
  markets: Marketplace[];
  skills: MarketSkill[];
}

export interface SettingsPayload {
  clis: Cli[];
  keys: { name: string; set: boolean }[];
  defaults: Record<string, unknown>;
  root: string;
  capabilities: { targets: string[]; agents: string[] };
}

export interface McpStatus {
  stdio: { state: 'installed' | 'missing'; command: string };
  http: { state: 'live' | 'down'; host: string; port: number; url: string };
}

export interface CreateSpec {
  entries: { type: string; input: string }[];
  name: string;
  description: string;
  targets: string[];
  flags: Record<string, unknown>;
}

// Every endpoint that queues background work answers with the accepted job.
export interface JobAck {
  ok: boolean;
  job: Job;
}

// ── Skill detail (GET /api/skills/{id}/detail) ──────────────────────────────

export interface QualityDimension {
  label: string;
  score: number;
}

export interface AnalysisRow {
  tool: string;
  count: number | null;
  ranAt: string;
  path: string;
}

// `.enhancement_status.json` is written by the CLI and is free-form; the page
// reads known keys defensively rather than pretending a schema exists.
export type EnhanceStatus = Record<string, unknown>;

export interface SkillDetail extends Skill {
  fileCount: number;
  config: string | null;
  qualityBreakdown: QualityDimension[];
  enhanceStatus: EnhanceStatus | null;
  analysis: AnalysisRow[];
}

// ── Config detail (GET /api/configs/{id}) ───────────────────────────────────

export interface Validation {
  valid: boolean;
  errors: string[];
  warnings: string[];
}

export interface SyncSettings {
  enabled: boolean;
  interval: string;
  auto_rebuild: boolean;
}

export interface ConfigDetail {
  id: string;
  name: string;
  path: string;
  source: string;
  origin: string;
  framework: string;
  version: string;
  data: Record<string, unknown>;
  revision: string;
  validation: Validation;
  usedBy: { id: string; name: string }[];
  sync: Record<string, unknown> | null;
  syncSettings: SyncSettings | null;
  lastEstimate: Record<string, unknown> | null;
}

// ── Workflows (GET /api/workflows) ──────────────────────────────────────────

// Workflow validation reports a single parse/load error, not the config
// validator's errors+warnings lists — keep the two shapes apart.
export interface WorkflowValidation {
  valid: boolean;
  error: string | null;
}

export interface WorkflowRow {
  name: string;
  origin: 'user' | 'bundled';
  file: string;
  yaml: string;
  steps: number;
  description: string;
  validation: WorkflowValidation;
}

// ── Analyze (POST /api/analyze, GET /api/analyze/recent) ────────────────────

export interface AnalyzeBody {
  target: { kind: 'skill' | 'dir' | 'repo'; value: string };
  tools: string[];
  depth: 'basic' | 'c3x';
  min_confidence: number;
  ai_mode: 'off' | 'auto' | 'api' | 'local';
  attach_to: string | null;
}

export interface AnalysisManifest {
  slug: string;
  target: string;
  tools: string[];
  skipped: string[];
  startedAt: string;
  attachedTo: string | null;
  results: Record<string, { count: number | null; path: string }>;
}

// ── Environment (GET /api/environment) ──────────────────────────────────────

export interface DoctorCheck {
  name: string;
  ok: boolean;
  level: 'ok' | 'warning' | 'error';
  found: string;
  hint: string;
  fix: string;
}

export interface ServerRow {
  id: 'mcp-stdio' | 'mcp-http' | 'embedding';
  name: string;
  address: string;
  state: 'installed' | 'missing' | 'running' | 'live' | 'stopped';
  jobId: string | null;
}

export interface AgentRow {
  id: string;
  name: string;
  short: string;
  color: string;
  detected: boolean;
  version: string | null;
  agentDir: string;
  skillInstalled: boolean;
}

export interface EnvironmentPayload {
  doctor: { checks: DoctorCheck[]; ranAt: string };
  servers: ServerRow[];
  agents: AgentRow[];
}

export const api = {
  overview: () => req<OverviewPayload>('/overview'),
  skills: () => req<Skill[]>('/skills'),
  jobs: () => req<Job[]>('/jobs'),
  library: () => req<LibraryPayload>('/library'),
  marketplaces: () => req<MarketPayload>('/marketplaces'),
  mcpTools: () => req<{ tools: McpTool[]; count: number }>('/mcp/tools'),
  mcpStatus: () => req<McpStatus>('/mcp/status'),
  settings: () => req<SettingsPayload>('/settings'),

  create: (spec: CreateSpec) => post<{ ok: boolean; name: string }>('/create', spec),
  moveSkills: (ids: string[], dest: string) => post('/skills/move', { ids, dest }),
  deleteSkills: (ids: string[]) => post('/skills/delete', { ids }),
  portSkills: (ids: string[], cli: string, replace: boolean) =>
    post('/skills/port', { ids, cli, replace }),
  enhanceSkill: (id: string) => post(`/skills/${id}/enhance`),
  packageSkill: (id: string, targets: string[]) => post(`/skills/${id}/package`, { targets }),
  skillContent: (id: string) => req<{ content: string; revision: string; files?: { path: string; size: string }[] }>(`/skills/${id}/content`),
  saveSkillContent: (id: string, content: string, revision: string) => put(`/skills/${id}/content`, { content, revision }),
  archivedSkills: () => req<{ id: string; name: string; archivedAt: string; original: string }[]>('/skills/archived'),
  restoreSkill: (id: string) => post(`/skills/archived/${id}/restore`),
  cancelJob: (id: string) => post(`/jobs/${id}/cancel`),
  retryJob: (id: string) => post(`/jobs/${id}/retry`),

  addProject: (path: string) => post<{ project: Project }>('/projects', { path }),
  rescanProject: (id: string) => post(`/projects/${id}/rescan`),
  removeProject: (id: string) => del(`/projects/${id}`),

  addSource: (repo: string) => post('/library/sources', { repo }),
  removeSource: (name: string) => del(`/library/sources/${name}`),
  fetchSource: (name: string) => post(`/library/sources/${name}/fetch`),
  fetchOfficial: (name: string) => post('/library/official/fetch', { name }),
  buildConfig: (config_path: string) => post('/library/build', { config_path }),

  addMarketplace: (repo: string) => post('/marketplaces', { repo }),
  removeMarketplace: (name: string) => del(`/marketplaces/${name}`),
  syncMarketplaces: () => post('/marketplaces/sync'),
  installMarketItem: (path: string, kind: string, clis: string[], replace: boolean) =>
    post('/marketplaces/install', { path, kind, clis, replace }),
  publishSkill: (skill_name: string, marketplace: string) =>
    post('/marketplaces/publish', { skill_name, marketplace }),

  setKey: (name: string, value: string) => put('/settings/keys', { name, value }),
  setDefaults: (settings: Record<string, unknown>) => put('/settings/defaults', { settings }),
  reprobe: () => post<{ clis: Cli[] }>('/settings/reprobe'),

  // ── skill page ──
  skillDetail: (id: string) => req<SkillDetail>(`/skills/${id}/detail`),
  skillHistory: (id: string) => req<Job[]>(`/skills/${id}/history`),
  enhanceStatus: (id: string) => req<EnhanceStatus | null>(`/skills/${id}/enhance-status`),
  uploadSkill: (id: string, target: string, options: Record<string, string>) =>
    post<JobAck>(`/skills/${id}/upload`, { target, options }),
  translateSkill: (id: string, languages: string[]) =>
    post<JobAck>(`/skills/${id}/translate`, { languages }),
  updateSkill: (id: string, apply: boolean) => post<JobAck>(`/skills/${id}/update`, { apply }),
  qualitySkill: (id: string) => post<JobAck>(`/skills/${id}/quality`),

  // ── config page ──
  configDetail: (id: string) => req<ConfigDetail>(`/configs/${id}`),
  saveConfig: (id: string, data: unknown, revision: string) =>
    put<{ ok: boolean; revision: string }>(`/configs/${id}`, { data, revision }),
  validateConfig: (id: string) => post<Validation>(`/configs/${id}/validate`),
  estimateConfig: (id: string, body: { max_discovery: number; timeout: number }) =>
    post<JobAck>(`/configs/${id}/estimate`, body),
  splitConfig: (id: string, body: { strategy: string; target_pages: number }) =>
    post<JobAck>(`/configs/${id}/split`, body),
  pushConfig: (id: string, body: { source: string; message: string; branch: boolean }) =>
    post<JobAck>(`/configs/${id}/push`, body),
  submitConfig: (id: string, probe_urls: boolean) =>
    post<JobAck>(`/configs/${id}/submit`, { probe_urls }),
  syncCheck: (id: string) => post<JobAck>(`/configs/${id}/sync/check`),
  setSync: (id: string, body: SyncSettings) =>
    put<{ ok: boolean; syncSettings: SyncSettings }>(`/configs/${id}/sync`, body),
  generateConfig: (body: { kind: string; value: string; probe_urls: boolean }) =>
    post<JobAck>('/configs/generate', body),

  // ── workflows ──
  workflows: () => req<WorkflowRow[]>('/workflows'),
  workflow: (name: string) => req<WorkflowRow>(`/workflows/${name}`),
  copyWorkflow: (name: string) => post<{ ok: boolean; path: string }>(`/workflows/${name}/copy`),
  saveWorkflow: (name: string, yaml: string) =>
    put<{ ok: boolean; path: string }>(`/workflows/${name}`, { yaml }),
  validateWorkflow: (name: string) => post<WorkflowValidation>(`/workflows/${name}/validate`),
  deleteWorkflow: (name: string) => del(`/workflows/${name}`),

  // ── analyze ──
  analyze: (body: AnalyzeBody) => post<JobAck>('/analyze', body),
  recentAnalyses: () => req<AnalysisManifest[]>('/analyze/recent'),

  // ── environment ──
  environment: () => req<EnvironmentPayload>('/environment'),
  rerunDoctor: () => post<EnvironmentPayload['doctor']>('/environment/doctor'),
  startServer: (id: string) => post<JobAck>(`/environment/servers/${id}/start`),
  stopServer: (id: string) => post(`/environment/servers/${id}/stop`),
  installAgent: (agent: string, body: { force: boolean }) =>
    post<JobAck>(`/environment/agents/${agent}/install`, body),
};
