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
  pending: boolean;
  sectionErrors: Record<string, string>;
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
  refreshMcp: () => Promise<void>;

  create: (spec: CreateSpec) => Promise<boolean>;
  move: (ids: string[], dest: string) => Promise<boolean>;
  remove: (ids: string[]) => Promise<boolean>;
  port: (ids: string[], cli: string, replace: boolean) => Promise<boolean>;
  enhance: (id: string) => Promise<boolean>;
  packageSkill: (id: string, targets?: string[]) => Promise<boolean>;
  saveContent: (id: string, content: string, revision: string) => Promise<boolean>;
  addProject: (path: string) => Promise<boolean>;
  rescan: (id: string) => Promise<boolean>;
  removeProject: (id: string) => Promise<boolean>;
  addSource: (repo: string) => Promise<boolean>;
  fetchSource: (name: string) => Promise<boolean>;
  fetchOfficial: (name: string) => Promise<boolean>;
  removeSource: (name: string) => Promise<boolean>;
  buildConfig: (path: string, name: string) => Promise<boolean>;
  addMarketplace: (repo: string) => Promise<boolean>;
  removeMarketplace: (name: string) => Promise<boolean>;
  installMarketItem: (s: MarketSkill, targets: string[], replace: boolean) => Promise<boolean>;
  publish: (skillName: string, marketplace: string) => Promise<boolean>;
  setKey: (name: string, value: string) => Promise<boolean>;
  setDefaults: (settings: Record<string, unknown>) => Promise<boolean>;
  reprobe: () => Promise<boolean>;
  syncMarket: () => Promise<boolean>;
  cancelJob: (id: string) => Promise<boolean>;
  retryJob: (id: string) => Promise<boolean>;
  restoreSkill: (id: string) => Promise<boolean>;
}

const StoreContext = createContext<StoreState | null>(null);

export function useStore(): StoreState {
  const ctx = useContext(StoreContext);
  if (!ctx) throw new Error('useStore outside provider');
  return ctx;
}

