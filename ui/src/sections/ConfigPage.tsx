import { useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import { useNavigate } from 'react-router';
import { toast } from 'sonner';
import { Panel } from '@/components/hud';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import { Switch } from '@/components/ui/switch';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { GenerateConfigForm } from '@/components/generate-config-form';
import { usePayload } from '@/hooks/use-payload';
import { api } from '@/lib/api';
import type { ConfigDetail, Validation } from '@/lib/api';
import { useStore } from '@/lib/store';
import { cn } from '@/lib/utils';
import {
  CheckCircle2, Copy, FileJson, Gauge, GitBranch, Pencil, RefreshCw, Rocket, Scissors, UploadCloud, Wand2,
} from 'lucide-react';

// ── static tables ───────────────────────────────────────────────────────────

const TABS: [string, string][] = [
  ['overview', 'Overview'],
  ['json', 'JSON'],
  ['validate', 'Validate'],
  ['estimate', 'Estimate'],
  ['sync', 'Sync'],
  ['push', 'Push / Submit'],
  ['generate', 'Generate'],
];

// The split job's argparse choices (routes/configs.py:SPLIT_STRATEGIES).
const SPLIT_STRATEGIES = ['auto', 'none', 'source', 'category', 'router', 'size'] as const;
// PUT .../sync's argparse-equivalent choices (routes/configs.py:SYNC_INTERVALS).
const SYNC_INTERVALS = ['hourly', 'daily', 'weekly', 'manual'] as const;

// registry.list_config_entries origins — same palette as sections/Library.tsx
// (not exported from there, so this is the one deliberate duplicate).
const ORIGIN_STYLE: Record<string, string> = {
  preset: '187 92% 50%',
  scanned: '258 90% 66%',
  custom: '45 93% 55%',
  synced: '152 60% 45%',
};

// A config's `sync` state and `lastEstimate` are both free-form job output
// (see routes/configs.py) — read known keys defensively rather than assuming
// a schema.
const readString = (o: Record<string, unknown> | null | undefined, key: string): string =>
  o && typeof o[key] === 'string' ? (o[key] as string) : '';
const readNumber = (o: Record<string, unknown> | null | undefined, key: string): number | null =>
  o && typeof o[key] === 'number' ? (o[key] as number) : null;
const readBool = (o: Record<string, unknown> | null | undefined, key: string): boolean | null =>
  o && typeof o[key] === 'boolean' ? (o[key] as boolean) : null;

function configSources(data: Record<string, unknown>): Record<string, unknown>[] {
  const raw = data['sources'];
  return Array.isArray(raw) ? raw.filter((s): s is Record<string, unknown> => typeof s === 'object' && s !== null) : [];
}

// ── small shared presentation bits (mirrors SkillPage's private helpers) ────

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

function Tag({ children, color }: { children: ReactNode; color: string }) {
  return (
    <span
      className="inline-flex items-center rounded-[4px] border px-1.5 py-0.5 font-mono-hud text-[10px] uppercase tracking-wider whitespace-nowrap"
      style={{ color: `hsl(${color})`, borderColor: `hsl(${color} / 0.4)`, background: `hsl(${color} / 0.08)` }}
    >
      {children}
    </span>
  );
}

const copyText = (value: string) =>
  navigator.clipboard.writeText(value)
    .then(() => toast.success('Copied'))
    .catch(() => toast.error('Copy unavailable', { description: value }));

// ── page ────────────────────────────────────────────────────────────────────

export default function ConfigPage({ id }: { id: string }) {
  const store = useStore();
  const navigate = useNavigate();
  const { data, error, reload } = usePayload<ConfigDetail>(() => api.configDetail(id), id);
  const [tab, setTab] = useState('overview');
  const [splitOpen, setSplitOpen] = useState(false);
  const [splitStrategy, setSplitStrategy] = useState<(typeof SPLIT_STRATEGIES)[number]>('auto');
  const [splitTarget, setSplitTarget] = useState(5000);

  // JSON editor state lives here, not in JsonTab, so a tab change (or the
  // header's Validate/Estimate shortcuts, which also change tabs) can guard
  // against silently discarding a draft — mirrors SkillPage.tsx's
  // editing/draft/dirty/beforeunload pattern (SkillPage.tsx:172-231).
  const [editingJson, setEditingJson] = useState(false);
  const [jsonDraft, setJsonDraft] = useState('');
  const [jsonError, setJsonError] = useState('');
  // The revision sent on save is pinned at the moment editing starts, not
  // re-read from `data.revision` at save time — `data` can be refreshed from
  // under an open editor (job polling, a manual reload), which would silently
  // swap in a fresher revision and defeat the 409 conflict check.
  const [pinnedRevision, setPinnedRevision] = useState('');

  const dirty = editingJson && data !== null && jsonDraft !== JSON.stringify(data.data, null, 2);
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

  // Estimate/sync-check/push/submit/generate all run as background jobs whose
  // results only land once the job finishes and rewrites the config's
  // sidecar files, so re-read the detail whenever a job's signature changes
  // (mirrors SkillPage's jobsKey effect). Skipped while no job has ever run
  // for this workspace (so a quiet page does not double-fetch on mount) and
  // while the JSON editor is open (a background reload would replace `data`
  // out from under an in-progress edit).
  const jobsKey = store.jobs.map((j) => `${j.id}:${j.status}:${j.progress}`).join(',');
  useEffect(() => {
    if (jobsKey && !editingJson) reload();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [jobsKey]);

  if (error) {
    return (
      <p role="alert" className="rounded border border-destructive p-3">
        {error} <button className="underline" onClick={() => reload()}>Retry</button>
      </p>
    );
  }
  if (!data) return <p role="status">Loading config…</p>;

  const sourceTypes = Array.from(new Set(configSources(data.data).map((s) => readString(s, 'type')).filter(Boolean)));
  const estimatedTotal = readNumber(data.lastEstimate, 'estimated_total');
  const syncStatus = readString(data.sync, 'status');
  const description = typeof data.data.description === 'string' ? data.data.description : '';

  const startEditJson = () => {
    setJsonDraft(JSON.stringify(data.data, null, 2));
    setPinnedRevision(data.revision);
    setJsonError('');
    setEditingJson(true);
  };

  // Also used as the JSON tab's "Cancel" button — discarding an edit in
  // progress goes through the same confirm-if-dirty gate as navigating away.
  const leaveJsonEditor = () => {
    if (dirty && !window.confirm('Discard unsaved config edits?')) return false;
    setJsonDraft(JSON.stringify(data.data, null, 2));
    setJsonError('');
    setEditingJson(false);
    return true;
  };

  const changeTab = (next: string) => {
    if (dirty && !leaveJsonEditor()) return;
    setTab(next);
  };

  const saveJson = async () => {
    let parsed: unknown;
    try {
      parsed = JSON.parse(jsonDraft);
    } catch (e) {
      setJsonError(`Invalid JSON: ${e instanceof Error ? e.message : String(e)}`);
      return;
    }
    setJsonError('');
    if (await store.saveConfig(id, parsed, pinnedRevision)) {
      setEditingJson(false);
      reload();
    }
  };

  return (
    <div className="space-y-4 animate-flicker">
      <nav aria-label="Breadcrumb" className="flex items-center gap-2 font-mono-hud text-[11px] uppercase tracking-[0.15em]">
        <button onClick={() => { if (store.confirmLeave()) navigate('/configs'); }} className="text-primary hover:underline">‹ Configs</button>
        <span className="text-muted-foreground">/ {data.name}</span>
      </nav>

      <Panel className="p-5">
        {/* ── header ── */}
        <div className="flex flex-wrap items-start gap-4">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-md border border-primary/40 bg-primary/[0.08] font-mono-hud text-lg text-primary/80">
            <FileJson className="h-5 w-5" />
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-xl font-semibold tracking-tight">{data.name}</h1>
              <Tag color="217 12% 55%">{data.source}</Tag>
              <Tag color={ORIGIN_STYLE[data.origin] ?? '217 12% 55%'}>{data.origin}</Tag>
              <span className="font-mono-hud text-[10px] text-muted-foreground">
                {data.framework} · v{data.version} · fetched from {data.source}
              </span>
            </div>
            {description && <p className="mt-1.5 max-w-[720px] text-[13px] text-muted-foreground">{description}</p>}
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Button size="sm" disabled={store.pending} onClick={() => store.buildConfig(data.path, data.name)} className="font-mono-hud text-[11px] uppercase tracking-wider">
              <Wand2 className="mr-1.5 h-3.5 w-3.5" /> Build skill
            </Button>
            <Button size="sm" variant="outline" onClick={() => changeTab('validate')} className="font-mono-hud text-[11px] uppercase tracking-wider">
              <CheckCircle2 className="mr-1.5 h-3.5 w-3.5" /> Validate
            </Button>
            <Button size="sm" variant="outline" onClick={() => changeTab('estimate')} className="font-mono-hud text-[11px] uppercase tracking-wider">
              <Gauge className="mr-1.5 h-3.5 w-3.5" /> Estimate
            </Button>
            <Button size="sm" variant="outline" onClick={() => setSplitOpen(true)} className="font-mono-hud text-[11px] uppercase tracking-wider">
              <Scissors className="mr-1.5 h-3.5 w-3.5" /> Split
            </Button>
          </div>
        </div>

        {/* ── stats strip ── */}
        <div className="mt-4 grid grid-cols-2 gap-px overflow-hidden rounded border border-border bg-border sm:grid-cols-3 lg:grid-cols-5">
          <div className="bg-card">
            <Stat label="validation">
              {data.validation.valid
                ? <span className="text-[hsl(152_60%_50%)]">✓ valid</span>
                : <span className="text-destructive">✗ {data.validation.errors.length} error(s)</span>}
            </Stat>
          </div>
          <div className="bg-card">
            <Stat label="source types">{sourceTypes.length ? sourceTypes.join(' · ') : '—'}</Stat>
          </div>
          <div className="bg-card">
            <Stat label="last estimate">{estimatedTotal !== null ? `~${estimatedTotal} pages` : 'not run'}</Stat>
          </div>
          <div className="bg-card">
            <Stat label="sync">
              {data.syncSettings?.enabled
                ? <span className="text-[hsl(152_60%_50%)]">watching · {data.syncSettings.interval}</span>
                : <span className="text-muted-foreground">off</span>}
            </Stat>
          </div>
          <div className="bg-card">
            <Stat label="upstream">{syncStatus || (data.sync ? 'checked' : 'never checked')}</Stat>
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
            <OverviewTab config={data} onNavigate={navigate} />
          </TabsContent>

          <TabsContent value="json" className="py-4">
            <JsonTab
              config={data}
              editing={editingJson}
              draft={jsonDraft}
              jsonError={jsonError}
              onDraft={setJsonDraft}
              onEdit={startEditJson}
              onCancel={leaveJsonEditor}
              onSave={saveJson}
            />
          </TabsContent>

          <TabsContent value="validate" className="py-4">
            <ValidateTab id={id} validation={data.validation} onValidated={reload} />
          </TabsContent>

          <TabsContent value="estimate" className="py-4">
            <EstimateTab id={id} lastEstimate={data.lastEstimate} />
          </TabsContent>

          <TabsContent value="sync" className="py-4">
            <SyncTab id={id} syncSettings={data.syncSettings} sync={data.sync} onChanged={reload} />
          </TabsContent>

          <TabsContent value="push" className="py-4">
            <PushSubmitTab id={id} valid={data.validation.valid} />
          </TabsContent>

          <TabsContent value="generate" className="py-4">
            <GenerateTab />
          </TabsContent>
        </Tabs>
      </Panel>

      {/* ── split ── */}
      <Dialog open={splitOpen} onOpenChange={(open) => { if (!open && !store.pending) setSplitOpen(false); }}>
        <DialogContent className="!fixed hud-panel border-border sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="font-mono-hud text-sm uppercase tracking-[0.2em] text-primary">// split {data.name}</DialogTitle>
            <DialogDescription className="text-xs text-muted-foreground">
              Splits this config into several smaller configs by strategy, written into the configs library.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3 py-2">
            <div className="space-y-1">
              <div className="font-mono-hud text-[10px] uppercase tracking-[0.2em] text-muted-foreground">strategy</div>
              <select
                aria-label="Split strategy"
                value={splitStrategy}
                onChange={(e) => setSplitStrategy(e.target.value as (typeof SPLIT_STRATEGIES)[number])}
                className="h-8 w-full rounded border border-border bg-secondary/40 px-2 font-mono-hud text-xs outline-none focus:border-primary/50"
              >
                {SPLIT_STRATEGIES.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
            <div className="space-y-1">
              <div className="font-mono-hud text-[10px] uppercase tracking-[0.2em] text-muted-foreground">target pages per split</div>
              <Input
                aria-label="Target pages"
                type="number"
                min={100}
                max={100000}
                value={splitTarget}
                onChange={(e) => setSplitTarget(Number(e.target.value))}
                className="h-8 font-mono-hud text-xs"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setSplitOpen(false)} className="font-mono-hud text-xs">Cancel</Button>
            <Button
              disabled={store.pending}
              onClick={async () => {
                if (await store.splitConfig(id, { strategy: splitStrategy, target_pages: splitTarget })) setSplitOpen(false);
              }}
              className="font-mono-hud text-xs uppercase tracking-wider"
            >
              Split
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

// ── Overview ────────────────────────────────────────────────────────────────

function OverviewTab({ config, onNavigate }: { config: ConfigDetail; onNavigate: (to: string) => void }) {
  const sources = configSources(config.data);
  return (
    <div className="grid gap-4 lg:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
      <Panel corners={false} className="overflow-hidden">
        <div className="p-4 pb-0"><CardTitle>Sources</CardTitle></div>
        {sources.length === 0 ? (
          <p className="px-4 pb-4 text-xs text-muted-foreground">This config carries no sources yet — add one from the JSON tab.</p>
        ) : (
          <div className="overflow-x-auto" role="region" aria-label="Config sources" tabIndex={0}>
            <table className="w-full min-w-[520px] text-sm">
              <thead>
                <tr className="border-b border-border font-mono-hud text-[10px] uppercase tracking-[0.15em] text-muted-foreground">
                  <th className="px-3 py-2.5 text-left font-medium">type</th>
                  <th className="px-3 py-2.5 text-left font-medium">target</th>
                  <th className="px-3 py-2.5 text-left font-medium">limits</th>
                </tr>
              </thead>
              <tbody>
                {sources.map((s, i) => {
                  const target = readString(s, 'base_url') || readString(s, 'repo') || readString(s, 'path') || '—';
                  const maxPages = readNumber(s, 'max_pages');
                  const rateLimit = readNumber(s, 'rate_limit');
                  const limits = [maxPages !== null ? `${maxPages} pages` : null, rateLimit !== null ? `${rateLimit}s/req` : null]
                    .filter(Boolean).join(' · ') || '—';
                  return (
                    <tr key={i} className="border-b border-border/60">
                      <td className="px-3 py-2.5 font-mono-hud text-[11px] uppercase tracking-wider text-primary">{readString(s, 'type') || '—'}</td>
                      <td className="break-all px-3 py-2.5 font-mono-hud text-[12px]">{target}</td>
                      <td className="px-3 py-2.5 font-mono-hud text-[11px] text-muted-foreground">{limits}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Panel>

      <Panel corners={false} className="p-4">
        <CardTitle>Used by</CardTitle>
        {config.usedBy.length === 0 && <p className="text-xs text-muted-foreground">No skill in this workspace was built from this config yet.</p>}
        <div className="space-y-1.5">
          {config.usedBy.map((u) => (
            <button key={u.id} onClick={() => onNavigate(`/skills/${encodeURIComponent(u.id)}`)} className="block font-mono-hud text-[13px] text-primary hover:underline">
              {u.name}
            </button>
          ))}
        </div>
      </Panel>

      <Panel corners={false} className="p-4 lg:col-span-2">
        <CardTitle>Lifecycle</CardTitle>
        <ul className="space-y-2 text-[13px]">
          <li>
            <span className="text-muted-foreground">last estimate: </span>
            {config.lastEstimate
              ? `${readNumber(config.lastEstimate, 'estimated_total') ?? '—'} pages projected from ${readNumber(config.lastEstimate, 'discovered') ?? '—'} discovered in ${readNumber(config.lastEstimate, 'elapsed_seconds') ?? '—'}s`
              : <span className="text-muted-foreground">no estimate run yet</span>}
          </li>
          <li>
            <span className="text-muted-foreground">sync: </span>
            {config.syncSettings?.enabled
              ? `watching · ${config.syncSettings.interval}${config.syncSettings.auto_rebuild ? ' · auto-rebuild on' : ''}`
              : <span className="text-muted-foreground">not watching upstream</span>}
          </li>
          <li>
            <span className="text-muted-foreground">last check: </span>
            {config.sync
              ? `${readString(config.sync, 'checkedAt') || readString(config.sync, 'last_check') || '—'} · ${readString(config.sync, 'status') || 'unknown'}`
              : <span className="text-muted-foreground">never checked</span>}
          </li>
        </ul>
      </Panel>
    </div>
  );
}

// ── JSON ────────────────────────────────────────────────────────────────────

function JsonTab({ config, editing, draft, jsonError, onDraft, onEdit, onCancel, onSave }: {
  config: ConfigDetail;
  editing: boolean;
  draft: string;
  jsonError: string;
  onDraft: (value: string) => void;
  onEdit: () => void;
  onCancel: () => void;
  onSave: () => void;
}) {
  const { pending } = useStore();

  return (
    <Panel corners={false} className="p-4">
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <CardTitle>Config JSON</CardTitle>
        <span className="font-mono-hud text-[10px] text-muted-foreground">revision {config.revision.slice(0, 8)}…</span>
        <div className="ml-auto flex items-center gap-2">
          <Button size="sm" variant="outline" onClick={() => copyText(JSON.stringify(config.data, null, 2))} className="font-mono-hud text-[11px] uppercase tracking-wider">
            <Copy className="mr-1.5 h-3.5 w-3.5" /> Copy
          </Button>
          {!editing && (
            <Button size="sm" disabled={pending} onClick={onEdit} className="font-mono-hud text-[11px] uppercase tracking-wider">
              <Pencil className="mr-1.5 h-3.5 w-3.5" /> Edit
            </Button>
          )}
          {editing && (
            <>
              <Button size="sm" variant="outline" disabled={pending} onClick={onCancel} className="font-mono-hud text-[11px] uppercase tracking-wider">Cancel</Button>
              <Button size="sm" disabled={pending} onClick={onSave} className="font-mono-hud text-[11px] uppercase tracking-wider">Save</Button>
            </>
          )}
        </div>
      </div>

      {jsonError && <p role="alert" className="mb-3 text-sm text-destructive">{jsonError}</p>}
      {editing ? (
        <textarea
          aria-label="Config JSON"
          value={draft}
          onChange={(e) => onDraft(e.target.value)}
          spellCheck={false}
          className="min-h-96 w-full rounded border border-border bg-background p-3 font-mono-hud text-sm outline-none focus:border-primary/50"
        />
      ) : (
        <pre className="max-h-[32rem] overflow-auto whitespace-pre-wrap break-words rounded border border-border bg-black/30 p-4 font-mono-hud text-sm">
          {JSON.stringify(config.data, null, 2)}
        </pre>
      )}
      <p className="mt-3 text-xs text-muted-foreground">
        Saves are revision-checked: if the file changed on disk since it was opened, the save is rejected and you reload before retrying.
      </p>
    </Panel>
  );
}

// ── Validate ─────────────────────────────────────────────────────────────────

function ValidateTab({ id, validation, onValidated }: { id: string; validation: Validation; onValidated: () => void }) {
  const store = useStore();
  return (
    <Panel corners={false} className="p-4">
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <CardTitle>Validation</CardTitle>
        <div className="ml-auto">
          <Button
            size="sm"
            disabled={store.pending}
            onClick={async () => { if (await store.validateConfig(id)) onValidated(); }}
            className="font-mono-hud text-[11px] uppercase tracking-wider"
          >
            <RefreshCw className="mr-1.5 h-3.5 w-3.5" /> Re-validate
          </Button>
        </div>
      </div>

      {validation.valid
        ? <p className="flex items-center gap-2 text-sm text-[hsl(152_60%_50%)]"><span aria-hidden="true">✓</span> valid — no schema errors found</p>
        : <p role="alert" className="mb-2 flex items-center gap-2 text-sm text-destructive"><span aria-hidden="true">✗</span> this config fails validation</p>}

      {(validation.errors.length > 0 || validation.warnings.length > 0) && (
        <ul className="mt-2 space-y-1.5">
          {validation.errors.map((e, i) => (
            <li key={`e-${i}`} className="flex items-start gap-2 text-sm text-destructive">
              <span aria-hidden="true">✗</span><span className="break-words">{e}</span>
            </li>
          ))}
          {validation.warnings.map((w, i) => (
            <li key={`w-${i}`} className="flex items-start gap-2 text-sm text-[hsl(45_93%_55%)]">
              <span aria-hidden="true">!</span><span className="break-words">{w}</span>
            </li>
          ))}
        </ul>
      )}
      {validation.valid && validation.warnings.length === 0 && (
        <p className="mt-2 text-xs text-muted-foreground">Warnings are always empty today — the validator raises on the first error it finds.</p>
      )}
    </Panel>
  );
}

// ── Estimate ─────────────────────────────────────────────────────────────────

function EstimateTab({ id, lastEstimate }: { id: string; lastEstimate: Record<string, unknown> | null }) {
  const store = useStore();
  const [maxDiscovery, setMaxDiscovery] = useState(200);
  const [timeoutSecs, setTimeoutSecs] = useState(10);

  const discovered = readNumber(lastEstimate, 'discovered');
  const estimatedTotal = readNumber(lastEstimate, 'estimated_total');
  const elapsed = readNumber(lastEstimate, 'elapsed_seconds');
  const hitLimit = readBool(lastEstimate, 'hit_limit');

  return (
    <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
      <Panel corners={false} className="p-4">
        <CardTitle>Run a page-count estimate</CardTitle>
        <p className="mb-3 text-xs text-muted-foreground">
          Crawls a bounded sample of the documentation source(s) to project the full page count before committing to a full scrape.
        </p>
        <div className="grid gap-3 sm:grid-cols-2">
          <div className="space-y-1">
            <div className="font-mono-hud text-[10px] uppercase tracking-[0.2em] text-muted-foreground">max discovery</div>
            <Input
              aria-label="Max discovery"
              type="number"
              min={1}
              max={5000}
              value={maxDiscovery}
              onChange={(e) => setMaxDiscovery(Number(e.target.value))}
              className="h-8 font-mono-hud text-xs"
            />
          </div>
          <div className="space-y-1">
            <div className="font-mono-hud text-[10px] uppercase tracking-[0.2em] text-muted-foreground">timeout (s)</div>
            <Input
              aria-label="Timeout seconds"
              type="number"
              min={1}
              max={300}
              value={timeoutSecs}
              onChange={(e) => setTimeoutSecs(Number(e.target.value))}
              className="h-8 font-mono-hud text-xs"
            />
          </div>
        </div>
        <Button
          className="mt-3 w-full font-mono-hud text-[11px] uppercase tracking-wider"
          disabled={store.pending}
          onClick={() => store.estimateConfig(id, { max_discovery: maxDiscovery, timeout: timeoutSecs })}
        >
          <Gauge className="mr-1.5 h-3.5 w-3.5" /> Run estimate
        </Button>
      </Panel>

      <Panel corners={false} className="p-4">
        <CardTitle>Last estimate</CardTitle>
        {!lastEstimate && <p className="text-xs text-muted-foreground">No estimate has been run for this config yet.</p>}
        {lastEstimate && (
          <div className="grid gap-3 sm:grid-cols-2">
            <Field label="discovered">{discovered ?? '—'}</Field>
            <Field label="projected total">{estimatedTotal ?? '—'}</Field>
            <Field label="elapsed">{elapsed !== null ? `${elapsed}s` : '—'}</Field>
            <Field label="hit discovery limit">{hitLimit === null ? '—' : hitLimit ? 'yes' : 'no'}</Field>
          </div>
        )}
      </Panel>
    </div>
  );
}

// ── Sync ─────────────────────────────────────────────────────────────────────

function SyncTab({ id, syncSettings, sync, onChanged }: {
  id: string;
  syncSettings: ConfigDetail['syncSettings'];
  sync: ConfigDetail['sync'];
  onChanged: () => void;
}) {
  const store = useStore();
  const [enabled, setEnabled] = useState(syncSettings?.enabled ?? false);
  const [intervalChoice, setIntervalChoice] = useState<(typeof SYNC_INTERVALS)[number]>(
    (syncSettings?.interval as (typeof SYNC_INTERVALS)[number]) ?? 'daily',
  );
  const [autoRebuild, setAutoRebuild] = useState(syncSettings?.auto_rebuild ?? false);

  // Reloads the page's config detail on every successful change so the stats
  // strip and Overview's Lifecycle bullet (both driven by the parent's copy
  // of `syncSettings`/`sync`) stay current, and so a later remount of this
  // tab (switching away and back) re-seeds from fresh data instead of the
  // props this tab mounted with.
  const push = async (next: Partial<{ enabled: boolean; interval: string; auto_rebuild: boolean }>) => {
    const ok = await store.setSync(id, { enabled, interval: intervalChoice, auto_rebuild: autoRebuild, ...next });
    if (ok) onChanged();
    return ok;
  };

  const toggle = async (checked: boolean) => { if (await push({ enabled: checked })) setEnabled(checked); };
  const changeInterval = async (next: (typeof SYNC_INTERVALS)[number]) => { if (await push({ interval: next })) setIntervalChoice(next); };
  const toggleAutoRebuild = async (checked: boolean) => { if (await push({ auto_rebuild: checked })) setAutoRebuild(checked); };
  const checkNow = async () => { if (await store.syncCheck(id)) onChanged(); };

  const status = readString(sync, 'status');
  const checkedAt = readString(sync, 'checkedAt') || readString(sync, 'last_check');
  const totalChanges = readNumber(sync, 'total_changes');
  const changes = Array.isArray(sync?.['changes'])
    ? (sync!['changes'] as unknown[]).filter((c): c is Record<string, unknown> => typeof c === 'object' && c !== null)
    : [];

  return (
    <div className="space-y-4">
      <Panel corners={false} className="p-4">
        <CardTitle>Watch upstream</CardTitle>
        <div className="flex flex-wrap items-center gap-3">
          <Switch aria-label="Watch upstream docs for changes" checked={enabled} disabled={store.pending} onCheckedChange={toggle} />
          {/* No scheduler runs these settings yet — the wording must not imply
              a background watcher exists. Checks happen on "Check now". */}
          <span className="text-[13px]">{enabled ? 'Watch setting saved' : 'Not watching upstream'}</span>
        </div>

        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          <div>
            <div className="mb-1.5 font-mono-hud text-[10px] uppercase tracking-[0.2em] text-muted-foreground">check interval</div>
            <div className="flex flex-wrap gap-1.5">
              {SYNC_INTERVALS.map((opt) => (
                <button
                  key={opt}
                  aria-pressed={intervalChoice === opt}
                  disabled={!enabled || store.pending}
                  onClick={() => changeInterval(opt)}
                  className={cn(
                    'rounded border px-2.5 py-1 font-mono-hud text-[11px] capitalize transition-colors disabled:opacity-40',
                    intervalChoice === opt ? 'border-primary/50 bg-primary/10 text-primary' : 'border-border text-muted-foreground hover:text-foreground',
                  )}
                >
                  {opt}
                </button>
              ))}
            </div>
            <p className="mt-1.5 text-[11px] text-muted-foreground">
              Schedule is saved for a future scheduler; checks run when you press Check now.
            </p>
          </div>
          <div className="space-y-1.5">
            <label className="flex items-center gap-2.5 font-mono-hud text-[11px] text-foreground/80 cursor-pointer select-none">
              <Checkbox checked={autoRebuild} disabled={!enabled || store.pending} onCheckedChange={(v) => toggleAutoRebuild(v === true)} />
              auto-rebuild the skill when upstream changes
            </label>
            <p className="text-[11px] text-muted-foreground">
              Saved for a future scheduler; checks run when you press Check now.
            </p>
          </div>
        </div>

        <div className="mt-4 flex flex-wrap items-center gap-3 border-t border-border pt-3">
          <Button size="sm" variant="outline" disabled={store.pending} onClick={checkNow} className="font-mono-hud text-[11px] uppercase tracking-wider">
            <RefreshCw className="mr-1.5 h-3.5 w-3.5" /> Check now
          </Button>
          <span className="font-mono-hud text-[10px] text-muted-foreground">
            {checkedAt
              ? `last checked ${checkedAt}${status ? ` · ${status}` : ''}${totalChanges !== null ? ` · ${totalChanges} change(s) lifetime` : ''}`
              : 'never checked'}
          </span>
        </div>
      </Panel>

      <Panel corners={false} className="overflow-hidden">
        <div className="p-4 pb-0"><CardTitle>Detected changes</CardTitle></div>
        {changes.length === 0 ? (
          <p className="px-4 pb-4 text-xs text-muted-foreground">No changes recorded by the last check.</p>
        ) : (
          <div className="overflow-x-auto" role="region" aria-label="Sync changes" tabIndex={0}>
            <table className="w-full min-w-[520px] text-sm">
              <thead>
                <tr className="border-b border-border font-mono-hud text-[10px] uppercase tracking-[0.15em] text-muted-foreground">
                  <th className="px-3 py-2.5 text-left font-medium">url</th>
                  <th className="px-3 py-2.5 text-left font-medium">change</th>
                  <th className="px-3 py-2.5 text-left font-medium">detected</th>
                </tr>
              </thead>
              <tbody>
                {changes.map((c, i) => (
                  <tr key={i} className="border-b border-border/60">
                    <td className="break-all px-3 py-2.5 font-mono-hud text-[12px]">{readString(c, 'url')}</td>
                    <td className="px-3 py-2.5 font-mono-hud text-[11px] uppercase text-muted-foreground">{readString(c, 'change_type')}</td>
                    <td className="px-3 py-2.5 font-mono-hud text-[11px] text-muted-foreground">{readString(c, 'detected_at')}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Panel>
    </div>
  );
}

// ── Push / Submit ─────────────────────────────────────────────────────────────

function PushSubmitTab({ id, valid }: { id: string; valid: boolean }) {
  const store = useStore();
  const pushable = store.sources.filter((s) => s.id !== 'official');
  const [source, setSource] = useState(pushable[0]?.id ?? '');
  const [note, setNote] = useState('');
  const [branch, setBranch] = useState(false);
  const [probe, setProbe] = useState(true);

  const githubTokenSet = (store.settings?.keys ?? []).find((k) => k.name === 'GITHUB_TOKEN')?.set ?? false;

  return (
    <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
      <Panel corners={false} className="p-4">
        <CardTitle>Push to a config source</CardTitle>
        <p className="mb-3 text-xs text-muted-foreground">
          Commits this file into one of your registered git config sources. The official registry is read-only here — use Submit for that.
        </p>
        {pushable.length === 0 ? (
          <p className="text-xs text-muted-foreground">No custom config sources registered yet — add one from the Configs library.</p>
        ) : (
          <>
            <div className="space-y-1">
              <div className="font-mono-hud text-[10px] uppercase tracking-[0.2em] text-muted-foreground">destination</div>
              <select
                aria-label="Push destination"
                value={source}
                onChange={(e) => setSource(e.target.value)}
                className="h-8 w-full rounded border border-border bg-secondary/40 px-2 font-mono-hud text-xs outline-none focus:border-primary/50"
              >
                {pushable.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
              </select>
            </div>
            <div className="mt-3 space-y-1">
              <div className="font-mono-hud text-[10px] uppercase tracking-[0.2em] text-muted-foreground">note (job log only)</div>
              <Input
                aria-label="Push note"
                value={note}
                onChange={(e) => setNote(e.target.value)}
                placeholder="not a commit message — recorded in the job log"
                className="h-8 font-mono-hud text-xs"
              />
            </div>
            <label className="mt-3 flex items-center gap-2.5 font-mono-hud text-[11px] text-foreground/80 cursor-pointer select-none">
              <Checkbox checked={branch} onCheckedChange={(v) => setBranch(v === true)} />
              create a branch instead of pushing directly
            </label>
            <Button
              className="mt-3 w-full font-mono-hud text-[11px] uppercase tracking-wider"
              disabled={store.pending || !source}
              onClick={() => store.pushConfig(id, { source, message: note, branch })}
            >
              <GitBranch className="mr-1.5 h-3.5 w-3.5" /> Push → {source || '…'}
            </Button>
          </>
        )}
      </Panel>

      <Panel corners={false} className="p-4">
        <CardTitle>Submit to community registry</CardTitle>
        <p className="mb-3 text-xs text-muted-foreground">Files a GitHub issue with this config for maintainers to review and add to the official registry.</p>
        <div className="space-y-2">
          <div className="flex items-center justify-between rounded border border-border bg-secondary/30 px-3 py-2">
            <span className="text-[13px]">GITHUB_TOKEN</span>
            <span className={cn('font-mono-hud text-[10px]', githubTokenSet ? 'text-[hsl(152_60%_50%)]' : 'text-destructive')}>
              {githubTokenSet ? 'set' : 'missing'}
            </span>
          </div>
          <div className="flex items-center justify-between rounded border border-border bg-secondary/30 px-3 py-2">
            <span className="text-[13px]">Validation</span>
            <span className={cn('font-mono-hud text-[10px]', valid ? 'text-[hsl(152_60%_50%)]' : 'text-destructive')}>
              {valid ? 'valid' : 'invalid'}
            </span>
          </div>
        </div>
        <label className="mt-3 flex items-center gap-2.5 font-mono-hud text-[11px] text-foreground/80 cursor-pointer select-none">
          <Checkbox checked={probe} onCheckedChange={(v) => setProbe(v === true)} />
          probe URLs before submitting
        </label>
        <Button
          className="mt-3 w-full font-mono-hud text-[11px] uppercase tracking-wider"
          disabled={store.pending || !githubTokenSet || !valid}
          onClick={() => store.submitConfig(id, probe)}
        >
          <Rocket className="mr-1.5 h-3.5 w-3.5" /> Submit to registry
        </Button>
        {!githubTokenSet && <p className="mt-2 text-xs text-muted-foreground">Add GITHUB_TOKEN in Settings to enable submission.</p>}
        {!valid && <p className="mt-2 text-xs text-muted-foreground">Fix validation errors before submitting to the registry.</p>}
      </Panel>
    </div>
  );
}

// ── Generate ──────────────────────────────────────────────────────────────────

function GenerateTab() {
  return (
    <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
      <Panel corners={false} className="p-4">
        <CardTitle>Generate a config with AI</CardTitle>
        <GenerateConfigForm />
      </Panel>

      <Panel corners={false} className="p-4">
        <CardTitle>What happens next</CardTitle>
        <ol className="list-decimal space-y-2 pl-4 text-xs text-muted-foreground">
          <li>An AI pass drafts a unified config JSON for the source.</li>
          <li>The job writes it into your configs directory, where it appears in the Configs library.</li>
          <li>Open it here to validate, estimate its page count, and build a skill from it.</li>
        </ol>
        <p className="mt-3 flex items-center gap-2 text-xs text-muted-foreground">
          <UploadCloud className="h-3.5 w-3.5 shrink-0" /> Tip: run Estimate before a full build if the source is a large documentation site.
        </p>
      </Panel>
    </div>
  );
}
