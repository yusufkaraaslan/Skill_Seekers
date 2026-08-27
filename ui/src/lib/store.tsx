// ── Seeker HUD · global store ───────────────────────────────────────────────
// Loads all dynamic data from the Skill Seekers backend and polls for job
// updates. Exposes one context consumed by App + all sections.

import { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react';
import type { ReactNode } from 'react';
import { toast } from 'sonner';
import { setClis } from '@/lib/data';
import type {
  Activity, Cli, Job, MarketSkill, Marketplace, McpTool, Project, Skill, Workflow, ConfigEntry, ConfigSource,
} from '@/lib/data';
import { api as client } from '@/lib/api';
import type { CreateSpec, SettingsPayload } from '@/lib/api';

export interface StoreState {
  ready: boolean;
  backendDown: boolean;
  skills: Skill[];
  jobs: Job[];
  projects: Project[];
  clis: Cli[];
  activity: Activity[];
  mcpTools: McpTool[];
  workflows: Workflow[];
  sources: ConfigSource[];
  entries: ConfigEntry[];
  markets: Marketplace[];
  marketSkills: MarketSkill[];
  settings: SettingsPayload | null;
  root: string;
  skillQuery: string;
  setSkillQuery: (q: string) => void;

  refresh: () => Promise<void>;
  refreshLibrary: () => Promise<void>;
  refreshMarket: () => Promise<void>;
  refreshSettings: () => Promise<void>;

  create: (spec: CreateSpec) => Promise<void>;
  move: (ids: string[], dest: string) => Promise<void>;
  remove: (ids: string[]) => Promise<void>;
  port: (ids: string[], cli: string, ai: boolean, agent: string) => Promise<void>;
  enhance: (id: string) => Promise<void>;
  packageSkill: (id: string, targets?: string[]) => Promise<void>;
  saveContent: (id: string, content: string) => Promise<void>;
  addProject: (path: string) => Promise<void>;
  rescan: (id: string) => Promise<void>;
  removeProject: (id: string) => Promise<void>;
  addSource: (repo: string) => Promise<void>;
  fetchSource: (name: string) => Promise<void>;
  fetchOfficial: (name: string) => Promise<void>;
  removeSource: (name: string) => Promise<void>;
  buildConfig: (path: string, name: string) => Promise<void>;
  addMarketplace: (repo: string) => Promise<void>;
  removeMarketplace: (name: string) => Promise<void>;
  installMarketItem: (s: MarketSkill) => Promise<void>;
  publish: (skillName: string, marketplace: string) => Promise<void>;
  setKey: (name: string, value: string) => Promise<void>;
  setDefaults: (settings: Record<string, unknown>) => Promise<void>;
  reprobe: () => Promise<void>;
}

const StoreContext = createContext<StoreState | null>(null);

export function useStore(): StoreState {
  const ctx = useContext(StoreContext);
  if (!ctx) throw new Error('useStore outside provider');
  return ctx;
}

export function StoreProvider({ children }: { children: ReactNode }) {
  const [ready, setReady] = useState(false);
  const [backendDown, setBackendDown] = useState(false);
  const [skills, setSkills] = useState<Skill[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [clis, setClisState] = useState<Cli[]>([]);
  const [activity, setActivity] = useState<Activity[]>([]);
  const [mcpTools, setMcpTools] = useState<McpTool[]>([]);
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [sources, setSources] = useState<ConfigSource[]>([]);
  const [entries, setEntries] = useState<ConfigEntry[]>([]);
  const [markets, setMarkets] = useState<Marketplace[]>([]);
  const [marketSkills, setMarketSkills] = useState<MarketSkill[]>([]);
  const [settings, setSettings] = useState<SettingsPayload | null>(null);
  const [skillQuery, setSkillQuery] = useState('');
  const runningRef = useRef(0);

  const refresh = useCallback(async () => {
    try {
      const o = await client.overview();
      setSkills(o.skills);
      setJobs(o.jobs);
      setProjects(o.projects);
      setClisState(o.clis);
      setClis(o.clis);
      setActivity(o.activity);
      runningRef.current = o.jobs.filter((j) => j.status === 'running').length;
      setBackendDown(false);
    } catch {
      setBackendDown(true);
    } finally {
      setReady(true);
    }
  }, []);

  const refreshLibrary = useCallback(async () => {
    try {
      const l = await client.library();
      setSources(l.sources);
      setEntries(l.entries);
      setWorkflows(l.workflows);
    } catch { /* backend offline */ }
  }, []);

  const refreshMarket = useCallback(async () => {
    try {
      const m = await client.marketplaces();
      setMarkets(m.markets);
      setMarketSkills(m.skills);
    } catch { /* backend offline */ }
  }, []);

  const refreshSettings = useCallback(async () => {
    try {
      setSettings(await client.settings());
    } catch { /* backend offline */ }
  }, []);

  // initial load
  useEffect(() => {
    refresh();
    refreshLibrary();
    refreshSettings();
    client.mcpTools().then((m) => setMcpTools(m.tools)).catch(() => undefined);
  }, [refresh, refreshLibrary, refreshSettings]);

  // polling: fast while jobs run, slow otherwise
  useEffect(() => {
    const tick = () => {
      refresh();
      if (runningRef.current > 0) refreshLibrary();
    };
    const fast = setInterval(() => {
      if (runningRef.current > 0) tick();
    }, 1500);
    const slow = setInterval(tick, 10000);
    return () => {
      clearInterval(fast);
      clearInterval(slow);
    };
  }, [refresh, refreshLibrary]);

  const act = useCallback(
    async (fn: () => Promise<unknown>, ok?: string, then?: () => Promise<void>) => {
      try {
        await fn();
        if (ok) toast.success(ok);
        await refresh();
        await then?.();
      } catch (e) {
        toast.error('operation failed', { description: e instanceof Error ? e.message : String(e) });
      }
    },
    [refresh],
  );

  const value: StoreState = {
    ready, backendDown, skills, jobs, projects, clis, activity, mcpTools, workflows,
    sources, entries, markets, marketSkills, settings,
    root: settings?.root ?? '',
    skillQuery, setSkillQuery,
    refresh, refreshLibrary, refreshMarket, refreshSettings,

    create: (spec) =>
      act(
        () => client.create(spec),
        `Create job launched: ${spec.name || 'auto'}`,
      ),
    move: (ids, dest) =>
      act(() => client.moveSkills(ids, dest), `Moved ${ids.length} skill(s)`),
    remove: (ids) =>
      act(() => client.deleteSkills(ids), `Deleted ${ids.length} skill(s)`),
    port: (ids, cli, ai, agent) =>
      act(() => client.portSkills(ids, cli, ai, agent), `Porting ${ids.length} skill(s) → ${cli}`),
    enhance: (id) =>
      act(() => client.enhanceSkill(id), `Enhancing ${id}`),
    packageSkill: (id, targets = ['claude']) =>
      act(() => client.packageSkill(id, targets), `Packaging ${id} → ${targets.join(', ')}`),
    saveContent: (id, content) =>
      act(() => client.saveSkillContent(id, content), `Saved ${id}/SKILL.md`),
    addProject: (path) =>
      act(() => client.addProject(path), 'Project added — scan queued'),
    rescan: (id) =>
      act(() => client.rescanProject(id), 'Rescan queued'),
    removeProject: (id) =>
      act(() => client.removeProject(id), 'Project removed'),
    addSource: (repo) =>
      act(() => client.addSource(repo), 'Config source registered', refreshLibrary),
    fetchSource: (name) =>
      act(() => client.fetchSource(name), `fetch_config started: ${name}`),
    fetchOfficial: (name) =>
      act(() => client.fetchOfficial(name), `fetched ${name}.json from official registry`, refreshLibrary),
    removeSource: (name) =>
      act(() => client.removeSource(name), `Removed source ${name}`, refreshLibrary),
    buildConfig: (path, name) =>
      act(() => client.buildConfig(path), `Build queued: ${name}`),
    addMarketplace: (repo) =>
      act(() => client.addMarketplace(repo), 'Marketplace registered', refreshMarket),
    removeMarketplace: (name) =>
      act(() => client.removeMarketplace(name), `Removed ${name}`, refreshMarket),
    installMarketItem: (s) =>
      act(
        () =>
          client.installMarketItem(
            s.path,
            s.kind,
            clis.filter((c) => c.detected).map((c) => c.id).length
              ? clis.filter((c) => c.detected).map((c) => c.id)
              : ['claude'],
          ),
        `Installing ${s.name}`,
        refreshMarket,
      ),
    publish: (skillName, marketplace) =>
      act(() => client.publishSkill(skillName, marketplace), `publish_to_marketplace queued`),
    setKey: (name, value) =>
      act(() => client.setKey(name, value), `${name} saved`, refreshSettings),
    setDefaults: (s) =>
      act(() => client.setDefaults(s), 'Defaults saved', refreshSettings),
    reprobe: () =>
      act(async () => {
        const r = await client.reprobe();
        setClis(r.clis);
      }, 'Reprobed CLIs', refreshSettings),
  };

  return <StoreContext.Provider value={value}>{children}</StoreContext.Provider>;
}
