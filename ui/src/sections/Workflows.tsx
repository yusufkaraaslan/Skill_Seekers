import { useState } from 'react';
import { useNavigate } from 'react-router';
import { toast } from 'sonner';
import { Panel, SectionHeader } from '@/components/hud';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { usePayload } from '@/hooks/use-payload';
import { api } from '@/lib/api';
import type { WorkflowRow } from '@/lib/api';
import { useStore } from '@/lib/store';
import { cn } from '@/lib/utils';
import { CheckCircle2, Copy, Pencil, Trash2, UploadCloud, Wand2 } from 'lucide-react';

// safe_name-safe on the backend: letters, digits, - and _ only.
const NAME_RE = /^[A-Za-z0-9_-]+$/;

// ── small shared presentation bits (mirrors ConfigPage's private helpers) ────

function OriginTag({ origin }: { origin: WorkflowRow['origin'] }) {
  const color = origin === 'user' ? '152 60% 45%' : '217 12% 55%';
  return (
    <span
      className="inline-flex items-center rounded-[4px] border px-1.5 py-0.5 font-mono-hud text-[10px] uppercase tracking-wider whitespace-nowrap"
      style={{ color: `hsl(${color})`, borderColor: `hsl(${color} / 0.4)`, background: `hsl(${color} / 0.08)` }}
    >
      {origin}
    </span>
  );
}

function ValidationPill({ validation }: { validation: WorkflowRow['validation'] }) {
  return validation.valid
    ? <span className="font-mono-hud text-[11px] text-[hsl(152_60%_50%)]">✓ valid</span>
    : <span className="font-mono-hud text-[11px] text-destructive">✗ invalid</span>;
}

// ── page ────────────────────────────────────────────────────────────────────

