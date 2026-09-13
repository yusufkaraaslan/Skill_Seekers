import { useCallback, useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import { useNavigate } from 'react-router';
import { toast } from 'sonner';
import {
  CliChip, InstallSet, OriginTag, Pager, Panel, QualityMeter, ScopeTag, StatusPill,
} from '@/components/hud';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription,
  AlertDialogFooter, AlertDialogHeader, AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { usePagination } from '@/hooks/use-pagination';
import { api } from '@/lib/api';
import type { EnhanceStatus, SkillDetail } from '@/lib/api';
import { EXPORT_TARGETS, SOURCE_META, fmtSize, qualityColor } from '@/lib/data';
import type { CliId, Job, SkillFile } from '@/lib/data';
import { useStore } from '@/lib/store';
import { cn } from '@/lib/utils';
import {
  ArrowLeftRight, Copy, FolderInput, MoreHorizontal, Package, Pencil, Sparkles, Trash2, UploadCloud,
} from 'lucide-react';

// ── static tables ───────────────────────────────────────────────────────────

const TABS: [string, string][] = [
  ['overview', 'Overview'],
  ['content', 'SKILL.md'],
  ['files', 'Files'],
  ['installs', 'Installs'],
  ['enhance', 'Enhance'],
  ['analysis', 'Analysis'],
  ['export', 'Export'],
  ['history', 'History'],
];

// The backend scores four dimensions under short keys; these are the reader's
// names for them (see registry.skill_quality_breakdown).
const QUALITY_LABEL: Record<string, string> = {
  frontmatter: 'frontmatter',
  structure: 'section structure',
  examples: 'code examples',
  links: 'reference links',
};

// The five C3.x analysers, in the order the runner executes them. `quality` is
// deliberately not here: it has its own endpoint (POST /skills/{id}/quality)
// that writes a report next to the skill rather than an analysis manifest.
const ANALYSIS_TOOLS: { tool: string; label: string; tag: string; hint: string }[] = [
  { tool: 'patterns', label: 'Design patterns', tag: 'C3.1', hint: 'GoF patterns across 9 languages' },
  { tool: 'tests', label: 'Test examples', tag: 'C3.2', hint: 'usage examples pulled from test files' },
  { tool: 'guides', label: 'How-to guides', tag: 'C3.3', hint: 'needs the tests tool in the same run — use Run all' },
  { tool: 'config', label: 'Config patterns', tag: 'C3.4', hint: 'package.json, tsconfig, eslint, babel…' },
  { tool: 'router', label: 'Architecture router', tag: 'C3.5', hint: 'only for skills that carry sub-skill configs' },
];

const UPLOAD_CARDS: { target: string; label: string; env: string; fmt: string }[] = [
  { target: 'claude', label: 'Claude', env: 'ANTHROPIC_API_KEY', fmt: 'zip' },
  { target: 'openai', label: 'OpenAI', env: 'OPENAI_API_KEY', fmt: 'zip' },
  { target: 'gemini', label: 'Gemini', env: 'GOOGLE_API_KEY', fmt: 'tar.gz' },
];

// One connection field per database. `key` is the option name the backend maps
// to an upload_skill flag (web/runner.py:UPLOAD_OPTION_FLAGS); `field` is the
// human name, and doubles as the input's accessible name.
//
// `upload` is whether `upload_skill` can actually reach the store:
// get_upload_platforms() is derived from each adaptor's supports_upload(), and
// FAISS/Qdrant answer no — a job for them dies in argparse. Weaviate takes
// `weaviate_url`, not `cluster_url`: the adaptor only reads cluster_url on the
// Weaviate Cloud branch (use_cloud AND an api key), so a plain URL sent under
// that name is silently dropped.
const VECTOR_DBS: { id: string; label: string; field: string; key: string; placeholder: string; upload: boolean }[] = [
  { id: 'chroma', label: 'ChromaDB', field: 'persist directory', key: 'persist_directory', placeholder: './chroma_db', upload: true },
  { id: 'faiss', label: 'FAISS', field: 'index path', key: 'persist_directory', placeholder: './skill.faiss', upload: false },
  { id: 'qdrant', label: 'Qdrant', field: 'server url', key: 'cluster_url', placeholder: 'http://localhost:6333', upload: false },
  { id: 'weaviate', label: 'Weaviate', field: 'cluster url', key: 'weaviate_url', placeholder: 'http://localhost:8080', upload: true },
];

// argparse `choices` on --embedding-function (cli/arguments/upload.py); any
// other value fails the job, so the UI offers exactly these.
const EMBEDDING_FUNCTIONS = ['none', 'openai', 'sentence-transformers'];

const TRANSLATE_LANGS: [string, string][] = [
  ['tr', 'Türkçe'], ['de', 'Deutsch'], ['ja', '日本語'],
  ['es', 'Español'], ['fr', 'Français'], ['zh', '中文'],
];

// `.enhancement_status.json` is free-form; read known keys defensively.
const readString = (o: EnhanceStatus | null, key: string): string =>
  o && typeof o[key] === 'string' ? (o[key] as string) : '';
const readNumber = (o: EnhanceStatus | null, key: string): number | null =>
  o && typeof o[key] === 'number' ? (o[key] as number) : null;

const ENHANCE_PILL: Record<string, string> = {
  pending: 'queued', running: 'running', completed: 'done', failed: 'failed',
};

function fileKind(path: string): string {
  const base = path.split('/').pop() ?? path;
  if (base === 'SKILL.md') return 'entry';
  if (base.startsWith('.')) return 'sidecar';
  if (path.startsWith('references/')) return 'reference';
  if (path.startsWith('scripts/')) return 'script';
  if (path.startsWith('assets/')) return 'asset';
  return 'file';
}

// ── small shared presentation bits ──────────────────────────────────────────

function CardTitle({ children }: { children: ReactNode }) {
  return (
    <div className="mb-3 flex items-center gap-2">
      <span className="inline-block h-3.5 w-[3px] bg-primary shadow-[0_0_8px_hsl(187_92%_50%/0.8)]" />
      <h3 className="font-mono-hud text-[12px] font-semibold uppercase tracking-[0.18em]">{children}</h3>
    </div>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="space-y-1 min-w-0">
      <div className="font-mono-hud text-[10px] uppercase tracking-[0.2em] text-muted-foreground">{label}</div>
      <div className="break-all text-[13px]">{children}</div>
    </div>
  );
}

function Stat({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="flex flex-col gap-1.5 px-4 py-3">
      <span className="font-mono-hud text-[10px] uppercase tracking-[0.2em] text-muted-foreground">{label}</span>
      <div className="font-mono-hud text-[13px]">{children}</div>
    </div>
  );
}

function Bar({ score }: { score: number }) {
  const color = qualityColor(score);
  return (
    <div className="h-[3px] w-full overflow-hidden rounded-full bg-secondary">
      <div className="h-full rounded-full" style={{ width: `${Math.max(0, Math.min(100, score))}%`, background: `hsl(${color})`, boxShadow: `0 0 6px hsl(${color})` }} />
    </div>
  );
}

const copyText = (value: string) =>
  navigator.clipboard.writeText(value)
    .then(() => toast.success('Copied'))
    .catch(() => toast.error('Copy unavailable', { description: value }));

// ── page ────────────────────────────────────────────────────────────────────

export default function SkillPage({ id }: { id: string }) {
  const store = useStore();
  const navigate = useNavigate();
  const [detail, setDetail] = useState<SkillDetail | null>(null);
  const [history, setHistory] = useState<Job[]>([]);
  const [error, setError] = useState('');
  const [tab, setTab] = useState('overview');

  // SKILL.md + file list share one payload, fetched the first time either tab
  // is opened rather than on mount (a skill can carry a very large SKILL.md).
  const [content, setContent] = useState<{ content: string; revision: string; files?: SkillFile[] } | null>(null);
  const [contentError, setContentError] = useState('');
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState('');

  const [moveOpen, setMoveOpen] = useState(false);
  const [archiveOpen, setArchiveOpen] = useState(false);

  const load = useCallback(
    () => Promise.all([api.skillDetail(id), api.skillHistory(id)])
      .then(([d, h]) => { setDetail(d); setHistory(h); setError(''); })
      .catch((e) => setError(e instanceof Error ? e.message : String(e))),
    [id],
  );

  // Jobs move on their own (the store polls), and every one of them can change
  // what this page shows — quality, installs, analysis, history. Re-read on a
  // job *signature* rather than the array identity, so an unchanged poll costs
  // nothing.
  const jobsKey = store.jobs.map((j) => `${j.id}:${j.status}:${j.progress}`).join(',');
  useEffect(() => { load(); }, [load, jobsKey]);

  const needsContent = tab === 'content' || tab === 'files';
  useEffect(() => {
    if (!needsContent || content || contentError) return;
    let active = true;
    api.skillContent(id)
      .then((data) => { if (active) { setContent(data); setDraft(data.content); } })
      .catch((e) => { if (active) setContentError(e instanceof Error ? e.message : String(e)); });
    return () => { active = false; };
  }, [id, needsContent, content, contentError]);

  const dirty = content !== null && editing && draft !== content.content;
  useEffect(() => {
    if (!dirty) return;
    const warn = (e: BeforeUnloadEvent) => { e.preventDefault(); e.returnValue = ''; };
    window.addEventListener('beforeunload', warn);
    return () => window.removeEventListener('beforeunload', warn);
  }, [dirty]);
  // beforeunload only covers a full page load. Client-side navigation (sidebar,
  // header search, breadcrumb) reads this instead.
  const { setDirty } = store;
  useEffect(() => { setDirty(dirty); }, [dirty, setDirty]);
  useEffect(() => () => setDirty(false), [setDirty]);

  // A config path in the sidecar is only a link when the library actually holds
  // that config; otherwise it stays plain text.
  const configEntry = useMemo(() => {
    const want = (detail?.config ?? '').replace(/\\/g, '/');
    if (!want) return null;
    const base = want.split('/').pop() ?? want;
    return store.entries.find((e) => (e.path ?? '').replace(/\\/g, '/').endsWith(want) || e.name === base) ?? null;
  }, [detail?.config, store.entries]);

  const leaveEditor = () => {
    if (dirty && !window.confirm('Discard unsaved SKILL.md edits?')) return false;
    setDraft(content?.content ?? '');
    setEditing(false);
    return true;
  };

  const changeTab = (next: string) => {
    if (dirty && !leaveEditor()) return;
    setTab(next);
  };

  const save = async () => {
    if (!content) return;
    // A rejected save (409 conflict, running enhancement) keeps the editor open
    // with the draft intact — the store surfaces the reason as a toast.
    if (!(await store.saveContent(id, draft, content.revision))) return;
    try {
      const fresh = await api.skillContent(id);
      setContent(fresh);
      setDraft(fresh.content);
      setEditing(false);
      setContentError('');
    } catch (e) {
      setContentError(`Saved, but reload failed: ${e instanceof Error ? e.message : String(e)}`);
    }
  };

  if (error) {
    return (
      <p role="alert" className="rounded border border-destructive p-3">
        {error} <button className="underline" onClick={() => load()}>Retry</button>
      </p>
    );
  }
  if (!detail) return <p role="status">Loading skill…</p>;

  const owned = detail.origin === 'seeker' && detail.editable !== false;
  const source = SOURCE_META[detail.sourceType] ?? { label: detail.sourceType, icon: '◆' };
  const lastJob = history[0];

  return (
    <div className="space-y-4 animate-flicker">
      <nav aria-label="Breadcrumb" className="flex items-center gap-2 font-mono-hud text-[11px] uppercase tracking-[0.15em]">
        <button onClick={() => { if (store.confirmLeave()) navigate('/skills'); }} className="text-primary hover:underline">‹ Skills</button>
        <span className="text-muted-foreground">/ {detail.name}</span>
      </nav>

      <Panel className="p-5">
        {/* ── header ── */}
        <div className="flex flex-wrap items-start gap-4">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-md border border-primary/40 bg-primary/[0.08] font-mono-hud text-lg text-primary/80">
            {source.icon}
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-xl font-semibold tracking-tight">{detail.name}</h1>
              <ScopeTag scope={detail.scope} project={store.projects.find((p) => p.id === detail.projectId)?.name} />
              <OriginTag origin={detail.origin} pluginName={detail.pluginName} />
              <span className="font-mono-hud text-[10px] text-muted-foreground">
                v{detail.version} · {source.label} · updated {detail.updatedAt}
              </span>
            </div>
            <p className="mt-1.5 max-w-[720px] text-[13px] text-muted-foreground">{detail.description}</p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {owned && (
              <Button size="sm" disabled={store.pending} onClick={() => store.enhance(id)} className="font-mono-hud text-[11px] uppercase tracking-wider">
                <Sparkles className="mr-1.5 h-3.5 w-3.5" /> Enhance
              </Button>
            )}
            <Button size="sm" variant="outline" onClick={() => changeTab('export')} className="font-mono-hud text-[11px] uppercase tracking-wider">
              <Package className="mr-1.5 h-3.5 w-3.5" /> Package
            </Button>
            <Button size="sm" variant="outline" onClick={() => changeTab('installs')} className="font-mono-hud text-[11px] uppercase tracking-wider">
              <ArrowLeftRight className="mr-1.5 h-3.5 w-3.5" /> Install to CLI
            </Button>
            <Button size="sm" variant="outline" onClick={() => changeTab('export')} className="font-mono-hud text-[11px] uppercase tracking-wider">
              <UploadCloud className="mr-1.5 h-3.5 w-3.5" /> Upload
            </Button>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button aria-label="More actions" className="rounded border border-border p-1.5 text-muted-foreground hover:bg-secondary hover:text-foreground">
                  <MoreHorizontal className="h-4 w-4" />
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-52 font-mono-hud text-xs">
                <DropdownMenuItem disabled={!owned} onClick={() => setMoveOpen(true)}>
                  <FolderInput className="mr-2 h-3.5 w-3.5" /> Move to…
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem disabled={!owned} className="text-destructive focus:text-destructive" onClick={() => setArchiveOpen(true)}>
                  <Trash2 className="mr-2 h-3.5 w-3.5" /> Archive skill
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>

        {/* ── stats strip ── */}
        <div className="mt-4 grid grid-cols-2 gap-px overflow-hidden rounded border border-border bg-border sm:grid-cols-3 lg:grid-cols-5">
          <div className="bg-card"><Stat label="quality"><QualityMeter q={detail.quality} /></Stat></div>
          <div className="bg-card"><Stat label="footprint">{fmtSize(detail.sizeKb)}</Stat></div>
          <div className="bg-card"><Stat label="files">{detail.fileCount}</Stat></div>
          <div className="bg-card"><Stat label="installed in"><InstallSet installs={detail.installs} /></Stat></div>
          <div className="bg-card">
            <Stat label="last job">
              {lastJob
                ? <span className="flex flex-wrap items-center gap-2"><StatusPill status={lastJob.status} /><span className="text-muted-foreground">{lastJob.type}</span></span>
                : <span className="text-muted-foreground">none</span>}
            </Stat>
          </div>
        </div>

        {/* ── tabs ── */}
        <Tabs value={tab} onValueChange={changeTab} className="mt-5">
          <div className="overflow-x-auto">
            <TabsList className="h-auto w-full justify-start gap-1 rounded-none border-b border-border bg-transparent p-0">
              {TABS.map(([value, label]) => (
                <TabsTrigger
                  key={value}
                  value={value}
                  className="flex-none rounded-none border-0 border-b-2 border-transparent px-3 py-2 font-mono-hud text-[11px] uppercase tracking-[0.12em] text-muted-foreground data-[state=active]:border-primary data-[state=active]:bg-transparent data-[state=active]:text-primary data-[state=active]:shadow-none"
                >
                  {label}
                </TabsTrigger>
              ))}
            </TabsList>
          </div>

          <TabsContent value="overview" className="py-4">
            <OverviewTab
              detail={detail}
              history={history}
              source={source.label}
              configHref={configEntry ? `/configs/${encodeURIComponent(configEntry.id)}` : null}
              onTab={changeTab}
            />
          </TabsContent>

          <TabsContent value="content" className="py-4">
            <ContentTab
              content={content}
              error={contentError}
              editing={editing}
              owned={owned}
              draft={draft}
              onDraft={setDraft}
              onEdit={() => setEditing(true)}
              onCancel={leaveEditor}
              onSave={save}
            />
          </TabsContent>

          <TabsContent value="files" className="py-4">
            <FilesTab id={id} files={content?.files ?? []} loading={!content && !contentError} error={contentError} total={detail.fileCount} />
          </TabsContent>

          <TabsContent value="installs" className="py-4">
            <InstallsTab id={id} detail={detail} />
          </TabsContent>

          <TabsContent value="enhance" className="py-4">
            <EnhanceTab id={id} detail={detail} history={history} owned={owned} onNavigate={navigate} />
          </TabsContent>

          <TabsContent value="analysis" className="py-4">
            <AnalysisTab id={id} detail={detail} />
          </TabsContent>

          <TabsContent value="export" className="py-4">
            <ExportTab id={id} onNavigate={navigate} />
          </TabsContent>

          <TabsContent value="history" className="py-4">
            <HistoryTab history={history} />
          </TabsContent>
        </Tabs>
      </Panel>

      {/* ── move ── */}
      <Dialog open={moveOpen} onOpenChange={(open) => { if (!open && !store.pending) setMoveOpen(false); }}>
        <DialogContent className="!fixed hud-panel border-border sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="font-mono-hud text-sm uppercase tracking-[0.2em] text-primary">// move {detail.name}</DialogTitle>
            <DialogDescription className="text-xs text-muted-foreground">
              Organize the skill within this HUD. Project assignment does not change CLI installation paths or which sessions load it.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2 py-2">
            {[{ id: 'global', name: '◈ Global', path: 'Unassigned in this workspace' },
              ...store.projects.map((p) => ({ id: p.id, name: `▣ ${p.name}`, path: p.path }))].map((dest) => (
              <button
                key={dest.id}
                disabled={store.pending}
                onClick={async () => { if (await store.move([id], dest.id)) setMoveOpen(false); }}
                className="flex w-full items-center justify-between rounded border border-border bg-secondary/40 px-3 py-2.5 text-left transition-colors hover:border-primary/50 disabled:opacity-50"
              >
                <span>
                  <span className="block font-mono-hud text-xs font-semibold">{dest.name}</span>
                  <span className="block font-mono-hud text-[10px] text-muted-foreground">{dest.path}</span>
                </span>
                <FolderInput className="h-3.5 w-3.5 text-muted-foreground" />
              </button>
            ))}
          </div>
        </DialogContent>
      </Dialog>

      {/* ── archive ── */}
      <AlertDialog open={archiveOpen} onOpenChange={setArchiveOpen}>
        <AlertDialogContent className="!fixed hud-panel border-border">
          <AlertDialogHeader>
            <AlertDialogTitle className="font-mono-hud text-sm uppercase tracking-[0.2em] text-destructive">
              // archive {detail.name}?
            </AlertDialogTitle>
            <AlertDialogDescription className="text-xs text-muted-foreground">
              Moves the source files to the recoverable archive and removes the copies Seeker installed from this source.
              Installations Seeker does not own stay untouched. Restore from “Archived skills” on the Skills screen.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="font-mono-hud text-xs">Cancel</AlertDialogCancel>
            <AlertDialogAction
              disabled={store.pending}
              className="bg-destructive font-mono-hud text-xs uppercase tracking-wider text-destructive-foreground hover:bg-destructive/90"
              onClick={async (e) => { e.preventDefault(); if (await store.remove([id])) { setArchiveOpen(false); navigate('/skills'); } }}
            >
              Archive
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

// ── Overview ────────────────────────────────────────────────────────────────

function OverviewTab({ detail, history, source, configHref, onTab }: {
  detail: SkillDetail;
  history: Job[];
  source: string;
  configHref: string | null;
  onTab: (tab: string) => void;
}) {
  const navigate = useNavigate();
  const created = history.find((j) => j.type === 'create');
  const status = detail.enhanceStatus;
  const enhancedAt = readString(status, 'timestamp');
  const enhanceState = readString(status, 'status');

  return (
    <div className="grid gap-4 lg:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
      <Panel corners={false} className="p-4">
        <CardTitle>Provenance</CardTitle>
        <div className="grid gap-3 sm:grid-cols-2">
          <Field label="source">
            <span className="text-muted-foreground">{source} · </span>{detail.source}
          </Field>
          {detail.config && (
            <Field label="config">
              {configHref
                ? <button className="text-primary hover:underline" onClick={() => navigate(configHref)}>{detail.config}</button>
                : <span>{detail.config} <span className="text-muted-foreground">(not in the config library)</span></span>}
            </Field>
          )}
          <Field label="location">{detail.dir ?? '—'}</Field>
          <Field label="built by">
            {created ? `job ${created.type} · ${created.startedAt}` : <span className="text-muted-foreground">not built in this workspace</span>}
          </Field>
          <Field label="enhancement">
            {enhanceState
              ? `${enhanceState}${enhancedAt ? ` · ${enhancedAt}` : ''}`
              : <span className="text-muted-foreground">no enhancement pass recorded</span>}
          </Field>
          <Field label="tags">
            {detail.tags.length ? detail.tags.join(', ') : <span className="text-muted-foreground">none</span>}
          </Field>
        </div>
      </Panel>

      <Panel corners={false} className="p-4">
        <CardTitle>Quality breakdown</CardTitle>
        {detail.qualityBreakdown.length === 0 && (
          <p className="text-xs text-muted-foreground">No quality report yet — run a check from the Analysis tab.</p>
        )}
        <div className="space-y-3">
          {detail.qualityBreakdown.map((dim) => (
            <div key={dim.label} className="space-y-1.5">
              <div className="flex items-center justify-between font-mono-hud text-[11px]">
                <span className="text-muted-foreground">{QUALITY_LABEL[dim.label] ?? dim.label}</span>
                <span style={{ color: `hsl(${qualityColor(dim.score)})` }}>{dim.score}</span>
              </div>
              <Bar score={dim.score} />
            </div>
          ))}
        </div>
      </Panel>

      <Panel corners={false} className="p-4 lg:col-span-2">
        <CardTitle>Recent ops on this skill</CardTitle>
        {history.length === 0 && <p className="text-xs text-muted-foreground">No jobs have touched this skill yet.</p>}
        <div className="space-y-2">
          {history.slice(0, 4).map((job) => (
            <div key={job.id} className="flex flex-wrap items-center gap-3 border-b border-border/60 pb-2 text-[13px] last:border-0">
              <time className="font-mono-hud text-[11px] text-muted-foreground">{job.startedAt}</time>
              <span className="font-mono-hud text-[11px] uppercase tracking-wider text-primary">{job.type}</span>
              <span className="min-w-0 flex-1 break-words text-muted-foreground">{job.detail}</span>
              <StatusPill status={job.status} />
            </div>
          ))}
        </div>
        {history.length > 0 && (
          <button className="mt-3 font-mono-hud text-[11px] uppercase tracking-wider text-primary hover:underline" onClick={() => onTab('history')}>
            Full history →
          </button>
        )}
      </Panel>
    </div>
  );
}

// ── SKILL.md ────────────────────────────────────────────────────────────────

function ContentTab({ content, error, editing, owned, draft, onDraft, onEdit, onCancel, onSave }: {
  content: { content: string; revision: string } | null;
  error: string;
  editing: boolean;
  owned: boolean;
  draft: string;
  onDraft: (value: string) => void;
  onEdit: () => void;
  onCancel: () => void;
  onSave: () => void;
}) {
  const { pending } = useStore();
  return (
    <Panel corners={false} className="p-4">
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <CardTitle>SKILL.md</CardTitle>
        <span className="font-mono-hud text-[10px] text-muted-foreground">
          {content ? `revision ${content.revision.slice(0, 8)}… · ${content.content.length} chars` : ''}
        </span>
        <div className="ml-auto flex items-center gap-2">
          <Button size="sm" variant="outline" disabled={!content} onClick={() => content && copyText(content.content)} className="font-mono-hud text-[11px] uppercase tracking-wider">
            <Copy className="mr-1.5 h-3.5 w-3.5" /> Copy
          </Button>
          {owned && !editing && (
            <Button size="sm" disabled={!content || pending} onClick={onEdit} className="font-mono-hud text-[11px] uppercase tracking-wider">
              <Pencil className="mr-1.5 h-3.5 w-3.5" /> Edit
            </Button>
          )}
          {owned && editing && (
            <>
              <Button size="sm" variant="outline" disabled={pending} onClick={onCancel} className="font-mono-hud text-[11px] uppercase tracking-wider">Cancel</Button>
              <Button size="sm" disabled={pending} onClick={onSave} className="font-mono-hud text-[11px] uppercase tracking-wider">Save</Button>
            </>
          )}
        </div>
      </div>

      {error && <p role="alert" className="mb-3 text-sm text-destructive">{error}</p>}
      {!content && !error && <p role="status">Loading complete SKILL.md…</p>}
      {content && (editing
        ? <textarea
            aria-label="SKILL.md content"
            value={draft}
            onChange={(e) => onDraft(e.target.value)}
            spellCheck={false}
            className="min-h-96 w-full rounded border border-border bg-background p-3 font-mono-hud text-sm outline-none focus:border-primary/50"
          />
        : <pre className="max-h-[32rem] overflow-auto whitespace-pre-wrap break-words rounded border border-border bg-black/30 p-4 font-mono-hud text-sm">{content.content}</pre>
      )}
      {owned && (
        <p className="mt-3 text-xs text-muted-foreground">
          Saves are revision-checked: if another process changes the file first, your draft stays open and you reload before saving.
        </p>
      )}
      {!owned && (
        <p className="mt-3 text-xs text-muted-foreground">This skill is managed outside Skill Seekers, so it is read-only here.</p>
      )}
    </Panel>
  );
}

// ── Files ───────────────────────────────────────────────────────────────────

function FilesTab({ id, files, loading, error, total }: {
  id: string;
  files: SkillFile[];
  loading: boolean;
  error: string;
  total: number;
}) {
  const pager = usePagination(files, 'skill-files', id);
  if (error) return <p role="alert" className="rounded border border-destructive p-3">{error}</p>;
  if (loading) return <p role="status">Loading file list…</p>;
  if (!files.length) return <Panel corners={false} className="p-6"><p className="text-sm text-muted-foreground">This skill is a single file — no bundled references, scripts or assets.</p></Panel>;

  return (
    <Panel corners={false} className="overflow-hidden">
      <div className="overflow-x-auto" role="region" aria-label="Skill files" tabIndex={0}>
        <table className="w-full min-w-[520px] text-sm">
          <thead>
            <tr className="border-b border-border font-mono-hud text-[10px] uppercase tracking-[0.15em] text-muted-foreground">
              <th className="px-3 py-2.5 text-left font-medium">path</th>
              <th className="px-3 py-2.5 text-left font-medium">kind</th>
              <th className="px-3 py-2.5 text-left font-medium">size</th>
              <th className="w-24 px-3 py-2.5" />
            </tr>
          </thead>
          <tbody>
            {pager.slice.map((file) => (
              <tr key={file.path} className="border-b border-border/60">
                <td className="break-all px-3 py-2.5 font-mono-hud text-[12px]">{file.path}</td>
                <td className="px-3 py-2.5 font-mono-hud text-[11px] text-muted-foreground">{fileKind(file.path)}</td>
                <td className="px-3 py-2.5 font-mono-hud text-[11px] text-muted-foreground">{file.size}</td>
                <td className="px-3 py-2.5 text-right">
                  <Button size="sm" variant="ghost" className="h-7 font-mono-hud text-[10px] uppercase tracking-wider" onClick={() => copyText(file.path)}>
                    Copy path
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="px-3 py-2 font-mono-hud text-[10px] text-muted-foreground">
        {/* registry.list_skill_files stops at 200, and fileCount counts the same
            capped list — say so rather than implying a complete inventory. */}
        {total} file{total === 1 ? '' : 's'}{total >= 200 ? ' · the detail view lists at most 200' : ''}
      </div>
      <Pager page={pager.page} pageCount={pager.pageCount} pageSize={pager.pageSize} total={pager.total} onPage={pager.setPage} onPageSize={pager.setPageSize} />
    </Panel>
  );
}

// ── Installs ────────────────────────────────────────────────────────────────

function InstallsTab({ id, detail }: { id: string; detail: SkillDetail }) {
  const store = useStore();
  const [selected, setSelected] = useState<CliId[]>([]);
  const [replace, setReplace] = useState(false);
  const installations = detail.installations ?? [];
  const installedIds = installations.map((i) => i.cli);
  // Only CLIs actually present on this machine: writing into a missing tool's
  // directory would make the HUD report that tool as detected.
  const available = store.clis.filter((c) => c.detected && !installedIds.includes(c.id));

  const toggle = (cli: CliId) =>
    setSelected((s) => (s.includes(cli) ? s.filter((c) => c !== cli) : [...s, cli]));

  // `port` shares one in-flight mutation guard with every other store call, so
  // the selected CLIs are installed one after another, not in parallel.
  const installSelected = async () => {
    for (const cli of selected) {
      if (!(await store.port([id], cli, replace))) return;
    }
    setSelected([]);
  };

  return (
    <div className="grid gap-4 lg:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
      <Panel corners={false} className="overflow-hidden">
        <div className="p-4 pb-0"><CardTitle>Installed locations</CardTitle></div>
        <div className="overflow-x-auto" role="region" aria-label="Installed locations" tabIndex={0}>
          <table className="w-full min-w-[560px] text-sm">
            <thead>
              <tr className="border-b border-border font-mono-hud text-[10px] uppercase tracking-[0.15em] text-muted-foreground">
                <th className="px-3 py-2.5 text-left font-medium">cli</th>
                <th className="px-3 py-2.5 text-left font-medium">location</th>
                <th className="px-3 py-2.5 text-left font-medium">owned</th>
                <th className="w-28 px-3 py-2.5" />
              </tr>
            </thead>
            <tbody>
              {installations.map((install) => (
                <tr key={`${install.cli}:${install.path}`} className="border-b border-border/60">
                  <td className="px-3 py-2.5"><CliChip id={install.cli} /></td>
                  <td className="break-all px-3 py-2.5 font-mono-hud text-[12px]">{install.path}</td>
                  <td className="px-3 py-2.5 font-mono-hud text-[11px] text-muted-foreground">
                    {install.owned === 'true' ? 'seeker copy' : 'external copy'}
                  </td>
                  <td className="px-3 py-2.5 text-right">
                    <Button
                      size="sm"
                      variant="outline"
                      disabled={store.pending}
                      className="h-7 font-mono-hud text-[10px] uppercase tracking-wider"
                      onClick={() => store.port([id], install.cli, true)}
                    >
                      Reinstall
                    </Button>
                  </td>
                </tr>
              ))}
              {installations.length === 0 && (
                <tr>
                  <td colSpan={4} className="px-3 py-8 text-center font-mono-hud text-xs text-muted-foreground">
                    ∅ this skill is not installed in any CLI yet
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        <p className="border-t border-border px-3 py-2 text-xs text-muted-foreground">
          Removing a single CLI copy is not available from the HUD; “Archive skill” (⋯ menu) removes the source and every Seeker-owned copy.
        </p>
      </Panel>

      <Panel corners={false} className="p-4">
        <CardTitle>Install to more CLIs</CardTitle>
        {available.length === 0 && (
          <p className="text-xs text-muted-foreground">Every detected CLI already carries this skill.</p>
        )}
        <div className="space-y-2">
          {available.map((cli) => (
            <label key={cli.id} className="flex cursor-pointer items-center gap-3 rounded border border-border bg-secondary/30 px-3 py-2">
              <Checkbox aria-label={`Install to ${cli.name}`} checked={selected.includes(cli.id)} onCheckedChange={() => toggle(cli.id)} />
              <CliChip id={cli.id} />
              <span className="min-w-0">
                <span className="block text-[13px]">{cli.name}</span>
                <span className="block break-all font-mono-hud text-[10px] text-muted-foreground">{cli.globalPath}</span>
              </span>
            </label>
          ))}
        </div>
        {available.length > 0 && (
          <>
            <label className="mt-3 flex items-center gap-2 text-xs">
              <Checkbox checked={replace} onCheckedChange={(v) => setReplace(v === true)} />
              Replace existing destination copies
            </label>
            {replace && <p className="mt-1 text-xs text-destructive">Existing destination content will be replaced. The source is preserved.</p>}
            <Button
              className="mt-3 w-full font-mono-hud text-[11px] uppercase tracking-wider"
              disabled={store.pending || selected.length === 0}
              onClick={installSelected}
            >
              Install to {selected.length} CLI(s)
            </Button>
          </>
        )}
      </Panel>
    </div>
  );
}

// ── Enhance ─────────────────────────────────────────────────────────────────

function EnhanceTab({ id, detail, history, owned, onNavigate }: {
  id: string;
  detail: SkillDetail;
  history: Job[];
  owned: boolean;
  onNavigate: (to: string) => void;
}) {
  const store = useStore();
  const [langs, setLangs] = useState<string[]>([]);
  const status = detail.enhanceStatus;
  const state = readString(status, 'status');
  const progress = readNumber(status, 'progress');
  const statusError = readString(status, 'error');
  // The pass re-runs whatever failed last; `create` counts because an
  // interrupted build leaves the skill half-enhanced too.
  const resumable = history.find((j) => j.status === 'failed' && (j.type === 'enhance' || j.type === 'create'));
  const agent = String(store.settings?.defaults.default_agent ?? 'claude');
  const lastCheck = history.find((j) => j.type === 'update');

  const toggleLang = (code: string) =>
    setLangs((l) => (l.includes(code) ? l.filter((c) => c !== code) : [...l, code]));

  return (
    <div className="space-y-4">
      {!owned && (
        <p className="rounded border border-border bg-secondary/30 p-3 text-xs text-muted-foreground">
          This skill was not built by Skill Seekers, so enhancement, update and translation are unavailable.
        </p>
      )}

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        <Panel corners={false} className="p-4">
          <CardTitle>Enhancement status</CardTitle>
          <div className="grid gap-3 sm:grid-cols-2">
            <Field label="status">
              <StatusPill status={ENHANCE_PILL[state] ?? (state || 'idle')} />
            </Field>
            <Field label="last pass">{readString(status, 'timestamp') || <span className="text-muted-foreground">never</span>}</Field>
            <Field label="message">{readString(status, 'message') || <span className="text-muted-foreground">—</span>}</Field>
            <Field label="quality">{detail.quality}</Field>
          </div>
          {progress !== null && progress > 0 && progress < 1 && (
            <progress aria-label="Enhancement progress" max={100} value={Math.round(progress * 100)} className="mt-3 h-2 w-full" />
          )}
          {statusError && <p role="alert" className="mt-3 text-sm text-destructive">{statusError}</p>}
          <div className="mt-4 flex flex-wrap gap-2">
            <Button
              disabled={!owned || store.pending}
              onClick={() => store.enhance(id)}
              className="font-mono-hud text-[11px] uppercase tracking-wider"
            >
              <Sparkles className="mr-1.5 h-3.5 w-3.5" /> Run enhancement
            </Button>
            <Button
              variant="outline"
              disabled={!resumable || store.pending}
              onClick={() => resumable && store.retryJob(resumable.id)}
              className="font-mono-hud text-[11px] uppercase tracking-wider"
            >
              Resume interrupted pass
            </Button>
          </div>
          {!resumable && <p className="mt-2 text-xs text-muted-foreground">No interrupted enhance or create job to resume.</p>}
        </Panel>

        <Panel corners={false} className="p-4">
          <CardTitle>Pass profile</CardTitle>
          <p className="mb-3 text-xs text-muted-foreground">
            The pass runs with this workspace's saved profile — a skill page never changes a workspace-wide default.
          </p>
          <div className="grid gap-3 sm:grid-cols-2">
            <Field label="agent">{agent}</Field>
            <Field label="timeout">600 s</Field>
            <Field label="enhance level"><span className="text-muted-foreground">chosen at create time</span></Field>
            <Field label="workflow"><span className="text-muted-foreground">chosen at create time</span></Field>
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            <Button variant="outline" onClick={() => onNavigate('/settings')} className="font-mono-hud text-[11px] uppercase tracking-wider">
              Change default in Settings
            </Button>
            <Button variant="ghost" onClick={() => onNavigate('/workflows')} className="font-mono-hud text-[11px] uppercase tracking-wider">
              Browse workflows
            </Button>
          </div>
        </Panel>
      </div>

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        <Panel corners={false} className="p-4">
          <CardTitle>Update from source</CardTitle>
          <p className="text-xs text-muted-foreground">
            Re-scrape <span className="break-all font-mono-hud">{detail.source}</span> and rebuild. Check first to see what moved upstream; the result lands in Jobs.
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            <Button variant="outline" disabled={!owned || store.pending} onClick={() => store.updateSkill(id, false)} className="font-mono-hud text-[11px] uppercase tracking-wider">
              Check for changes
            </Button>
            <Button disabled={!owned || store.pending} onClick={() => store.updateSkill(id, true)} className="font-mono-hud text-[11px] uppercase tracking-wider">
              Update skill
            </Button>
          </div>
          <p className="mt-2 text-xs text-muted-foreground">
            {lastCheck ? `last run ${lastCheck.startedAt} · ${lastCheck.status}` : 'no upstream check recorded yet'}
          </p>
        </Panel>

        <Panel corners={false} className="p-4">
          <CardTitle>Translations</CardTitle>
          <p className="mb-3 text-xs text-muted-foreground">Writes a translated copy of the skill per language (multilang).</p>
          <div className="flex flex-wrap gap-2">
            {TRANSLATE_LANGS.map(([code, label]) => (
              <button
                key={code}
                aria-pressed={langs.includes(code)}
                onClick={() => toggleLang(code)}
                className={cn(
                  'rounded border px-2.5 py-1 font-mono-hud text-[11px] transition-colors',
                  langs.includes(code)
                    ? 'border-primary/50 bg-primary/10 text-primary'
                    : 'border-border text-muted-foreground hover:text-foreground',
                )}
              >
                {label}
              </button>
            ))}
          </div>
          <Button
            className="mt-3 w-full font-mono-hud text-[11px] uppercase tracking-wider"
            disabled={!owned || store.pending || langs.length === 0}
            onClick={async () => { if (await store.translateSkill(id, langs)) setLangs([]); }}
          >
            Translate to {langs.length} language(s)
          </Button>
        </Panel>
      </div>
    </div>
  );
}

// ── Analysis ────────────────────────────────────────────────────────────────

function AnalysisTab({ id, detail }: { id: string; detail: SkillDetail }) {
  const store = useStore();
  const run = (tools: string[]) =>
    store.analyze({
      target: { kind: 'skill', value: id },
      tools,
      depth: 'basic',
      min_confidence: 0.7,
      ai_mode: 'off',
      attach_to: id,
    });
  // list_for_skill returns newest first, so the first row per tool is current.
  const rowFor = (tool: string) => detail.analysis.find((a) => a.tool === tool) ?? null;
  const quality = rowFor('quality');

  return (
    <div className="space-y-4">
      <Panel corners={false} className="flex flex-wrap items-center gap-3 p-4">
        <div className="min-w-0 flex-1">
          <CardTitle>Codebase analysis (C3.x)</CardTitle>
          <p className="text-xs text-muted-foreground">
            Runs against this skill's directory and attaches the results here. Each run updates this tool's result and leaves the others
            alone; “Run all” refreshes every card.
          </p>
        </div>
        <Button
          disabled={store.pending}
          onClick={() => run(ANALYSIS_TOOLS.map((t) => t.tool))}
          className="font-mono-hud text-[11px] uppercase tracking-wider"
        >
          Run all
        </Button>
      </Panel>

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
        {ANALYSIS_TOOLS.map((meta) => {
          const row = rowFor(meta.tool);
          return (
            <Panel key={meta.tool} corners={false} className="flex flex-col p-4">
              <div className="flex items-start justify-between gap-2">
                <h4 className="text-[13px] font-semibold">{meta.label}</h4>
                <span className="font-mono-hud text-[10px] uppercase tracking-wider text-muted-foreground">{meta.tag}</span>
              </div>
              <div className="mt-2 font-mono-hud text-xl text-primary">{row?.count ?? '—'}</div>
              <p className="mt-1 min-h-8 text-xs text-muted-foreground">
                {row ? `${row.ranAt}` : meta.hint}
              </p>
              {row?.path && <p className="break-all font-mono-hud text-[10px] text-muted-foreground">{row.path}</p>}
              <div className="mt-3 flex gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  disabled={store.pending}
                  onClick={() => run([meta.tool])}
                  className="h-7 font-mono-hud text-[10px] uppercase tracking-wider"
                >
                  {row ? 'Re-run' : 'Run'}
                </Button>
                {row?.path && (
                  <Button size="sm" variant="ghost" className="h-7 font-mono-hud text-[10px] uppercase tracking-wider" onClick={() => copyText(row.path)}>
                    Copy path
                  </Button>
                )}
              </div>
            </Panel>
          );
        })}

        <Panel corners={false} className="flex flex-col p-4">
          <div className="flex items-start justify-between gap-2">
            <h4 className="text-[13px] font-semibold">Quality check</h4>
            <span className="font-mono-hud text-[10px] uppercase tracking-wider text-muted-foreground">quality</span>
          </div>
          <div className="mt-2"><QualityMeter q={detail.quality} /></div>
          <p className="mt-1 min-h-8 text-xs text-muted-foreground">
            {quality ? `${quality.count ?? '—'} findings · ${quality.ranAt}` : 'writes a full report under output/_reports'}
          </p>
          <div className="mt-3 flex gap-2">
            <Button
              size="sm"
              variant="outline"
              disabled={store.pending}
              onClick={() => store.qualitySkill(id)}
              className="h-7 font-mono-hud text-[10px] uppercase tracking-wider"
            >
              {quality ? 'Re-check' : 'Run'}
            </Button>
          </div>
        </Panel>
      </div>
    </div>
  );
}

// ── Export ──────────────────────────────────────────────────────────────────

function ExportTab({ id, onNavigate }: { id: string; onNavigate: (to: string) => void }) {
  const store = useStore();
  const [targets, setTargets] = useState<string[]>(['claude']);
  const [db, setDb] = useState('chroma');
  const [conn, setConn] = useState<Record<string, string>>({});
  const [embedding, setEmbedding] = useState('none');
  const available = store.settings?.capabilities.targets ?? [];
  const keys = store.settings?.keys ?? [];
  const active = VECTOR_DBS.find((d) => d.id === db) ?? VECTOR_DBS[0];
  const connValue = conn[active.id] ?? '';
  // The backend rejects a target it does not support, and the seeded default
  // ('claude') is only a guess until /api/settings reports the real list.
  const chosen = targets.filter((t) => available.includes(t));

  const toggleTarget = (target: string) =>
    setTargets((t) => (t.includes(target) ? t.filter((x) => x !== target) : [...t, target]));

  const exportToDb = () => {
    const options: Record<string, string> = { [active.key]: connValue.trim() };
    if (embedding !== 'none') options.embedding_function = embedding;
    return store.uploadSkill(id, active.id, options);
  };

  return (
    <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
      <Panel corners={false} className="p-4">
        <CardTitle>Package</CardTitle>
        <p className="mb-3 text-xs text-muted-foreground">Archives land in output/_packages and are listed on the job.</p>
        {available.length === 0 && <p className="text-xs text-muted-foreground">No package targets reported by the backend.</p>}
        <div className="grid gap-2 sm:grid-cols-2">
          {available.map((target) => {
            const meta = EXPORT_TARGETS.find((t) => t.id === target);
            return (
              <label
                key={target}
                className={cn(
                  'flex cursor-pointer items-center gap-2.5 rounded border px-3 py-2.5 transition-colors',
                  targets.includes(target) ? 'border-primary/60 bg-primary/10' : 'border-border bg-secondary/30',
                )}
              >
                <Checkbox aria-label={target} checked={targets.includes(target)} onCheckedChange={() => toggleTarget(target)} />
                <span className="min-w-0">
                  <span className="block text-[12px] font-medium">{meta?.label ?? target}</span>
                  <span className="block font-mono-hud text-[10px] text-muted-foreground">{target}</span>
                </span>
              </label>
            );
          })}
        </div>
        <Button
          className="mt-3 w-full font-mono-hud text-[11px] uppercase tracking-wider"
          disabled={store.pending || chosen.length === 0}
          onClick={() => store.packageSkill(id, chosen)}
        >
          Package {chosen.length} format(s) → _packages/
        </Button>
      </Panel>

      <Panel corners={false} className="p-4">
        <CardTitle>Upload</CardTitle>
        <p className="mb-3 text-xs text-muted-foreground">Packages the skill for the platform, then uploads the archive with your stored key.</p>
        <div className="space-y-2">
          {UPLOAD_CARDS.map((card) => {
            const set = keys.find((k) => k.name === card.env)?.set ?? false;
            return (
              <div key={card.target} className="flex flex-wrap items-center gap-3 rounded border border-border bg-secondary/30 px-3 py-2.5">
                <span className="min-w-0 flex-1">
                  <span className="block text-[13px] font-medium">{card.label}</span>
                  <span className={cn('block font-mono-hud text-[10px]', set ? 'text-[hsl(152_60%_50%)]' : 'text-muted-foreground')}>
                    {card.env} {set ? 'set' : 'missing'}
                  </span>
                </span>
                {set ? (
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={store.pending}
                    onClick={() => store.uploadSkill(id, card.target, {})}
                    className="h-7 font-mono-hud text-[10px] uppercase tracking-wider"
                  >
                    Upload {card.fmt}
                  </Button>
                ) : (
                  <Button size="sm" variant="ghost" onClick={() => onNavigate('/settings')} className="h-7 font-mono-hud text-[10px] uppercase tracking-wider">
                    Add key in Settings →
                  </Button>
                )}
              </div>
            );
          })}
        </div>
      </Panel>

      <Panel corners={false} className="p-4 lg:col-span-2">
        <CardTitle>Vector DB export</CardTitle>
        <p className="mb-3 text-xs text-muted-foreground">Chunks the skill and writes it into a vector store. One connection setting per database.</p>
        <RadioGroup value={db} onValueChange={setDb} className="grid grid-cols-2 gap-2 sm:grid-cols-4">
          {VECTOR_DBS.map((entry) => (
            <label
              key={entry.id}
              className={cn(
                'flex items-center gap-2.5 rounded border px-3 py-2.5 transition-colors',
                entry.upload ? 'cursor-pointer' : 'cursor-not-allowed opacity-50',
                db === entry.id ? 'border-primary/60 bg-primary/10' : 'border-border bg-secondary/30',
              )}
            >
              <RadioGroupItem value={entry.id} aria-label={entry.label} disabled={!entry.upload} />
              <span className="font-mono-hud text-[12px]">{entry.label}</span>
            </label>
          ))}
        </RadioGroup>
        {VECTOR_DBS.some((entry) => !entry.upload) && (
          <p className="mt-2 text-xs text-muted-foreground">
            {VECTOR_DBS.filter((entry) => !entry.upload).map((entry) => entry.label).join(' and ')}: not supported by
            upload yet — package to this format instead.
          </p>
        )}
        <div className="mt-3 grid gap-3 sm:grid-cols-2">
          <div className="space-y-1">
            <div className="font-mono-hud text-[10px] uppercase tracking-[0.2em] text-muted-foreground">{active.field}</div>
            <Input
              aria-label={active.field}
              value={connValue}
              placeholder={active.placeholder}
              onChange={(e) => setConn((c) => ({ ...c, [active.id]: e.target.value }))}
              className="h-8 font-mono-hud text-xs"
            />
          </div>
          <div className="space-y-1">
            <div className="font-mono-hud text-[10px] uppercase tracking-[0.2em] text-muted-foreground">embedding function</div>
            <select
              aria-label="embedding function"
              value={embedding}
              onChange={(e) => setEmbedding(e.target.value)}
              className="h-8 w-full rounded border border-border bg-secondary/40 px-2 font-mono-hud text-xs outline-none focus:border-primary/50"
            >
              {EMBEDDING_FUNCTIONS.map((fn) => (
                <option key={fn} value={fn}>{fn === 'none' ? 'none (platform default)' : fn}</option>
              ))}
            </select>
          </div>
        </div>
        <Button
          variant="outline"
          className="mt-3 w-full font-mono-hud text-[11px] uppercase tracking-wider"
          disabled={store.pending || !active.upload || !connValue.trim()}
          onClick={exportToDb}
        >
          Export to {active.label}
        </Button>
      </Panel>
    </div>
  );
}

// ── History ─────────────────────────────────────────────────────────────────

function HistoryTab({ history }: { history: Job[] }) {
  const store = useStore();
  if (!history.length) {
    return (
      <Panel corners={false} className="p-6">
        <p className="text-sm text-muted-foreground">No jobs have touched this skill yet.</p>
      </Panel>
    );
  }
  return (
    <Panel corners={false} className="overflow-hidden">
      <div className="overflow-x-auto" role="region" aria-label="Skill job history" tabIndex={0}>
        <table className="w-full min-w-[760px] text-sm">
          <thead>
            <tr className="border-b border-border font-mono-hud text-[10px] uppercase tracking-[0.15em] text-muted-foreground">
              <th className="px-3 py-2.5 text-left font-medium">when</th>
              <th className="px-3 py-2.5 text-left font-medium">job</th>
              <th className="px-3 py-2.5 text-left font-medium">detail</th>
              <th className="px-3 py-2.5 text-left font-medium">status</th>
              <th className="px-3 py-2.5 text-left font-medium">outputs</th>
              <th className="w-20 px-3 py-2.5" />
            </tr>
          </thead>
          <tbody>
            {history.map((job) => (
              <tr key={job.id} className="border-b border-border/60 align-top">
                <td className="px-3 py-2.5 font-mono-hud text-[11px] text-muted-foreground">{job.startedAt}</td>
                <td className="px-3 py-2.5 font-mono-hud text-[11px] uppercase tracking-wider text-primary">{job.type}</td>
                <td className="px-3 py-2.5">
                  <span className="block break-words text-[13px]">{job.detail}</span>
                  {job.error && <span role="alert" className="block break-words text-[11px] text-destructive">{job.error}</span>}
                  {/* same affordance as sections/Jobs.tsx: the worker log is the
                      only place a failure explains itself */}
                  <details open={job.status === 'failed'} className="mt-1">
                    <summary className="cursor-pointer font-mono-hud text-[11px] text-muted-foreground">
                      Log ({(job.log ?? []).length} lines)
                    </summary>
                    <pre className="mt-1 max-h-64 overflow-auto whitespace-pre-wrap break-words rounded border border-border bg-black/30 p-2 text-[11px]">
                      {(job.log ?? []).join('\n')}
                    </pre>
                  </details>
                </td>
                <td className="px-3 py-2.5"><StatusPill status={job.status} /></td>
                <td className="px-3 py-2.5">
                  {(job.artifacts ?? []).length === 0 && <span className="font-mono-hud text-[11px] text-muted-foreground">—</span>}
                  {(job.artifacts ?? []).map((artifact, i) => (
                    <span key={artifact} className="flex flex-wrap items-center gap-2">
                      <span className="break-all font-mono-hud text-[11px]">{artifact}</span>
                      {job.downloadableArtifacts?.includes(i) && (
                        <a className="font-mono-hud text-[11px] text-primary underline" href={`/api/jobs/${job.id}/artifacts/${i}`} download>Download</a>
                      )}
                    </span>
                  ))}
                </td>
                <td className="px-3 py-2.5 text-right">
                  {/* Retrying a job that is still active is a 409 on the way in
                      — an active row gets the cancel affordance instead. */}
                  {['running', 'queued', 'cancelling'].includes(job.status) ? (
                    <Button
                      size="sm"
                      variant="outline"
                      disabled={store.pending || job.status === 'cancelling'}
                      onClick={() => store.cancelJob(job.id)}
                      className="h-7 font-mono-hud text-[10px] uppercase tracking-wider"
                    >
                      Cancel
                    </Button>
                  ) : (
                    <Button
                      size="sm"
                      variant="outline"
                      disabled={store.pending}
                      onClick={() => store.retryJob(job.id)}
                      className="h-7 font-mono-hud text-[10px] uppercase tracking-wider"
                    >
                      Retry
                    </Button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Panel>
  );
}
