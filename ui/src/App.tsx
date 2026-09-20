import { lazy, Suspense, useCallback, useEffect, useState } from 'react';
import { Routes, Route, useLocation, useNavigate } from 'react-router';
import { Toaster } from '@/components/ui/sonner';
import { TooltipProvider } from '@/components/ui/tooltip';
import {
  LayoutDashboard, FolderGit2, Layers, Wand2, ListChecks, Settings2, Radar as RadarIcon, Search,
  Store, LibraryBig, Workflow, ScanSearch, HeartPulse, Menu, X,
} from 'lucide-react';
const Overview = lazy(() => import('@/sections/Overview'));
const Projects = lazy(() => import('@/sections/Projects'));
const Skills = lazy(() => import('@/sections/Skills'));
const SkillPage = lazy(() => import('@/sections/SkillPage'));
const Create = lazy(() => import('@/sections/Create'));
const Marketplace = lazy(() => import('@/sections/Marketplace'));
const Library = lazy(() => import('@/sections/Library'));
const ConfigPage = lazy(() => import('@/sections/ConfigPage'));
const Workflows = lazy(() => import('@/sections/Workflows'));
const Analyze = lazy(() => import('@/sections/Analyze'));
const Environment = lazy(() => import('@/sections/Environment'));
const Jobs = lazy(() => import('@/sections/Jobs'));
const Settings = lazy(() => import('@/sections/Settings'));
import { StoreProvider, useStore } from '@/lib/store';
import { matchesSkillQuery } from '@/lib/data';
import type { View } from '@/lib/data';
import { cn } from '@/lib/utils';

const NAV: { id: View; label: string; icon: typeof LayoutDashboard; kbd: string }[] = [
  { id: 'overview',    label: 'Overview',    icon: LayoutDashboard, kbd: '1' },
  { id: 'projects',    label: 'Projects',    icon: FolderGit2,      kbd: '2' },
  { id: 'skills',      label: 'Skills',      icon: Layers,          kbd: '3' },
  { id: 'create',      label: 'Create',      icon: Wand2,           kbd: '4' },
  { id: 'marketplace', label: 'Marketplace', icon: Store,           kbd: '5' },
  { id: 'library',     label: 'Configs',     icon: LibraryBig,      kbd: '6' },
  { id: 'workflows',   label: 'Workflows',   icon: Workflow,        kbd: '7' },
  { id: 'analyze',     label: 'Analyze',     icon: ScanSearch,      kbd: '8' },
  { id: 'environment', label: 'Environment', icon: HeartPulse,      kbd: '9' },
  { id: 'jobs',        label: 'Jobs',        icon: ListChecks,      kbd: '' },
  { id: 'settings',    label: 'Settings',    icon: Settings2,       kbd: '0' },
];

export default function App() {
  return (
    <StoreProvider>
      <Routes>
        <Route path="/*" element={<Hud />} />
      </Routes>
    </StoreProvider>
  );
}

