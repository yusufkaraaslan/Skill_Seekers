import { useEffect, useMemo, useState } from 'react';
import { Panel, SectionHeader, ScopeTag, InstallSet, QualityMeter, CliChip, ALL_CLI_IDS } from '@/components/hud';
import { SOURCE_META, cliById, fmtSize } from '@/lib/data';
import type { CliId, Project, Skill } from '@/lib/data';
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
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from '@/components/ui/sheet';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Switch } from '@/components/ui/switch';
import { Search, MoreHorizontal, ArrowLeftRight, FolderInput, Trash2, Eye, Pencil, Sparkles, Package, X, Bot, CheckCircle2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useStore } from '@/lib/store';

type ScopeFilter = 'all' | 'global' | 'project';

export default function Skills({
  skills,
  projects,
  projectFilter,
  onProjectFilter,
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
  onOpenSkill: (id: string) => void;
  onMove: (ids: string[], dest: 'global' | string) => void;
  onPort: (ids: string[], cli: CliId, opts: { ai: boolean; agent: string }) => void;
  onDelete: (ids: string[]) => void;
  onEnhance: (id: string) => void;
  onPackage: (id: string) => void;
}) {
  const [query, setQuery] = useState('');
  const [scope, setScope] = useState<ScopeFilter>('all');
  const [cliFilter, setCliFilter] = useState<CliId[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [moveFor, setMoveFor] = useState<string[] | null>(null);
  const [portFor, setPortFor] = useState<string[] | null>(null);
  const [deleteFor, setDeleteFor] = useState<string[] | null>(null);

  const filtered = useMemo(() => {
    return skills.filter((s) => {
      if (scope !== 'all' && s.scope !== scope) return false;
      if (projectFilter !== 'all' && s.projectId !== projectFilter) return false;
      if (cliFilter.length && !cliFilter.some((c) => s.installs.includes(c))) return false;
      if (query) {
        const q = query.toLowerCase();
        return (
          s.name.toLowerCase().includes(q) ||
          s.description.toLowerCase().includes(q) ||
          s.tags.some((t) => t.includes(q))
        );
      }
      return true;
    });
  }, [skills, scope, projectFilter, cliFilter, query]);

  const toggleCli = (id: CliId) =>
    setCliFilter((f) => (f.includes(id) ? f.filter((c) => c !== id) : [...f, id]));

  const toggleAll = () =>
    setSelected((sel) => (sel.length === filtered.length ? [] : filtered.map((s) => s.id)));

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
              onChange={(e) => setQuery(e.target.value)}
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
      {selected.length > 0 && (
        <div className="flex items-center gap-3 rounded-md border border-primary/40 bg-primary/10 px-4 py-2 animate-flicker">
          <span className="font-mono-hud text-xs text-primary">{selected.length} selected</span>
          <div className="h-4 w-px bg-primary/30" />
          <Button size="sm" variant="ghost" className="h-7 font-mono-hud text-[11px] uppercase tracking-wider" onClick={() => setMoveFor(selected)}>
            <FolderInput className="mr-1.5 h-3.5 w-3.5" /> Move
          </Button>
          <Button size="sm" variant="ghost" className="h-7 font-mono-hud text-[11px] uppercase tracking-wider" onClick={() => setPortFor(selected)}>
            <ArrowLeftRight className="mr-1.5 h-3.5 w-3.5" /> Port to CLI
          </Button>
          <Button size="sm" variant="ghost" className="h-7 font-mono-hud text-[11px] uppercase tracking-wider text-destructive hover:text-destructive" onClick={() => setDeleteFor(selected)}>
            <Trash2 className="mr-1.5 h-3.5 w-3.5" /> Delete
          </Button>
          <button className="ml-auto text-muted-foreground hover:text-foreground" onClick={() => setSelected([])}>
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* table */}
      <Panel corners={false} className="overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border font-mono-hud text-[10px] uppercase tracking-[0.15em] text-muted-foreground">
              <th className="w-10 px-3 py-2.5 text-left">
                <Checkbox checked={selected.length === filtered.length && filtered.length > 0} onCheckedChange={toggleAll} />
              </th>
              <th className="px-3 py-2.5 text-left font-medium">skill</th>
              <th className="px-3 py-2.5 text-left font-medium">scope</th>
              <th className="px-3 py-2.5 text-left font-medium">installed on</th>
              <th className="px-3 py-2.5 text-left font-medium">quality</th>
              <th className="px-3 py-2.5 text-left font-medium">size</th>
              <th className="px-3 py-2.5 text-left font-medium">updated</th>
              <th className="w-10 px-3 py-2.5" />
            </tr>
          </thead>
          <tbody>
            {filtered.map((s) => (
              <tr
                key={s.id}
                className={cn(
                  'border-b border-border/60 hover:bg-secondary/40 transition-colors cursor-pointer',
                  selected.includes(s.id) && 'bg-primary/5'
                )}
                onClick={() => onOpenSkill(s.id)}
              >
                <td className="px-3 py-2.5" onClick={(e) => e.stopPropagation()}>
                  <Checkbox checked={selected.includes(s.id)} onCheckedChange={() => toggleOne(s.id)} />
                </td>
                <td className="px-3 py-2.5 max-w-[320px]">
                  <div className="flex items-center gap-2">
                    <span className="text-primary/70 font-mono-hud text-xs shrink-0">{SOURCE_META[s.sourceType].icon}</span>
                    <div className="min-w-0">
                      <div className="font-mono-hud text-[13px] font-semibold truncate">{s.name}</div>
                      <div className="text-[11px] text-muted-foreground truncate">{s.description}</div>
                    </div>
                  </div>
                </td>
                <td className="px-3 py-2.5"><ScopeTag scope={s.scope} project={projectName(s.projectId)} /></td>
                <td className="px-3 py-2.5"><InstallSet installs={s.installs} /></td>
                <td className="px-3 py-2.5"><QualityMeter q={s.quality} /></td>
                <td className="px-3 py-2.5 font-mono-hud text-xs text-muted-foreground">{fmtSize(s.sizeKb)}</td>
                <td className="px-3 py-2.5 font-mono-hud text-xs text-muted-foreground">{s.updatedAt}</td>
                <td className="px-3 py-2.5" onClick={(e) => e.stopPropagation()}>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <button className="rounded p-1 text-muted-foreground hover:bg-secondary hover:text-foreground">
                        <MoreHorizontal className="h-4 w-4" />
                      </button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="w-48 font-mono-hud text-xs">
                      <DropdownMenuItem onClick={() => onOpenSkill(s.id)}><Eye className="mr-2 h-3.5 w-3.5" /> View SKILL.md</DropdownMenuItem>
                      <DropdownMenuItem onClick={() => onOpenSkill(s.id)}><Pencil className="mr-2 h-3.5 w-3.5" /> Edit</DropdownMenuItem>
                      <DropdownMenuItem onClick={() => onEnhance(s.id)}><Sparkles className="mr-2 h-3.5 w-3.5" /> Enhance</DropdownMenuItem>
                      <DropdownMenuItem onClick={() => onPackage(s.id)}><Package className="mr-2 h-3.5 w-3.5" /> Package / export</DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem onClick={() => setMoveFor([s.id])}><FolderInput className="mr-2 h-3.5 w-3.5" /> Move to…</DropdownMenuItem>
                      <DropdownMenuItem onClick={() => setPortFor([s.id])}><ArrowLeftRight className="mr-2 h-3.5 w-3.5" /> Port to CLI…</DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem className="text-destructive focus:text-destructive" onClick={() => setDeleteFor([s.id])}>
                        <Trash2 className="mr-2 h-3.5 w-3.5" /> Delete
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={8} className="px-3 py-10 text-center font-mono-hud text-xs text-muted-foreground">
                  ∅ no skills match the current filter
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </Panel>

      {/* ── Move dialog ── */}
      <Dialog open={!!moveFor} onOpenChange={() => setMoveFor(null)}>
        <DialogContent className="!fixed hud-panel border-border sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="font-mono-hud text-sm uppercase tracking-[0.2em] text-primary">// move {moveFor?.length ?? 0} skill(s)</DialogTitle>
            <DialogDescription className="text-xs text-muted-foreground">
              Change scope — global skills load in every session; project skills only in their codebase.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2 py-2">
            <MoveOption label="◈ Global" desc="~/.claude/skills etc. — available everywhere" onClick={() => { onMove(moveFor!, 'global'); setMoveFor(null); setSelected([]); }} />
            {projects.map((p) => (
              <MoveOption key={p.id} label={`▣ ${p.name}`} desc={p.path} onClick={() => { onMove(moveFor!, p.id); setMoveFor(null); setSelected([]); }} />
            ))}
          </div>
        </DialogContent>
      </Dialog>

      {/* ── Port dialog ── */}
      <PortDialog
        ids={portFor}
        skills={skills}
        onClose={() => setPortFor(null)}
        onConfirm={(cli, opts) => { onPort(portFor!, cli, opts); setPortFor(null); setSelected([]); }}
      />

      {/* ── Delete confirm ── */}
      <AlertDialog open={!!deleteFor} onOpenChange={() => setDeleteFor(null)}>
        <AlertDialogContent className="!fixed hud-panel border-border">
          <AlertDialogHeader>
            <AlertDialogTitle className="font-mono-hud text-sm uppercase tracking-[0.2em] text-destructive">
              // delete {deleteFor?.length ?? 0} skill(s)?
            </AlertDialogTitle>
            <AlertDialogDescription className="text-xs text-muted-foreground">
              Removes the skill from every CLI install. Source assets stay in{' '}
              <span className="font-mono-hud text-foreground/80">output/</span> — rebuild anytime with one command.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="font-mono-hud text-xs">Cancel</AlertDialogCancel>
            <AlertDialogAction
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90 font-mono-hud text-xs uppercase tracking-wider"
              onClick={() => { onDelete(deleteFor!); setDeleteFor(null); setSelected([]); }}
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

const CLI_FORMAT: Record<CliId, string> = {
  claude:   'skill dir · SKILL.md + refs',
  kimi:     '.zip · SKILL.md',
  cursor:   '.cursorrules (flattened)',
  windsurf: '.windsurfrules',
  gemini:   '.tar.gz bundle',
  codex:    'instructions.md',
  opencode: 'agent .md',
};

function PortDialog({
  ids,
  skills,
  onClose,
  onConfirm,
}: {
  ids: string[] | null;
  skills: Skill[];
  onClose: () => void;
  onConfirm: (cli: CliId, opts: { ai: boolean; agent: string }) => void;
}) {
  const [ai, setAi] = useState(true);
  const [agent, setAgent] = useState('claude');
  const selectedSkills = skills.filter((s) => ids?.includes(s.id));

  return (
    <Dialog open={!!ids} onOpenChange={onClose}>
      <DialogContent className="!fixed hud-panel border-border sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="font-mono-hud text-sm uppercase tracking-[0.2em] text-primary">
            // port {ids?.length ?? 0} skill(s)
          </DialogTitle>
          <DialogDescription className="text-xs text-muted-foreground">
            Repackage + install to another CLI. With AI assist, the agent rewrites content to the
            target's conventions — e.g. SKILL.md → .cursorrules — instead of a raw copy.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-1.5 py-2 max-h-[320px] overflow-y-auto">
          {ALL_CLI_IDS.map((id) => {
            const cli = cliById(id);
            const already = selectedSkills.length > 0 && selectedSkills.every((s) => s.installs.includes(id));
            const partial = !already && selectedSkills.some((s) => s.installs.includes(id));
            return (
              <button
                key={id}
                disabled={!cli.detected}
                onClick={() => onConfirm(id, { ai, agent })}
                className={cn(
                  'flex w-full items-center gap-3 rounded border px-3 py-2.5 text-left transition-colors',
                  cli.detected
                    ? already
                      ? 'border-border bg-secondary/20 hover:border-[hsl(45_93%_55%/0.5)]'
                      : 'border-border bg-secondary/40 hover:border-primary/50'
                    : 'border-border opacity-40 cursor-not-allowed'
                )}
              >
                <CliChip id={id} />
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold">{cli.name}</span>
                    {already && (
                      <span className="flex items-center gap-1 font-mono-hud text-[9px] text-[hsl(45_93%_60%)]">
                        <CheckCircle2 className="h-3 w-3" /> installed — re-port
                      </span>
                    )}
                    {partial && (
                      <span className="font-mono-hud text-[9px] text-[hsl(258_90%_70%)]">partially installed</span>
                    )}
                  </div>
                  <div className="font-mono-hud text-[10px] text-muted-foreground truncate">
                    {cli.detected ? `${cli.globalPath} · ${CLI_FORMAT[id]}` : 'not detected on this machine'}
                  </div>
                </div>
                <ArrowLeftRight className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
              </button>
            );
          })}
        </div>

        <DialogFooter className="flex-col gap-3 sm:flex-col sm:space-x-0">
          <div className="flex items-center justify-between w-full rounded border border-primary/30 bg-primary/5 px-3 py-2">
            <span className="flex items-center gap-2 font-mono-hud text-[11px] text-foreground/85">
              <Bot className="h-3.5 w-3.5 text-primary" /> AI-assisted conversion
            </span>
            <div className="flex items-center gap-2">
              <div className="flex rounded border border-border overflow-hidden">
                {['claude', 'kimi', 'codex'].map((a) => (
                  <button
                    key={a}
                    onClick={() => setAgent(a)}
                    disabled={!ai}
                    className={cn(
                      'px-2 py-1 font-mono-hud text-[9px] transition-colors',
                      agent === a && ai ? 'bg-primary/15 text-primary' : 'text-muted-foreground',
                      !ai && 'opacity-40'
                    )}
                  >
                    {a}
                  </button>
                ))}
              </div>
              <Switch checked={ai} onCheckedChange={setAi} />
            </div>
          </div>
          <span className="font-mono-hud text-[10px] text-muted-foreground">
            undetected CLIs need a local CLI install first · re-port overwrites the target copy
          </span>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
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

// ── Detail drawer (rendered by App so table rows + drawer share state) ───────

export function SkillDrawer({
  skill,
  onClose,
  onEnhance,
  onPackage,
  onSave,
}: {
  skill: Skill | null;
  onClose: () => void;
  onEnhance: (id: string) => void;
  onPackage: (id: string) => void;
  onSave: (id: string, content: string) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState<string | null>(null);
  const { projects } = useStore();
  const project = projects.find((p) => p.id === skill?.projectId);

  useEffect(() => {
    setEditing(false);
    setDraft(null);
  }, [skill?.id]);

  const toggleEdit = () => {
    if (editing && skill && draft !== null && draft !== skill.content) {
      onSave(skill.id, draft);
    }
    setEditing(!editing);
  };

  return (
    <Sheet open={!!skill} onOpenChange={onClose}>
      <SheetContent side="right" className="!fixed w-[560px] sm:max-w-[560px] hud-panel border-l-border p-0 scanline">
        {skill && (
          <div className="flex h-full flex-col">
            <SheetHeader className="border-b border-border p-5 pb-4">
              <div className="flex items-center gap-2 flex-wrap">
                <ScopeTag scope={skill.scope} project={project?.name} />
                <span className="font-mono-hud text-[10px] text-muted-foreground">v{skill.version}</span>
                <span className="font-mono-hud text-[10px] text-muted-foreground">·</span>
                <span className="font-mono-hud text-[10px] text-muted-foreground">{SOURCE_META[skill.sourceType].label}</span>
              </div>
              <SheetTitle className="font-mono-hud text-lg">{skill.name}</SheetTitle>
              <SheetDescription className="text-xs leading-relaxed">{skill.description}</SheetDescription>
              <div className="flex items-center gap-2 pt-1 flex-wrap">
                <InstallSet installs={skill.installs} />
                <div className="ml-auto"><QualityMeter q={skill.quality} /></div>
              </div>
            </SheetHeader>

            <div className="flex gap-2 border-b border-border px-5 py-3">
              <Button size="sm" variant={editing ? 'default' : 'outline'} onClick={toggleEdit} className="h-7 font-mono-hud text-[10px] uppercase tracking-widest">
                <Pencil className="mr-1 h-3 w-3" /> {editing ? 'save' : 'edit'}
              </Button>
              <Button size="sm" variant="outline" onClick={() => onEnhance(skill.id)} className="h-7 font-mono-hud text-[10px] uppercase tracking-widest">
                <Sparkles className="mr-1 h-3 w-3" /> enhance
              </Button>
              <Button size="sm" variant="outline" onClick={() => onPackage(skill.id)} className="h-7 font-mono-hud text-[10px] uppercase tracking-widest">
                <Package className="mr-1 h-3 w-3" /> package
              </Button>
              <span className="ml-auto font-mono-hud text-[10px] text-muted-foreground self-center">{fmtSize(skill.sizeKb)}</span>
            </div>

            <ScrollArea className="flex-1">
              <div className="p-5 space-y-5">
                {/* SKILL.md */}
                <div>
                  <div className="font-mono-hud text-[10px] uppercase tracking-[0.2em] text-muted-foreground mb-2">SKILL.md</div>
                  {editing ? (
                    <textarea
                      value={draft ?? skill.content}
                      onChange={(e) => setDraft(e.target.value)}
                      spellCheck={false}
                      className="w-full h-72 rounded border border-primary/40 bg-black/40 p-4 font-mono-hud text-[12px] leading-relaxed text-foreground/90 outline-none resize-y"
                    />
                  ) : (
                    <div className="rounded border border-border bg-black/40 p-4 font-mono-hud text-[12px] leading-relaxed overflow-x-auto">
                      <MiniMd text={skill.content} />
                    </div>
                  )}
                </div>

                {/* files */}
                <div>
                  <div className="font-mono-hud text-[10px] uppercase tracking-[0.2em] text-muted-foreground mb-2">bundle files</div>
                  <div className="rounded border border-border divide-y divide-border/60">
                    {skill.files.map((f) => (
                      <div key={f.path} className="flex items-center justify-between px-3 py-1.5 font-mono-hud text-[11px]">
                        <span className="text-foreground/80">▸ {f.path}</span>
                        <span className="text-muted-foreground">{f.size}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* provenance */}
                <div>
                  <div className="font-mono-hud text-[10px] uppercase tracking-[0.2em] text-muted-foreground mb-2">provenance</div>
                  <div className="grid grid-cols-2 gap-px rounded border border-border overflow-hidden font-mono-hud text-[11px]">
                    {[
                      ['source', skill.source],
                      ['updated', skill.updatedAt],
                      ['tags', skill.tags.join(' · ')],
                      ['installs', `${skill.installs.length} CLIs`],
                    ].map(([k, v]) => (
                      <div key={k} className="bg-secondary/30 px-3 py-2">
                        <div className="text-[9px] uppercase tracking-widest text-muted-foreground">{k}</div>
                        <div className="mt-0.5 text-foreground/85 truncate">{v}</div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </ScrollArea>
          </div>
        )}
      </SheetContent>
    </Sheet>
  );
}

// ultra-light markdown renderer for the preview pane
function MiniMd({ text }: { text: string }) {
  const lines = text.split('\n');
  let inFront = false;
  return (
    <>
      {lines.map((l, i) => {
        if (l === '---') {
          inFront = !inFront;
          return <div key={i} className="text-muted-foreground/50 select-none">───</div>;
        }
        if (inFront) return <div key={i} className="text-muted-foreground">{l}</div>;
        if (l.startsWith('# ')) return <div key={i} className="text-primary font-bold text-[14px] mt-1">{l.slice(2)}</div>;
        if (l.startsWith('## ')) return <div key={i} className="text-[hsl(45_93%_60%)] font-semibold mt-3">{l.slice(3)}</div>;
        if (!l.trim()) return <div key={i} className="h-2" />;
        return (
          <div key={i} className="text-foreground/80">
            {l.split(/(`[^`]+`)/g).map((part, j) =>
              part.startsWith('`') ? (
                <code key={j} className="rounded bg-primary/10 px-1 text-primary">{part.slice(1, -1)}</code>
              ) : (
                <span key={j}>{part}</span>
              )
            )}
          </div>
        );
      })}
    </>
  );
}