export function StoreProvider({ children }: { children: ReactNode }) {
  const [sectionErrors, setSectionErrors] = useState<Record<string, string>>({});
  const [pending, setPending] = useState(false);
  const mutationRef = useRef(false);
  const refreshRef = useRef(false);
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

  const inflightRef = useRef<Promise<void> | null>(null);
  const refresh = useCallback(async (): Promise<void> => {
    // Share an in-flight poll instead of dropping the call: a mutation that
    // awaits refresh() must always observe post-mutation state, so after the
    // stale request settles we fetch again.
    if (inflightRef.current) {
      await inflightRef.current;
      if (inflightRef.current) return inflightRef.current;
    }
    const run = (async () => {
      refreshRef.current = true;
      try {
        const o = await client.overview();
        setSkills(o.skills);
        setJobs(o.jobs);
        setProjects(o.projects);
        setClisState(o.clis);
        setClis(o.clis);
        setActivity(o.activity);
        runningRef.current = o.jobs.filter((j) => ['running', 'queued', 'cancelling'].includes(j.status)).length;
        setBackendDown(false);
      } catch {
        setBackendDown(true);
      } finally {
        setReady(true);
        refreshRef.current = false;
      }
    })();
    inflightRef.current = run;
    try { await run; } finally { if (inflightRef.current === run) inflightRef.current = null; }
  }, []);

  const refreshLibrary = useCallback(async () => {
    try {
      const l = await client.library();
      setSources(l.sources);
      setEntries(l.entries);
      setWorkflows(l.workflows);
      setSectionErrors(e => ({ ...e, library: '' }));
    } catch (error) { setSectionErrors(e => ({ ...e, library: String(error) })); }
  }, []);

  const refreshMarket = useCallback(async () => {
    try {
      const m = await client.marketplaces();
      setMarkets(m.markets);
      setMarketSkills(m.skills);
      setSectionErrors(e => ({ ...e, marketplace: '' }));
    } catch (error) { setSectionErrors(e => ({ ...e, marketplace: String(error) })); }
  }, []);

  const refreshSettings = useCallback(async () => {
    try {
      setSettings(await client.settings());
      setSectionErrors(e => ({ ...e, settings: '' }));
    } catch (error) { setSectionErrors(e => ({ ...e, settings: String(error) })); }
  }, []);

  const refreshMcp = useCallback(async () => {
    try {
      setMcpTools((await client.mcpTools()).tools);
      setSectionErrors(e => ({ ...e, mcp: '' }));
    } catch (error) { setSectionErrors(e => ({ ...e, mcp: String(error) })); }
  }, []);

  // initial load
  useEffect(() => {
    refresh();
    refreshLibrary();
    refreshSettings();
    refreshMcp();
  }, [refresh, refreshLibrary, refreshSettings, refreshMcp]);

  // One awaited polling loop prevents overlapping scans and stale responses.
  useEffect(() => {
    let stopped = false;
    let timer: ReturnType<typeof setTimeout>;
    const tick = async () => {
      const wasRunning = runningRef.current > 0;
      await refresh();
      if (wasRunning) await Promise.allSettled([refreshLibrary(), refreshMarket()]);
      if (!stopped) timer = setTimeout(tick, runningRef.current > 0 ? 1500 : 10000);
    };
    timer = setTimeout(tick, 1500);
    return () => { stopped = true; clearTimeout(timer); };
  }, [refresh, refreshLibrary, refreshMarket]);

  const act = useCallback(
    async (fn: () => Promise<unknown>, ok?: string, then?: () => Promise<void>) => {
      if (mutationRef.current) return false;
      mutationRef.current = true;
      setPending(true);
      try {
        await fn();
        if (ok) toast.success(ok);
        await refresh();
        await then?.();
        return true;
      } catch (e) {
        toast.error('operation failed', { description: e instanceof Error ? e.message : String(e) });
        return false;
      } finally { mutationRef.current = false; setPending(false); }
    },
    [refresh],
  );

  const value: StoreState = {
    ready, pending, sectionErrors, backendDown, skills, jobs, projects, clis, activity, mcpTools, workflows,
    sources, entries, markets, marketSkills, settings,
    root: settings?.root ?? '',
    skillQuery, setSkillQuery,
    refresh, refreshLibrary, refreshMarket, refreshSettings, refreshMcp,

    create: (spec) =>
      act(
        () => client.create(spec),
        `Create job launched: ${spec.name || 'auto'}`,
      ),
    move: (ids, dest) =>
      act(() => client.moveSkills(ids, dest), `Moved ${ids.length} skill(s)`),
    remove: (ids) =>
      act(() => client.deleteSkills(ids), `Deleted ${ids.length} skill(s)`),
    port: (ids, cli, replace) =>
      act(() => client.portSkills(ids, cli, replace), `Porting ${ids.length} skill(s) → ${cli}`),
    enhance: (id) =>
      act(() => client.enhanceSkill(id), `Enhancing ${id}`),
    packageSkill: (id, targets = ['claude']) =>
      act(() => client.packageSkill(id, targets), `Packaging ${id} → ${targets.join(', ')}`),
    saveContent: (id, content, revision) =>
      act(() => client.saveSkillContent(id, content, revision), `Saved ${id}/SKILL.md`),
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
    installMarketItem: (s, targets, replace) =>
      act(() => client.installMarketItem(s.path, s.kind, targets, replace), `Installing ${s.name}`, refreshMarket),
    syncMarket: () => act(() => client.syncMarketplaces(), 'Marketplace sync queued'),
    cancelJob: (id) => act(() => client.cancelJob(id), 'Cancellation requested'),
    retryJob: (id) => act(() => client.retryJob(id), 'Retry queued'),
    restoreSkill: (id) => act(() => client.restoreSkill(id), 'Skill restored'),
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
