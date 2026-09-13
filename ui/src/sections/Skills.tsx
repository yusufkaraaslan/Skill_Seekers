import { useMemo, useState } from 'react';
import { Panel, SectionHeader, ScopeTag, InstallSet, QualityMeter, CliChip, OriginTag, Pager } from '@/components/hud';
import { ALL_CLI_IDS, SOURCE_META, cliById, fmtSize, matchesSkillQuery } from '@/lib/data';
import { usePagination } from '@/hooks/use-pagination';
import type { CliId, Project, Skill, SkillOrigin } from '@/lib/data';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Search, MoreHorizontal, ArrowLeftRight, FolderInput, Trash2, Eye, Pencil, Sparkles, Package, X, Lock } from 'lucide-react';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { cn } from '@/lib/utils';
import { useStore } from '@/lib/store';
import { api } from '@/lib/api';

type ScopeFilter = 'all' | 'global' | 'project';
type OriginFilter = 'all' | SkillOrigin;
const ORIGIN_FILTERS: OriginFilter[] = ['all', 'seeker', 'plugin', 'manual'];
const isOwned = (s: Skill) => s.origin === 'seeker';

export default function Skills({
  skills,
  projects,
  projectFilter,
  onProjectFilter,
  query,
  onQuery,
  onOpenSkill,
  onMove,
  onPort,
  onDelete,
  onEnhance,
  onPackage,
}: {
  skills: Skill[];
  projects: Project[];
  projectFilter: string;
  onProjectFilter: (p: string) => void;
  query: string;
  onQuery: (q: string) => void;
  onOpenSkill: (id: string) => void;
  onMove: (ids: string[], dest: 'global' | string) => Promise<boolean>;
  onPort: (ids: string[], cli: CliId, replace: boolean) => Promise<boolean>;
  onDelete: (ids: string[]) => Promise<boolean>;
  onEnhance: (id: string) => Promise<boolean>;
  onPackage: (id: string, targets?: string[]) => Promise<boolean>;
}) {
  const { pending } = useStore();
  const [packageFor, setPackageFor] = useState<string | null>(null);
  const [scope, setScope] = useState<ScopeFilter>('all');
  const [origin, setOrigin] = useState<OriginFilter>('all');
  const [cliFilter, setCliFilter] = useState<CliId[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [moveFor, setMoveFor] = useState<string[] | null>(null);
  const [portFor, setPortFor] = useState<string[] | null>(null);
  const [deleteFor, setDeleteFor] = useState<string[] | null>(null);

  const filtered = useMemo(() => {
    return skills.filter((s) => {
      if (scope !== 'all' && s.scope !== scope) return false;
      if (origin !== 'all' && s.origin !== origin) return false;
      if (projectFilter !== 'all' && s.projectId !== projectFilter) return false;
      if (cliFilter.length && !cliFilter.some((c) => s.installs.includes(c))) return false;
      return matchesSkillQuery(s, query);
    });
  }, [skills, scope, origin, projectFilter, cliFilter, query]);

  const pager = usePagination(
    filtered,
    'skills',
    `${query}|${scope}|${origin}|${projectFilter}|${cliFilter.join(',')}`,
  );

  const toggleCli = (id: CliId) =>
    setCliFilter((f) => (f.includes(id) ? f.filter((c) => c !== id) : [...f, id]));

  const toggleAll = () =>
    setSelected((sel) => {
      const pageIds = pager.slice.map((s) => s.id);
      const allOnPage = pageIds.length > 0 && pageIds.every((id) => sel.includes(id));
      return allOnPage ? sel.filter((id) => !pageIds.includes(id)) : Array.from(new Set([...sel, ...pageIds]));
    });

  const toggleOne = (id: string) =>
    setSelected((sel) => (sel.includes(id) ? sel.filter((x) => x !== id) : [...sel, id]));

  const projectName = (pid?: string) => projects.find((p) => p.id === pid)?.name;

  return (
    <div className="space-y-4 animate-flicker">
      <SectionHeader
        title="Skill registry"
        sub={`${filtered.length} of ${skills.length} skills · all CLIs, one grid`}
        right={
          <div className="relative w-64">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
            <Input
              value={query}
              onChange={(e) => onQuery(e.target.value)}
              placeholder="filter by name, tag, keyword…"
              className="pl-8 h-8 font-mono-hud text-xs bg-secondary/50"
            />
          </div>
        }
      />

      {/* filter row */}
      <div className="flex flex-wrap items-center gap-2">
        <div className="flex rounded-md border border-border overflow-hidden">
          {(['all', 'global', 'project'] as ScopeFilter[]).map((sc) => (
            <button
              key={sc}
              onClick={() => setScope(sc)}
              className={cn(
                'px-3 py-1.5 font-mono-hud text-[11px] uppercase tracking-wider transition-colors',
                scope === sc ? 'bg-primary/15 text-primary' : 'text-muted-foreground hover:text-foreground'
              )}
            >
              {sc}
            </button>
          ))}
        </div>
        <span className="font-mono-hud text-[10px] uppercase tracking-widest text-muted-foreground mx-1">origin:</span>
        <div className="flex rounded-md border border-border overflow-hidden">
          {ORIGIN_FILTERS.map((o) => (
            <button
              key={o}
              onClick={() => setOrigin(o)}
              className={cn(
                'px-2.5 py-1.5 font-mono-hud text-[10px] uppercase tracking-wider transition-colors',
                origin === o ? 'bg-primary/15 text-primary' : 'text-muted-foreground hover:text-foreground'
              )}
            >
              {o}
            </button>
          ))}
        </div>
        <span className="font-mono-hud text-[10px] uppercase tracking-widest text-muted-foreground mx-1">project:</span>
        <div className="flex rounded-md border border-border overflow-hidden">
          {[{ id: 'all', name: 'all' }, ...projects.map((p) => ({ id: p.id, name: p.name }))].map((p) => (
            <button
              key={p.id}
              onClick={() => onProjectFilter(p.id)}
              className={cn(
                'px-2.5 py-1.5 font-mono-hud text-[10px] tracking-wider transition-colors',
                projectFilter === p.id ? 'bg-[hsl(45_93%_55%/0.15)] text-[hsl(45_93%_60%)]' : 'text-muted-foreground hover:text-foreground'
              )}
            >
              {p.name}
            </button>
          ))}
        </div>
        <span className="font-mono-hud text-[10px] uppercase tracking-widest text-muted-foreground mx-1">installed on:</span>
        {ALL_CLI_IDS.map((id) => (
          <button key={id} onClick={() => toggleCli(id)} className={cn('transition-all', cliFilter.length && !cliFilter.includes(id) && 'opacity-35')}>
            <CliChip id={id} />
          </button>
        ))}
        {cliFilter.length > 0 && (
          <button onClick={() => setCliFilter([])} className="text-muted-foreground hover:text-foreground">
            <X className="h-3.5 w-3.5" />
          </button>
        )}
      </div>

      {/* bulk action bar */}
      {selected.length > 0 && (() => {
        const owned = selected.filter((id) => skills.find((s) => s.id === id && isOwned(s)));
        const skipped = selected.length - owned.length;
        return (
          <div className="flex items-center gap-3 rounded-md border border-primary/40 bg-primary/10 px-4 py-2 animate-flicker">
            <span className="font-mono-hud text-xs text-primary">
              {selected.length} selected{skipped > 0 && <span className="text-muted-foreground"> · {skipped} read-only skipped</span>}
            </span>
            <div className="h-4 w-px bg-primary/30" />
            <Button size="sm" variant="ghost" disabled={owned.length === 0} className="h-7 font-mono-hud text-[11px] uppercase tracking-wider" onClick={() => setMoveFor(owned)}>
              <FolderInput className="mr-1.5 h-3.5 w-3.5" /> Move
            </Button>
            <Button size="sm" variant="ghost" className="h-7 font-mono-hud text-[11px] uppercase tracking-wider" onClick={() => setPortFor(selected)}>
              <ArrowLeftRight className="mr-1.5 h-3.5 w-3.5" /> Port to CLI
            </Button>
            <Button size="sm" variant="ghost" disabled={owned.length === 0} className="h-7 font-mono-hud text-[11px] uppercase tracking-wider text-destructive hover:text-destructive" onClick={() => setDeleteFor(owned)}>
              <Trash2 className="mr-1.5 h-3.5 w-3.5" /> Delete
            </Button>
            <button className="ml-auto text-muted-foreground hover:text-foreground" onClick={() => setSelected([])}>
              <X className="h-4 w-4" />
            </button>
          </div>
        );
      })()}

      {/* table */}
      <Panel corners={false} className="overflow-hidden">
        <div className="overflow-x-auto" role="region" aria-label="Skills table" tabIndex={0}><table className="w-full min-w-[800px] text-sm">
          <thead>
            <tr className="border-b border-border font-mono-hud text-[10px] uppercase tracking-[0.15em] text-muted-foreground">
              <th className="w-10 px-3 py-2.5 text-left">
                <Checkbox aria-label="Select this page" checked={pager.slice.length > 0 && pager.slice.every((s) => selected.includes(s.id))} onCheckedChange={toggleAll} />
              </th>
              <th className="px-3 py-2.5 text-left font-medium">skill</th>
              <th className="px-3 py-2.5 text-left font-medium">origin</th>
              <th className="px-3 py-2.5 text-left font-medium">scope</th>
              <th className="px-3 py-2.5 text-left font-medium">installed on</th>
              <th className="px-3 py-2.5 text-left font-medium">quality</th>
              <th className="px-3 py-2.5 text-left font-medium">size</th>
              <th className="px-3 py-2.5 text-left font-medium">updated</th>
              <th className="w-10 px-3 py-2.5" />
            </tr>
          </thead>
          <tbody>
            {pager.slice.map((s) => (
              <tr
                key={s.id}
                className={cn(
                  'border-b border-border/60 hover:bg-secondary/40 transition-colors cursor-pointer',
                  selected.includes(s.id) && 'bg-primary/5'
                )}
                onClick={() => onOpenSkill(s.id)}
              >
                <td className="px-3 py-2.5" onClick={(e) => e.stopPropagation()}>
                  <Checkbox aria-label={`Select ${s.name}`} checked={selected.includes(s.id)} onCheckedChange={() => toggleOne(s.id)} />
                </td>
                <td className="px-3 py-2.5 max-w-[320px]">
                  <div className="flex items-center gap-2">
                    <span className="text-primary/70 font-mono-hud text-xs shrink-0">{SOURCE_META[s.sourceType].icon}</span>
                    <div className="min-w-0">
                      <div className="flex items-center gap-1.5">
                        <button className="font-mono-hud text-[13px] font-semibold truncate text-left" onClick={(e) => { e.stopPropagation(); onOpenSkill(s.id); }}>{s.name}</button>
                        {!isOwned(s) && (
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <Lock className="h-3 w-3 shrink-0 text-muted-foreground" />
                            </TooltipTrigger>
                            <TooltipContent side="top" className="font-mono-hud text-xs">managed outside Skill Seekers</TooltipContent>
                          </Tooltip>
                        )}
                      </div>
                      <div className="text-[11px] text-muted-foreground truncate">{s.description}</div>
                    </div>
                  </div>
                </td>
                <td className="px-3 py-2.5"><OriginTag origin={s.origin} pluginName={s.pluginName} /></td>
                <td className="px-3 py-2.5"><ScopeTag scope={s.scope} project={projectName(s.projectId)} /></td>
                <td className="px-3 py-2.5"><InstallSet installs={s.installs} /></td>
                <td className="px-3 py-2.5"><QualityMeter q={s.quality} /></td>
                <td className="px-3 py-2.5 font-mono-hud text-xs text-muted-foreground">{fmtSize(s.sizeKb)}</td>
                <td className="px-3 py-2.5 font-mono-hud text-xs text-muted-foreground">{s.updatedAt}</td>
                <td className="px-3 py-2.5" onClick={(e) => e.stopPropagation()}>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <button aria-label={`Actions for ${s.name}`} className="rounded p-1 text-muted-foreground hover:bg-secondary hover:text-foreground">
                        <MoreHorizontal className="h-4 w-4" />
                      </button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="w-48 font-mono-hud text-xs">
                      <DropdownMenuItem onClick={() => onOpenSkill(s.id)}><Eye className="mr-2 h-3.5 w-3.5" /> View SKILL.md</DropdownMenuItem>
                      {isOwned(s) && (
                        <>
                          <DropdownMenuItem onClick={() => onOpenSkill(s.id)}><Pencil className="mr-2 h-3.5 w-3.5" /> Edit</DropdownMenuItem>
                          <DropdownMenuItem onClick={() => onEnhance(s.id)}><Sparkles className="mr-2 h-3.5 w-3.5" /> Enhance</DropdownMenuItem>
                        </>
                      )}
                      <DropdownMenuItem onClick={() => setPackageFor(s.id)}><Package className="mr-2 h-3.5 w-3.5" /> Package / export</DropdownMenuItem>
                      <DropdownMenuSeparator />
                      {isOwned(s) && (
                        <DropdownMenuItem onClick={() => setMoveFor([s.id])}><FolderInput className="mr-2 h-3.5 w-3.5" /> Move to…</DropdownMenuItem>
                      )}
                      <DropdownMenuItem onClick={() => setPortFor([s.id])}><ArrowLeftRight className="mr-2 h-3.5 w-3.5" /> Port to CLI…</DropdownMenuItem>
                      {isOwned(s) && (
                        <>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem className="text-destructive focus:text-destructive" onClick={() => setDeleteFor([s.id])}>
                            <Trash2 className="mr-2 h-3.5 w-3.5" /> Delete
                          </DropdownMenuItem>
                        </>
                      )}
                    </DropdownMenuContent>
                  </DropdownMenu>
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={9} className="px-3 py-10 text-center font-mono-hud text-xs text-muted-foreground">
                  ∅ no skills match the current filter
                </td>
              </tr>
            )}
          </tbody>
        </table></div>
        <Pager page={pager.page} pageCount={pager.pageCount} pageSize={pager.pageSize} total={pager.total} onPage={pager.setPage} onPageSize={pager.setPageSize} />
      </Panel>

      {/* ── Move dialog ── */}
      <Dialog open={!!moveFor} onOpenChange={() => setMoveFor(null)}>
        <DialogContent className="!fixed hud-panel border-border sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="font-mono-hud text-sm uppercase tracking-[0.2em] text-primary">// move {moveFor?.length ?? 0} skill(s)</DialogTitle>
            <DialogDescription className="text-xs text-muted-foreground">
              Organize skills within this HUD. Project assignment does not change CLI installation paths or which sessions load a skill.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2 py-2">
            <MoveOption label="◈ Global" desc="Unassigned in this workspace" onClick={async () => { if (await onMove(moveFor!, 'global')) { setMoveFor(null); setSelected([]); } }} />
            {projects.map((p) => (
              <MoveOption key={p.id} label={`▣ ${p.name}`} desc={p.path} onClick={async () => { if (await onMove(moveFor!, p.id)) { setMoveFor(null); setSelected([]); } }} />
            ))}
          </div>
        </DialogContent>
      </Dialog>

      {/* ── Port dialog ── */}
      <PortDialog
        key={portFor?.join(",") ?? "closed"}
        ids={portFor}
        skills={skills}
        onClose={() => setPortFor(null)}
        onConfirm={async (cli, replace) => { const ok = await onPort(portFor!, cli, replace); if (ok) { setPortFor(null); setSelected([]); } return ok; }}
      />

      {packageFor && <PackageDialog id={packageFor} onClose={() => setPackageFor(null)} onPackage={onPackage} />}
      <ArchivedSkills />
      {/* ── Delete confirm ── */}
      <AlertDialog open={!!deleteFor} onOpenChange={() => setDeleteFor(null)}>
        <AlertDialogContent className="!fixed hud-panel border-border">
          <AlertDialogHeader>
            <AlertDialogTitle className="font-mono-hud text-sm uppercase tracking-[0.2em] text-destructive">
              // delete {deleteFor?.length ?? 0} skill(s)?
            </AlertDialogTitle>
            <AlertDialogDescription className="text-xs text-muted-foreground">
              Moves source files to the recoverable archive and removes copies installed from this source by Seeker. Other installations remain untouched. Restore source files from Archived skills below; reinstall CLI copies afterward.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="font-mono-hud text-xs">Cancel</AlertDialogCancel>
            <AlertDialogAction
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90 font-mono-hud text-xs uppercase tracking-wider"
              disabled={pending}
              onClick={async (e) => { e.preventDefault(); if (await onDelete(deleteFor!)) { setDeleteFor(null); setSelected([]); } }}
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}


// ── Port dialog with AI-assisted conversion ──────────────────────────────────

function PortDialog({ ids, onClose, onConfirm }: {
  ids: string[] | null; skills: Skill[]; onClose: () => void;
  onConfirm: (cli: CliId, replace: boolean) => Promise<boolean>;
}) {
  const { pending, clis } = useStore();
  // Only CLIs actually present on this machine: installing into a missing
  // tool's directory would make the HUD report that tool as detected.
  const available = ALL_CLI_IDS.filter(id => clis.find(c => c.id === id)?.detected);
  const [target, setTarget] = useState<CliId>(available[0] ?? 'claude');
  const [replace, setReplace] = useState(false);
  return <Dialog open={!!ids} onOpenChange={() => { if (!pending) onClose(); }}>
    <DialogContent className="hud-panel sm:max-w-lg">
      <DialogHeader><DialogTitle>Install {ids?.length ?? 0} skill(s)</DialogTitle><DialogDescription>Copy the complete skill folder into the selected CLI's user skill directory. Shared skill directories can also be read by other compatible CLIs.</DialogDescription></DialogHeader>
      <label htmlFor="install-cli">Destination CLI</label>
      <select id="install-cli" className="rounded border bg-background p-2" value={target} onChange={e => setTarget(e.target.value as CliId)}>
        {available.map(id => <option key={id} value={id}>{cliById(id).name} — {cliById(id).globalPath}</option>)}
      </select>
      {!available.length && <p className="text-sm text-destructive">No supported CLI was detected on this machine.</p>}
      <label className="flex items-center gap-2 text-sm"><Checkbox checked={replace} onCheckedChange={v => setReplace(v === true)} />Replace existing destination copies</label>
      {replace && <p className="text-sm text-destructive">Existing destination content will be replaced. The source is preserved.</p>}
      <DialogFooter><Button variant="outline" disabled={pending} onClick={onClose}>Cancel</Button><Button disabled={pending || !available.length} onClick={() => onConfirm(target, replace)}>Install</Button></DialogFooter>
    </DialogContent>
  </Dialog>;
}

function PackageDialog({ id, onClose, onPackage }: { id: string; onClose: () => void; onPackage: (id: string, targets?: string[]) => Promise<boolean> }) {
  const { settings, pending } = useStore();
  const [targets, setTargets] = useState(['claude']);
  return <Dialog open onOpenChange={() => { if (!pending) onClose(); }}><DialogContent className="hud-panel"><DialogHeader><DialogTitle>Package skill</DialogTitle><DialogDescription>Choose package formats. Output locations appear in Jobs.</DialogDescription></DialogHeader>
    <div className="grid grid-cols-2 gap-2 max-h-80 overflow-y-auto">{settings?.capabilities.targets.map(target => <label key={target} className="flex items-center gap-2 text-sm"><Checkbox checked={targets.includes(target)} onCheckedChange={v => setTargets(t => v ? [...t, target] : t.filter(x => x !== target))} />{target}</label>)}</div>
    <DialogFooter><Button disabled={pending || !targets.length} onClick={async () => { if (await onPackage(id, targets)) onClose(); }}>Package</Button></DialogFooter>
  </DialogContent></Dialog>;
}

function ArchivedSkills() {
  const { restoreSkill, pending } = useStore();
  const [entries, setEntries] = useState<Awaited<ReturnType<typeof api.archivedSkills>>>([]);
  const [error, setError] = useState('');
  const load = () => api.archivedSkills().then(data => { setEntries(data); setError(''); }).catch(e => setError(String(e)));
  return <details className="rounded border p-3" onToggle={e => { if (e.currentTarget.open) load(); }}><summary className="cursor-pointer text-sm">Archived skills</summary>
    {error && <p role="alert">{error}</p>}{!entries.length && <p className="mt-2 text-sm text-muted-foreground">No archived skills. Reopen to refresh.</p>}
    {entries.map(entry => <div key={entry.id} className="mt-2 flex flex-wrap items-center gap-2 text-sm"><span>{entry.name} · {entry.archivedAt}</span><Button size="sm" disabled={pending} onClick={async () => { if (await restoreSkill(entry.id)) await load(); }}>Restore</Button></div>)}
  </details>;
}

function MoveOption({ label, desc, onClick }: { label: string; desc: string; onClick: () => void }) {
  return (
    <button onClick={onClick} className="flex w-full items-center justify-between rounded border border-border bg-secondary/40 px-3 py-2.5 text-left hover:border-primary/50 transition-colors">
      <div>
        <div className="font-mono-hud text-xs font-semibold">{label}</div>
        <div className="font-mono-hud text-[10px] text-muted-foreground">{desc}</div>
      </div>
      <FolderInput className="h-3.5 w-3.5 text-muted-foreground" />
    </button>
  );
}