export default function Workflows({ selected }: { selected: string | null }) {
  const store = useStore();
  const navigate = useNavigate();
  const { data, error, reload } = usePayload<WorkflowRow[]>(() => api.workflows(), 'workflows');

  const [installOpen, setInstallOpen] = useState(false);
  const [installName, setInstallName] = useState('');
  const [installYaml, setInstallYaml] = useState('');
  const [copyOpen, setCopyOpen] = useState(false);
  const [copySource, setCopySource] = useState('');

  if (error) return <p role="alert" className="rounded border border-destructive p-3">{error}</p>;
  if (!data) return <p role="status">Loading workflows…</p>;

  const activeRow = (selected ? data.find((w) => w.name === selected) : null) ?? data[0] ?? null;
  const bundled = data.filter((w) => w.origin === 'bundled');
  const installNameError = installName !== '' && !NAME_RE.test(installName) ? 'letters, digits, - and _ only' : '';

  const openWorkflow = (name: string) => navigate(`/workflows/${encodeURIComponent(name)}`);

  const stashForCreate = (name: string) => {
    // `/api/workflows` and `/api/settings` load in parallel — `store.root`
    // reads '' until settings arrive, and a draft stashed under
    // `seeker.create..workflows` (empty root) is never read back by
    // sections/Create.tsx (its draftKey is keyed by the real root). The
    // button is disabled until settings load (see WorkflowDetail below),
    // but guard here too rather than trust only the disabled prop.
    if (!store.root) {
      toast.error('Workspace settings not loaded yet');
      return;
    }
    // Mirrors sections/Create.tsx's draft key exactly (`seeker.create.<root>.`
    // + field name) so the Create screen picks this up as its `workflows`
    // draft on the next load.
    try { sessionStorage.setItem(`seeker.create.${store.root}.workflows`, JSON.stringify([name])); } catch { /* storage unavailable */ }
    navigate('/create');
  };

  const openInstall = () => { setInstallName(''); setInstallYaml(''); setInstallOpen(true); };
  const openCopyFromBundled = () => { setCopySource(bundled[0]?.name ?? ''); setCopyOpen(true); };

  return (
    <div className="space-y-4 animate-flicker">
      <SectionHeader
        title="Enhancement workflows"
        sub={`${data.length} preset(s) — bundled and your own${activeRow ? ` · ${activeRow.name}` : ''}`}
        right={
          <div className="flex flex-wrap items-center gap-2">
            <Button size="sm" variant="outline" onClick={openInstall} className="font-mono-hud text-[11px] uppercase tracking-wider">
              <UploadCloud className="mr-1.5 h-3.5 w-3.5" /> Install YAML file…
            </Button>
            <Button size="sm" variant="outline" disabled={bundled.length === 0} onClick={openCopyFromBundled} className="font-mono-hud text-[11px] uppercase tracking-wider">
              <Copy className="mr-1.5 h-3.5 w-3.5" /> New from bundled
            </Button>
          </div>
        }
      />

      <div className="grid gap-4 lg:grid-cols-[340px_minmax(0,1fr)]">
        {/* ── left: workflow list ── */}
        <Panel corners={false} className="overflow-hidden">
          <div className="overflow-x-auto" role="region" aria-label="Workflows table" tabIndex={0}>
            <table className="w-full min-w-[280px] text-sm">
              <thead>
                <tr className="border-b border-border font-mono-hud text-[10px] uppercase tracking-[0.15em] text-muted-foreground">
                  <th className="px-3 py-2.5 text-left font-medium">workflow</th>
                  <th className="px-3 py-2.5 text-left font-medium">steps</th>
                  <th className="px-3 py-2.5 text-left font-medium">check</th>
                </tr>
              </thead>
              <tbody>
                {data.map((w) => {
                  const isSelected = activeRow?.name === w.name;
                  return (
                    <tr
                      key={w.name}
                      role="row"
                      tabIndex={0}
                      aria-selected={isSelected}
                      onClick={() => openWorkflow(w.name)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); openWorkflow(w.name); }
                      }}
                      className={cn(
                        'cursor-pointer border-b border-border/60 transition-colors hover:bg-secondary/40 focus:outline-none focus-visible:ring-1 focus-visible:ring-primary/50 focus-visible:ring-inset',
                        isSelected && 'bg-primary/5 shadow-[inset_2px_0_0_0_hsl(187_92%_50%)]',
                      )}
                    >
                      <td className="px-3 py-2.5">
                        <div className="flex flex-wrap items-center gap-1.5">
                          <span className="font-mono-hud text-[13px] font-semibold">{w.name}</span>
                          <OriginTag origin={w.origin} />
                        </div>
                        <div className="truncate text-[11px] text-muted-foreground">{w.file}</div>
                      </td>
                      <td className="px-3 py-2.5 font-mono-hud text-xs text-muted-foreground">{w.steps}</td>
                      <td className="px-3 py-2.5"><ValidationPill validation={w.validation} /></td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Panel>

        {/* ── right: selected workflow detail ── */}
        {activeRow ? (
          <WorkflowDetail
            key={activeRow.name}
            row={activeRow}
            reload={reload}
            onUseInCreate={() => stashForCreate(activeRow.name)}
          />
        ) : (
          <Panel className="p-5">
            <p className="text-sm text-muted-foreground">No workflows available — install one from a YAML file.</p>
          </Panel>
        )}
      </div>

      {/* ── install YAML file ── */}
      <Dialog open={installOpen} onOpenChange={(open) => { if (!open && !store.pending) setInstallOpen(false); }}>
        <DialogContent className="!fixed hud-panel border-border sm:max-w-lg">
          <DialogHeader>
            <DialogTitle className="font-mono-hud text-sm uppercase tracking-[0.2em] text-primary">// install workflow</DialogTitle>
            <DialogDescription className="text-xs text-muted-foreground">
              Writes a new user workflow YAML file into your workflow directory.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3 py-2">
            <div className="space-y-1">
              <div className="font-mono-hud text-[10px] uppercase tracking-[0.2em] text-muted-foreground">name</div>
              <Input
                aria-label="Workflow name"
                value={installName}
                onChange={(e) => setInstallName(e.target.value)}
                placeholder="my-workflow"
                className="h-8 font-mono-hud text-xs"
              />
              {installNameError && <p className="text-xs text-destructive">{installNameError}</p>}
            </div>
            <div className="space-y-1">
              <div className="font-mono-hud text-[10px] uppercase tracking-[0.2em] text-muted-foreground">yaml</div>
              <textarea
                aria-label="YAML"
                value={installYaml}
                onChange={(e) => setInstallYaml(e.target.value)}
                spellCheck={false}
                className="min-h-48 w-full rounded border border-border bg-background p-3 font-mono-hud text-sm outline-none focus:border-primary/50"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setInstallOpen(false)} className="font-mono-hud text-xs">Cancel</Button>
            <Button
              disabled={store.pending || !installName.trim() || !!installNameError || !installYaml.trim()}
              onClick={async () => {
                const name = installName.trim();
                if (await store.saveWorkflow(name, installYaml)) {
                  setInstallOpen(false);
                  reload();
                  openWorkflow(name);
                }
              }}
              className="font-mono-hud text-xs uppercase tracking-wider"
            >
              Install
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ── new from bundled ── */}
      <Dialog open={copyOpen} onOpenChange={(open) => { if (!open && !store.pending) setCopyOpen(false); }}>
        <DialogContent className="!fixed hud-panel border-border sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="font-mono-hud text-sm uppercase tracking-[0.2em] text-primary">// new from bundled</DialogTitle>
            <DialogDescription className="text-xs text-muted-foreground">
              Copies a bundled workflow into your workflow directory so you can edit it.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-1 py-2">
            <div className="font-mono-hud text-[10px] uppercase tracking-[0.2em] text-muted-foreground">bundled workflow</div>
            <select
              aria-label="Bundled workflow"
              value={copySource}
              onChange={(e) => setCopySource(e.target.value)}
              className="h-8 w-full rounded border border-border bg-secondary/40 px-2 font-mono-hud text-xs outline-none focus:border-primary/50"
            >
              {bundled.map((w) => <option key={w.name} value={w.name}>{w.name}</option>)}
            </select>
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setCopyOpen(false)} className="font-mono-hud text-xs">Cancel</Button>
            <Button
              disabled={store.pending || !copySource}
              onClick={async () => {
                const name = copySource;
                if (await store.copyWorkflow(name)) {
                  setCopyOpen(false);
                  reload();
                  openWorkflow(name);
                }
              }}
              className="font-mono-hud text-xs uppercase tracking-wider"
            >
              Copy
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

