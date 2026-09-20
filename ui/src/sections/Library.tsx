import { useState } from 'react';
import { useStore } from '@/lib/store';
import { Panel, SectionHeader, Pager } from '@/components/hud';
import type { ConfigEntry, ConfigSource } from '@/lib/data';
import { usePagination } from '@/hooks/use-pagination';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import { GenerateConfigForm } from '@/components/generate-config-form';
import { GitBranch, Plus, RefreshCw, FileJson, ArrowUpCircle, Sparkles, Trash2, CloudDownload, Search } from 'lucide-react';
import { cn } from '@/lib/utils';

const ORIGIN_STYLE: Record<ConfigEntry['origin'], string> = {
  preset:  '187 92% 50%',
  scanned: '258 90% 66%',
  custom:  '45 93% 55%',
  synced:  '152 60% 45%',
};

export default function Library({
  sources,
  entries,
  onAddSource,
  onFetchSource,
  onFetchOfficial,
  onRemoveSource,
  onBuild,
  onOpenConfig,
}: {
  sources: ConfigSource[];
  entries: ConfigEntry[];
  onAddSource: (repo: string) => Promise<boolean>;
  onFetchSource: (name: string) => void;
  onFetchOfficial: (name: string) => void;
  onRemoveSource: (name: string) => void;
  onBuild: (path: string, name: string) => void;
  onOpenConfig: (id: string) => void;
}) {
  const { pending } = useStore();
  const [activeSource, setActiveSource] = useState<string>('all');
  const [addOpen, setAddOpen] = useState(false);
  const [generateOpen, setGenerateOpen] = useState(false);
  const [repo, setRepo] = useState('');
  const [query, setQuery] = useState('');

  const q = query.trim().toLowerCase();
  const filtered = entries.filter((c) => {
    if (activeSource !== 'all' && c.source !== activeSource) return false;
    if (!q) return true;
    return (
      c.name.toLowerCase().includes(q) ||
      c.framework.toLowerCase().includes(q) ||
      (c.description ?? '').toLowerCase().includes(q)
    );
  });

  const pager = usePagination(filtered, 'configs', `${query}|${activeSource}`);

  return (
    <div className="space-y-5 animate-flicker">
      <SectionHeader
        title="Scrape configs"
        sub="recipes Skill Seekers builds skills from — presets, scanned & custom, backed by git remotes"
        right={
          <div className="flex flex-wrap items-center gap-2">
            <div className="relative w-56">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
              <Input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="filter configs…" className="pl-8 h-8 font-mono-hud text-xs bg-secondary/50" />
            </div>
            <Button size="sm" variant="outline" onClick={() => setGenerateOpen(true)} className="font-mono-hud text-xs uppercase tracking-wider">
              <Sparkles className="mr-1.5 h-3.5 w-3.5" /> Generate with AI
            </Button>
            <Button size="sm" onClick={() => setAddOpen(true)} className="font-mono-hud text-xs uppercase tracking-wider">
              <Plus className="mr-1.5 h-3.5 w-3.5" /> Add config source
            </Button>
          </div>
        }
      />

      {/* remote sources */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
        {sources.length === 0 && (
          <Panel corners={false} className="p-6 col-span-full text-center">
            <p className="font-mono-hud text-xs text-muted-foreground">
              no remote config sources — register a git repo of unified configs to sync presets across machines
            </p>
          </Panel>
        )}
        {sources.map((s) => (
          <Panel key={s.name} corners={false}
            className={cn('p-4 cursor-pointer transition-all group relative', activeSource === s.id && 'border-primary/60')}
            role="button" tabIndex={0} aria-pressed={activeSource === s.id}
            onKeyDown={e => { if (e.target === e.currentTarget && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); setActiveSource(activeSource === s.id ? 'all' : s.id); } }}
            onClick={() => setActiveSource(activeSource === s.id ? 'all' : s.id)}
          >
            <div className="flex items-center gap-2">
              <GitBranch className="h-3.5 w-3.5 text-primary shrink-0" />
              <span className="font-mono-hud text-xs font-semibold truncate">{s.name}</span>
              <span className={cn(
                'ml-auto rounded border px-1.5 py-0.5 font-mono-hud text-[9px] uppercase tracking-wider shrink-0',
                s.kind === 'official' ? 'border-primary/40 text-primary' : 'border-[hsl(45_93%_55%/0.4)] text-[hsl(45_93%_60%)]'
              )}>
                {s.kind}
              </span>
            </div>
            <div className="mt-1 font-mono-hud text-[10px] text-muted-foreground truncate">{s.repo} <span className="text-primary/70">({s.branch})</span></div>
            <div className="mt-3 flex items-center justify-between">
              <span className="font-mono-hud text-[10px] text-muted-foreground">{s.configs} configs · {s.lastFetch}</span>
              <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
                {(s as { connected?: boolean }).connected === false && (
                  <span className="font-mono-hud text-[9px] text-muted-foreground">○ offline</span>
                )}
                {s.id !== 'official' && (
                  <>
                    <Button size="sm" variant="ghost" className="h-6 px-2 font-mono-hud text-[10px]" aria-label={`Fetch config source ${s.name}`} onClick={() => onFetchSource(s.name)}>
                      <RefreshCw className="h-3 w-3" />
                    </Button>
                    <Button size="sm" variant="ghost" className="h-6 px-2 font-mono-hud text-[10px] " aria-label={`Remove config source ${s.name}`} onClick={() => { if (window.confirm(`Remove config source ${s.name}?`)) onRemoveSource(s.name); }}>
                      <Trash2 className="h-3 w-3 text-muted-foreground hover:text-destructive" />
                    </Button>
                  </>
                )}
              </div>
            </div>
          </Panel>
        ))}
      </div>

      {/* entries table */}
      <Panel corners={false} className="overflow-hidden">
        <div className="overflow-x-auto" role="region" aria-label="Configs table" tabIndex={0}><table className="w-full min-w-[760px] text-sm">
          <thead>
            <tr className="border-b border-border font-mono-hud text-[10px] uppercase tracking-[0.15em] text-muted-foreground">
              <th className="px-4 py-2.5 text-left font-medium">config</th>
              <th className="px-3 py-2.5 text-left font-medium">origin</th>
              <th className="px-3 py-2.5 text-left font-medium">framework</th>
              <th className="px-3 py-2.5 text-left font-medium">version</th>
              <th className="px-3 py-2.5 text-left font-medium">sources</th>
              <th className="px-3 py-2.5 text-left font-medium">used by</th>
              <th className="px-3 py-2.5 text-right font-medium">actions</th>
            </tr>
          </thead>
          <tbody>
            {pager.slice.map((c) => (
              <tr
                key={c.id}
                className="border-b border-border/60 hover:bg-secondary/40 transition-colors cursor-pointer"
                title={c.description}
                onClick={() => onOpenConfig(c.id)}
              >
                <td className="px-4 py-2.5">
                  <div className="flex items-center gap-2">
                    <FileJson className="h-3.5 w-3.5 text-primary/70 shrink-0" />
                    <button className="font-mono-hud text-[13px] text-left" onClick={(e) => { e.stopPropagation(); onOpenConfig(c.id); }}>{c.name}</button>
                    {c.status === 'update-available' && (
                      <span className="flex items-center gap-1 font-mono-hud text-[9px] text-[hsl(45_93%_60%)]">
                        <ArrowUpCircle className="h-3 w-3" /> update
                      </span>
                    )}
                    {c.status === 'building' && <span className="font-mono-hud text-[9px] text-primary animate-pulse">building…</span>}
                  </div>
                </td>
                <td className="px-3 py-2.5">
                  <span
                    className="rounded border px-1.5 py-0.5 font-mono-hud text-[9px] uppercase tracking-wider"
                    style={{ color: `hsl(${ORIGIN_STYLE[c.origin]})`, borderColor: `hsl(${ORIGIN_STYLE[c.origin]} / 0.4)` }}
                  >
                    {c.origin}
                  </span>
                </td>
                <td className="px-3 py-2.5 font-mono-hud text-xs text-foreground/80">{c.framework}</td>
                <td className="px-3 py-2.5 font-mono-hud text-xs text-muted-foreground">v{c.version}</td>
                <td className="px-3 py-2.5 font-mono-hud text-[10px] text-muted-foreground">
                  {c.sources ?? '—'}{c.category ? ` · ${c.category}` : ''}
                </td>
                <td className="px-3 py-2.5 font-mono-hud text-[11px] text-muted-foreground">
                  {c.usedIn.length ? c.usedIn.join(', ') : '—'}
                </td>
                <td className="px-3 py-2.5" onClick={(e) => e.stopPropagation()}>
                  <div className="flex items-center justify-end gap-1">
                    {c.remote ? (
                      <Button size="sm" variant="ghost" className="h-7 px-2 font-mono-hud text-[10px] uppercase tracking-wider text-primary"
                        onClick={() => onFetchOfficial(c.framework)}>
                        <CloudDownload className="mr-1 h-3 w-3" /> fetch
                      </Button>
                    ) : (
                      <Button size="sm" variant="ghost" className="h-7 px-2 font-mono-hud text-[10px] uppercase tracking-wider"
                        onClick={() => c.path && onBuild(c.path, c.framework)}>
                        build
                      </Button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={7} className="px-4 py-10 text-center font-mono-hud text-xs text-muted-foreground">
                  ∅ no configs match — clear the filter, run a project scan, or fetch a source
                </td>
              </tr>
            )}
          </tbody>
        </table></div>
        <Pager page={pager.page} pageCount={pager.pageCount} pageSize={pager.pageSize} total={pager.total} onPage={pager.setPage} onPageSize={pager.setPageSize} />
      </Panel>

      {/* generate with AI dialog */}
      <Dialog open={generateOpen} onOpenChange={setGenerateOpen}>
        <DialogContent className="!fixed hud-panel border-border sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="font-mono-hud text-sm uppercase tracking-[0.2em] text-primary">// Generate with AI</DialogTitle>
            <DialogDescription className="text-xs text-muted-foreground">
              Draft a new unified config from a docs URL, a framework name, or a local project directory. Runs as a background job and
              lands in this library when it finishes.
            </DialogDescription>
          </DialogHeader>
          <GenerateConfigForm onGenerated={() => setGenerateOpen(false)} />
        </DialogContent>
      </Dialog>

      {/* add source dialog */}
      <Dialog open={addOpen} onOpenChange={setAddOpen}>
        <DialogContent className="!fixed hud-panel border-border sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="font-mono-hud text-sm uppercase tracking-[0.2em] text-primary">// Add config source</DialogTitle>
            <DialogDescription className="text-xs text-muted-foreground">
              Register a git repo as a config remote — official registry or your own. Configs are fetched, validated, and merged into the library.
            </DialogDescription>
          </DialogHeader>
          <div className="py-2">
            <Input value={repo} onChange={(e) => setRepo(e.target.value)} placeholder="github.com/you/presets" className="font-mono-hud text-sm bg-secondary/50" />
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setAddOpen(false)} className="font-mono-hud text-xs">Cancel</Button>
            <Button
              disabled={pending || !repo.trim()}
              onClick={async () => {
                if (await onAddSource(repo.trim())) { setAddOpen(false); setRepo(''); }
              }}
              className="font-mono-hud text-xs uppercase tracking-wider"
            >
              register + fetch
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
