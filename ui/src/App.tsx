import { useEffect, useState } from 'react';
import { Routes, Route } from 'react-router';
import { Toaster } from '@/components/ui/sonner';
import { TooltipProvider } from '@/components/ui/tooltip';
import {
  LayoutDashboard, FolderGit2, Layers, Wand2, ListChecks, Settings2, Radar as RadarIcon, Search,
  Store, LibraryBig, Plug,
} from 'lucide-react';
import Overview from '@/sections/Overview';
import Projects from '@/sections/Projects';
import Skills, { SkillDrawer } from '@/sections/Skills';
import Create from '@/sections/Create';
import Marketplace from '@/sections/Marketplace';
import Library from '@/sections/Library';
import Mcp from '@/sections/Mcp';
import Jobs from '@/sections/Jobs';
import Settings from '@/sections/Settings';
import { StoreProvider, useStore } from '@/lib/store';
import { matchesSkillQuery } from '@/lib/data';
import { cn } from '@/lib/utils';

type View = 'overview' | 'projects' | 'skills' | 'create' | 'marketplace' | 'library' | 'mcp' | 'jobs' | 'settings';

const NAV: { id: View; label: string; icon: typeof LayoutDashboard; kbd: string }[] = [
  { id: 'overview',    label: 'Overview',    icon: LayoutDashboard, kbd: '1' },
  { id: 'projects',    label: 'Projects',    icon: FolderGit2,      kbd: '2' },
  { id: 'skills',      label: 'Skills',      icon: Layers,          kbd: '3' },
  { id: 'create',      label: 'Create',      icon: Wand2,           kbd: '4' },
  { id: 'marketplace', label: 'Marketplace', icon: Store,           kbd: '5' },
  { id: 'library',     label: 'Configs',     icon: LibraryBig,      kbd: '6' },
  { id: 'mcp',         label: 'Seeker MCP',  icon: Plug,            kbd: '7' },
  { id: 'jobs',        label: 'Jobs',        icon: ListChecks,      kbd: '8' },
  { id: 'settings',    label: 'Settings',    icon: Settings2,       kbd: '9' },
];

export default function App() {
  return (
    <StoreProvider>
      <Routes>
        <Route path="/" element={<Hud />} />
      </Routes>
    </StoreProvider>
  );
}

