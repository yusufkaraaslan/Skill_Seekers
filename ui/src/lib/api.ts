// ── API client for the Seeker HUD backend (skill_seekers.web) ───────────────

const BASE = '/api';

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
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
    throw new Error(detail);
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
}

export interface CreateSpec {
  entries: { type: string; input: string }[];
  name: string;
  description: string;
  targets: string[];
  flags: Record<string, unknown>;
}

export const api = {
  overview: () => req<OverviewPayload>('/overview'),
  skills: () => req<Skill[]>('/skills'),
  jobs: () => req<Job[]>('/jobs'),
  library: () => req<LibraryPayload>('/library'),
  marketplaces: () => req<MarketPayload>('/marketplaces'),
  mcpTools: () => req<{ tools: McpTool[]; count: number }>('/mcp/tools'),
  settings: () => req<SettingsPayload>('/settings'),

  create: (spec: CreateSpec) => post<{ ok: boolean; name: string }>('/create', spec),
  moveSkills: (ids: string[], dest: string) => post('/skills/move', { ids, dest }),
  deleteSkills: (ids: string[]) => post('/skills/delete', { ids }),
  portSkills: (ids: string[], cli: string, ai: boolean, agent: string) =>
    post('/skills/port', { ids, cli, ai, agent }),
  enhanceSkill: (id: string) => post(`/skills/${id}/enhance`),
  packageSkill: (id: string, targets: string[]) => post(`/skills/${id}/package`, { targets }),
  saveSkillContent: (id: string, content: string) => put(`/skills/${id}/content`, { content }),

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
  installMarketItem: (path: string, kind: string, clis: string[]) =>
    post('/marketplaces/install', { path, kind, clis }),
  publishSkill: (skill_name: string, marketplace: string) =>
    post('/marketplaces/publish', { skill_name, marketplace }),

  setKey: (name: string, value: string) => put('/settings/keys', { name, value }),
  setDefaults: (settings: Record<string, unknown>) => put('/settings/defaults', { settings }),
  reprobe: () => post<{ clis: Cli[] }>('/settings/reprobe'),
};