function Hud() {
  const store = useStore();
  const navigate = useNavigate();
  const location = useLocation();
  // One catch-all route: /<section>/<detail id?>. 'configs' is the public
  // spelling of the library view; '/mcp' is the retired Seeker MCP screen,
  // which now lives inside Environment.
  const [, segment = '', param = ''] = location.pathname.split('/');
  const candidate = segment === 'configs' ? 'library' : segment === 'mcp' ? 'environment' : segment;
  const view: View = NAV.find(n => n.id === candidate)?.id ?? 'overview';
  const [sidebarOpen, setSidebarOpen] = useState(false);
  // Every client-side navigation out of a detail page runs through these two,
  // so both ask the store whether an editor is holding unsaved edits first.
  const { confirmLeave } = store;
  const setView = useCallback((next: View) => {
    if (!confirmLeave()) return;
    navigate(next === 'overview' ? '/' : `/${next === 'library' ? 'configs' : next}`);
    setSidebarOpen(false);
  }, [navigate, confirmLeave]);
  useEffect(() => { if (segment === 'mcp') navigate('/environment', { replace: true }); }, [segment, navigate]);
  const detailId = param ? decodeURIComponent(param) : null;
  const openSkill = useCallback((id: string) => {
    if (confirmLeave()) navigate(`/skills/${encodeURIComponent(id)}`);
  }, [navigate, confirmLeave]);
  const [projectFilter, setProjectFilter] = useState<string>('all');

  const runningCount = store.jobs.filter((j) => j.status === 'running').length;
  const installCount = store.skills.reduce((a, s) => a + s.installs.length, 0);

  // number-key navigation (matches the kbd hints in the sidebar)
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      const target = e.target as HTMLElement;
      if (['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName) || target.isContentEditable || document.querySelector('[role=dialog], [role=alertdialog]')) return;
      const nav = NAV.find((n) => n.kbd === e.key);
      if (nav) setView(nav.id);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [setView]);

  return (
    <TooltipProvider delayDuration={200}>
      <div className="flex h-dvh overflow-hidden bg-background">
        {/* ── sidebar ── */}
        {sidebarOpen && <button aria-label="Close navigation" className="fixed inset-0 z-40 bg-black/60 md:hidden" onClick={() => setSidebarOpen(false)} />}
        <aside id="main-navigation" className={cn("w-[212px] shrink-0 border-r border-sidebar-border bg-sidebar flex-col md:flex", sidebarOpen ? 'fixed inset-y-0 left-0 z-50 flex' : 'hidden')}>
          <div className="flex items-center gap-2.5 px-4 h-14 border-b border-sidebar-border">
            <div className="flex h-8 w-8 items-center justify-center rounded border border-primary/50 bg-primary/10">
              <RadarIcon className="h-4 w-4 text-primary" />
            </div>
            <div>
              <div className="font-mono-hud text-[13px] font-bold tracking-wider text-foreground">
                SEEKER<span className="text-primary">HUD</span>
              </div>
              <div className="font-mono-hud text-[9px] uppercase tracking-[0.25em] text-muted-foreground">local workspace</div>
            </div>
          </div>

          <nav aria-label="Main navigation" className="flex-1 p-2.5 space-y-0.5">
            {NAV.map((n) => (
              <button
                key={n.id}
                aria-current={view === n.id ? 'page' : undefined}
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
                tracking {store.projects.length} projects
              </span>
            </div>
          </div>
        </aside>

        {/* ── main ── */}
        <div className="flex-1 flex flex-col min-w-0">
          {/* topbar */}
          <header className="h-14 shrink-0 border-b border-border flex items-center gap-4 px-5 bg-card/50 scanline relative">
            <ButtonNavigation open={sidebarOpen} onToggle={() => setSidebarOpen(!sidebarOpen)} />
            <div className="font-mono-hud text-[10px] uppercase tracking-[0.25em] text-muted-foreground">
              seeker://<span className="text-primary">{view}</span>
            </div>
            <div className="hidden md:flex items-center gap-2 flex-1 max-w-md">
              <div className="relative w-full">
                <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
                <input
                  aria-label="Search skills"
                  value={store.skillQuery}
                  placeholder="search skills…  ( enter opens first match )"
                  className="w-full h-8 rounded border border-border bg-secondary/40 pl-8 pr-3 font-mono-hud text-xs text-foreground placeholder:text-muted-foreground/60 outline-none focus:border-primary/50"
                  onChange={(e) => {
                    // Typing here also leaves a detail page: the query filters
                    // the list, which /skills/:id does not show. Confirm before
                    // the keystroke lands, so a dismissed prompt changes nothing.
                    const leaves = view !== 'skills' || !!detailId;
                    if (leaves && !confirmLeave()) return;
                    store.setSkillQuery(e.target.value);
                    if (leaves) setView('skills');
                  }}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      // the skill page autofocuses its first control; without this
                      // the same Enter keypress would activate it
                      e.preventDefault();
                      const hit = store.skills.find((s) => matchesSkillQuery(s, store.skillQuery));
                      if (hit) openSkill(hit.id);
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
                <Settings2 className="h-3.5 w-3.5" aria-hidden="true" />
              </div>
            </div>
          </header>

          {/* content */}
          <main id="main-content" className="flex-1 min-w-0 overflow-y-auto p-3 md:p-5 bg-grid">
            {store.backendDown && <div role="alert" className="mb-4 rounded border border-destructive p-3">Backend unavailable. <button className="underline" onClick={() => store.refresh()}>Retry connection</button></div>}
            {store.sectionErrors[view === 'create' ? 'settings' : view] && <div role="alert" className="mb-4 rounded border border-destructive p-3">{store.sectionErrors[view === 'create' ? 'settings' : view]} <button className="underline" onClick={() => { if (view === 'library') store.refreshLibrary(); if (view === 'marketplace') store.refreshMarket(); if (view === 'settings' || view === 'create') store.refreshSettings(); }}>Retry</button></div>}
            {store.pending && <p role="status" className="mb-2 text-sm text-primary">Saving request…</p>}
            {!store.ready && <p role="status">Loading workspace…</p>}
            <Suspense fallback={<p role="status">Loading screen…</p>}>
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
                onRemove={store.removeProject}
                onViewConfigs={() => setView('library')}
                onViewSkills={(pid) => { setProjectFilter(pid); setView('skills'); }}
              />
            )}
            {view === 'skills' && detailId && <SkillPage key={detailId} id={detailId} />}
            {view === 'skills' && !detailId && (
              <Skills
                skills={store.skills}
                projects={store.projects}
                projectFilter={projectFilter}
                onProjectFilter={setProjectFilter}
                query={store.skillQuery}
                onQuery={store.setSkillQuery}
                onOpenSkill={openSkill}
                onMove={store.move}
                onPort={(ids, cli, replace) => store.port(ids, cli, replace)}
                onDelete={store.remove}
                onEnhance={store.enhance}
                onPackage={store.packageSkill}
              />
            )}
            {view === 'create' && store.settings && (
              <Create
                workflows={store.workflows}
                settings={store.settings}
                onLaunch={async (spec) => {
                  const ok = await store.create(spec);
                  if (ok) setView('jobs');
                  return ok;
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
                onSync={store.syncMarket}
                clis={store.clis}
                localSkills={store.skills}
              />
            )}
            {view === 'library' && detailId && <ConfigPage key={detailId} id={detailId} />}
            {view === 'library' && !detailId && (
              <Library
                sources={store.sources}
                entries={store.entries}
                onAddSource={store.addSource}
                onFetchSource={store.fetchSource}
                onFetchOfficial={store.fetchOfficial}
                onRemoveSource={store.removeSource}
                onBuild={store.buildConfig}
                onOpenConfig={(id) => navigate(`/configs/${encodeURIComponent(id)}`)}
              />
            )}
            {view === 'workflows' && <Workflows selected={detailId} />}
            {view === 'analyze' && <Analyze />}
            {view === 'environment' && <Environment />}
            {view === 'jobs' && <Jobs jobs={store.jobs} onCancel={store.cancelJob} onRetry={store.retryJob} />}
            {view === 'settings' && (
              <Settings
                settings={store.settings}
                onSetKey={store.setKey}
                onSetDefaults={store.setDefaults}
                onReprobe={store.reprobe}
              />
            )}
            </Suspense>
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

      <Toaster position="bottom-right" theme="dark" />
    </TooltipProvider>
  );
}

function ButtonNavigation({ open, onToggle }: { open: boolean; onToggle: () => void }) {
  return <button aria-label={open ? 'Close navigation' : 'Open navigation'} aria-expanded={open} aria-controls="main-navigation" onClick={onToggle} className="md:hidden p-2 rounded border border-border">{open ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}</button>;
}