function Hud() {
  const store = useStore();
  const [view, setView] = useState<View>('overview');
  const [openSkillId, setOpenSkillId] = useState<string | null>(null);
  const [projectFilter, setProjectFilter] = useState<string>('all');

  const openSkill = store.skills.find((s) => s.id === openSkillId) ?? null;
  const runningCount = store.jobs.filter((j) => j.status === 'running').length;
  const installCount = store.skills.reduce((a, s) => a + s.installs.length, 0);

  // number-key navigation (matches the kbd hints in the sidebar)
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      const target = e.target as HTMLElement;
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable) return;
      const nav = NAV.find((n) => n.kbd === e.key);
      if (nav) setView(nav.id);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  return (
    <TooltipProvider delayDuration={200}>
      <div className="flex h-screen overflow-hidden bg-background">
        {/* ── sidebar ── */}
        <aside className="w-[212px] shrink-0 border-r border-sidebar-border bg-sidebar flex flex-col">
          <div className="flex items-center gap-2.5 px-4 h-14 border-b border-sidebar-border">
            <div className="flex h-8 w-8 items-center justify-center rounded border border-primary/50 bg-primary/10">
              <RadarIcon className="h-4 w-4 text-primary" />
            </div>
            <div>
              <div className="font-mono-hud text-[13px] font-bold tracking-wider text-foreground">
                SEEKER<span className="text-primary">HUD</span>
              </div>
              <div className="font-mono-hud text-[9px] uppercase tracking-[0.25em] text-muted-foreground">v3.9.0 · live</div>
            </div>
          </div>

          <nav className="flex-1 p-2.5 space-y-0.5">
            {NAV.map((n) => (
              <button
                key={n.id}
                onClick={() => setView(n.id)}
                className={cn(
                  'w-full flex items-center gap-2.5 rounded px-3 py-2 text-[13px] transition-colors',
                  view === n.id
                    ? 'bg-sidebar-accent text-sidebar-accent-foreground border-l-2 border-primary'
                    : 'text-sidebar-foreground hover:bg-sidebar-accent/50 hover:text-foreground border-l-2 border-transparent'
                )}
              >
                <n.icon className="h-4 w-4 shrink-0" />
                <span className="font-medium">{n.label}</span>
                {n.id === 'jobs' && runningCount > 0 && (
                  <span className="ml-auto flex h-4 min-w-4 items-center justify-center rounded-full bg-primary/20 px-1 font-mono-hud text-[9px] text-primary">
                    {runningCount}
                  </span>
                )}
                {n.id !== 'jobs' && (
                  <span className="ml-auto font-mono-hud text-[9px] text-muted-foreground/50">{n.kbd}</span>
                )}
              </button>
            ))}
          </nav>

          <div className="border-t border-sidebar-border p-3 space-y-2">
            <div className="flex items-center gap-2 px-1">
              <span
                className={cn(
                  'status-dot inline-block h-[6px] w-[6px] rounded-full',
                  store.backendDown
                    ? 'bg-[hsl(0_72%_55%)] text-[hsl(0_72%_55%)]'
                    : 'bg-[hsl(152_60%_50%)] text-[hsl(152_60%_50%)]'
                )}
              />
              <span className="font-mono-hud text-[10px] text-muted-foreground">
                {store.backendDown ? 'daemon offline' : 'daemon connected'}
              </span>
            </div>
            <div className="flex items-center gap-2 px-1">
              <span className="status-dot inline-block h-[6px] w-[6px] rounded-full bg-primary text-primary animate-pulse" />
              <span className="font-mono-hud text-[10px] text-muted-foreground">
                watching {store.projects.length} projects
              </span>
            </div>
          </div>
        </aside>

        {/* ── main ── */}
        <div className="flex-1 flex flex-col min-w-0">
          {/* topbar */}
          <header className="h-14 shrink-0 border-b border-border flex items-center gap-4 px-5 bg-card/50 scanline relative">
            <div className="font-mono-hud text-[10px] uppercase tracking-[0.25em] text-muted-foreground">
              seeker://<span className="text-primary">{view}</span>
            </div>
            <div className="hidden md:flex items-center gap-2 flex-1 max-w-md">
              <div className="relative w-full">
                <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
                <input
                  value={store.skillQuery}
                  placeholder="search skills…  ( enter opens first match )"
                  className="w-full h-8 rounded border border-border bg-secondary/40 pl-8 pr-3 font-mono-hud text-xs text-foreground placeholder:text-muted-foreground/60 outline-none focus:border-primary/50"
                  onChange={(e) => {
                    store.setSkillQuery(e.target.value);
                    if (view !== 'skills') setView('skills');
                  }}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      // the drawer autofocuses its first button; without this the
                      // same Enter keypress activates it (packaging the skill)
                      e.preventDefault();
                      const hit = store.skills.find((s) => matchesSkillQuery(s, store.skillQuery));
                      if (hit) setOpenSkillId(hit.id);
                    }
                  }}
                />
              </div>
            </div>
            <div className="ml-auto flex items-center gap-3">
              <span className="hidden lg:block font-mono-hud text-[10px] text-muted-foreground">
                skills <span className="text-foreground">{store.skills.length}</span> · jobs{' '}
                <span className="text-primary">{runningCount} active</span>
              </span>
              <div className="h-4 w-px bg-border" />
              <div className="flex h-7 w-7 items-center justify-center rounded-full border border-primary/50 bg-primary/15 font-mono-hud text-[10px] font-bold text-primary">
                YK
              </div>
            </div>
          </header>

          {/* content */}
          <main className="flex-1 overflow-y-auto p-5 bg-grid">
            {view === 'overview' && (
              <Overview
                skills={store.skills}
                jobs={store.jobs}
                clis={store.clis}
                activity={store.activity}
                onNavigate={(v) => setView(v as View)}
                onNewScan={() => setView('projects')}
                onNewSkill={() => setView('create')}
              />
            )}
            {view === 'projects' && (
              <Projects
                projects={store.projects}
                skills={store.skills}
                onRescan={store.rescan}
                onAdd={store.addProject}
                onViewSkills={(pid) => { setProjectFilter(pid); setView('skills'); }}
              />
            )}
            {view === 'skills' && (
              <Skills
                skills={store.skills}
                projects={store.projects}
                projectFilter={projectFilter}
                onProjectFilter={setProjectFilter}
                query={store.skillQuery}
                onQuery={store.setSkillQuery}
                onOpenSkill={setOpenSkillId}
                onMove={store.move}
                onPort={(ids, cli, opts) => store.port(ids, cli, opts.ai, opts.agent)}
                onDelete={store.remove}
                onEnhance={store.enhance}
                onPackage={store.packageSkill}
              />
            )}
            {view === 'create' && (
              <Create
                workflows={store.workflows}
                onLaunch={(spec) => {
                  store.create(spec);
                  setView('jobs');
                }}
              />
            )}
            {view === 'marketplace' && (
              <Marketplace
                markets={store.markets}
                skills={store.marketSkills}
                onAdd={store.addMarketplace}
                onRemove={store.removeMarketplace}
                onInstall={store.installMarketItem}
                onPublish={store.publish}
                onRefresh={store.refreshMarket}
                localSkills={store.skills}
              />
            )}
            {view === 'library' && (
              <Library
                sources={store.sources}
                entries={store.entries}
                workflows={store.workflows}
                onAddSource={store.addSource}
                onFetchSource={store.fetchSource}
                onFetchOfficial={store.fetchOfficial}
                onRemoveSource={store.removeSource}
                onBuild={store.buildConfig}
              />
            )}
            {view === 'mcp' && <Mcp tools={store.mcpTools} />}
            {view === 'jobs' && <Jobs jobs={store.jobs} />}
            {view === 'settings' && (
              <Settings
                settings={store.settings}
                onSetKey={store.setKey}
                onSetDefaults={store.setDefaults}
                onReprobe={store.reprobe}
              />
            )}
          </main>

          {/* status bar */}
          <footer className="h-7 shrink-0 border-t border-border bg-card/60 flex items-center gap-4 px-4 font-mono-hud text-[10px] text-muted-foreground">
            <span className={store.backendDown ? 'text-destructive' : 'text-primary'}>
              ▮ {store.backendDown ? 'BACKEND OFFLINE — start with `skill-seekers ui`' : 'SEEKER READY'}
            </span>
            <span className="hidden md:block truncate">root: {store.root || '…'}</span>
            <span className="hidden md:block">mcp: {store.mcpTools.length} tools</span>
            <span className="ml-auto hidden sm:block">{store.skills.length} skills · {installCount} installs</span>
          </footer>
        </div>
      </div>

      <SkillDrawer
        skill={openSkill}
        onClose={() => setOpenSkillId(null)}
        onEnhance={store.enhance}
        onPackage={store.packageSkill}
        onSave={store.saveContent}
      />
      <Toaster position="bottom-right" theme="dark" />
    </TooltipProvider>
  );
}