// ── selected workflow detail (right pane) ────────────────────────────────────

function WorkflowDetail({ row, reload, onUseInCreate }: {
  row: WorkflowRow;
  reload: () => void;
  onUseInCreate: () => void;
}) {
  const store = useStore();
  const navigate = useNavigate();
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState('');

  const startEdit = () => { setDraft(row.yaml); setEditing(true); };

  const save = async () => {
    if (await store.saveWorkflow(row.name, draft)) {
      setEditing(false);
      reload();
    }
  };

  const remove = async () => {
    if (!window.confirm(`Delete ${row.name}.yaml? This cannot be undone.`)) return;
    if (await store.deleteWorkflow(row.name)) {
      reload();
      navigate('/workflows');
    }
  };

  const validate = async () => { if (await store.validateWorkflow(row.name)) reload(); };

  const copyToUser = async () => {
    if (await store.copyWorkflow(row.name)) {
      reload();
      navigate(`/workflows/${encodeURIComponent(row.name)}`);
    }
  };

  return (
    <Panel className="p-5">
      <div className="flex flex-wrap items-start gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="text-xl font-semibold tracking-tight">{row.name}</h1>
            <OriginTag origin={row.origin} />
            <span className="font-mono-hud text-[10px] text-muted-foreground">{row.file}</span>
          </div>
          {row.description && <p className="mt-1.5 max-w-[640px] text-[13px] text-muted-foreground">{row.description}</p>}
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Button size="sm" variant="outline" disabled={store.pending} onClick={validate} className="font-mono-hud text-[11px] uppercase tracking-wider">
            <CheckCircle2 className="mr-1.5 h-3.5 w-3.5" /> Validate
          </Button>
          <Button
            size="sm"
            variant="outline"
            disabled={!store.settings}
            title={store.settings ? undefined : 'Loading workspace settings…'}
            onClick={onUseInCreate}
            className="font-mono-hud text-[11px] uppercase tracking-wider"
          >
            <Wand2 className="mr-1.5 h-3.5 w-3.5" /> Use in Create
          </Button>
          {row.origin === 'bundled' ? (
            <Button size="sm" disabled={store.pending} onClick={copyToUser} className="font-mono-hud text-[11px] uppercase tracking-wider">
              <Copy className="mr-1.5 h-3.5 w-3.5" /> Copy to user dir
            </Button>
          ) : (
            <>
              {!editing && (
                <Button size="sm" disabled={store.pending} onClick={startEdit} className="font-mono-hud text-[11px] uppercase tracking-wider">
                  <Pencil className="mr-1.5 h-3.5 w-3.5" /> Edit YAML
                </Button>
              )}
              <Button size="sm" variant="destructive" disabled={store.pending} onClick={remove} className="font-mono-hud text-[11px] uppercase tracking-wider">
                <Trash2 className="mr-1.5 h-3.5 w-3.5" /> Delete
              </Button>
            </>
          )}
        </div>
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-3 border-t border-border pt-3">
        <span className="font-mono-hud text-[11px] text-muted-foreground">{row.steps} step(s)</span>
        {row.validation.valid
          ? <span className="font-mono-hud text-[11px] text-[hsl(152_60%_50%)]">✓ valid</span>
          : <span className="font-mono-hud text-[11px] text-destructive">✗ {row.validation.error}</span>}
      </div>

      <div className="mt-4">
        {editing ? (
          <>
            <div className="mb-2 flex items-center justify-between">
              <span className="font-mono-hud text-[10px] uppercase tracking-[0.2em] text-muted-foreground">edit yaml</span>
              <div className="flex items-center gap-2">
                <Button size="sm" variant="outline" disabled={store.pending} onClick={() => setEditing(false)} className="font-mono-hud text-[11px] uppercase tracking-wider">Cancel</Button>
                <Button size="sm" disabled={store.pending} onClick={save} className="font-mono-hud text-[11px] uppercase tracking-wider">Save</Button>
              </div>
            </div>
            <textarea
              aria-label={`${row.name} YAML`}
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              spellCheck={false}
              className="min-h-72 w-full rounded border border-border bg-background p-3 font-mono-hud text-sm outline-none focus:border-primary/50"
            />
          </>
        ) : (
          <pre className="max-h-[28rem] overflow-auto whitespace-pre-wrap break-words rounded border border-border bg-black/30 p-4 font-mono-hud text-sm">
            {row.yaml}
          </pre>
        )}
      </div>
    </Panel>
  );
}
