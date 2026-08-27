import { useState } from 'react';
import { Panel, SectionHeader } from '@/components/hud';
import type { ConfigEntry, ConfigSource, Workflow } from '@/lib/data';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import { GitBranch, Plus, RefreshCw, FileJson, ArrowUpCircle, Sparkles, Trash2, CloudDownload } from 'lucide-react';
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
  workflows,
  onAddSource,
  onFetchSource,
  onFetchOfficial,
  onRemoveSource,
  onBuild,
}: {
  sources: ConfigSource[];
  entries: ConfigEntry[];
  workflows: Workflow[];
  onAddSource: (repo: string) => void;
  onFetchSource: (name: string) => void;
  onFetchOfficial: (name: string) => void;
  onRemoveSource: (name: string) => void;
  onBuild: (path: string, name: string) => void;
}) {
  const [activeSource, setActiveSource] = useState<string>('all');
  const [addOpen, setAddOpen] = useState(false);
  const [repo, setRepo] = useState('');

  const filtered = entries.filter((c) => activeSource === 'all' || c.source === activeSource);

  return (
    <div className="space-y-5 animate-flicker">
      <SectionHeader
        title="Scrape configs"
        sub="recipes Skill Seekers builds skills from — presets, scanned & custom, backed by git remotes"
        right={
          <Button size="sm" onClick={() => setAddOpen(true)} className="font-mono-hud text-xs uppercase tracking-wider">
            <Plus className="mr-1.5 h-3.5 w-3.5" /> add_config_source
          </Button>
        }
      />

      {/* remote sources */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
        {sources.length === 0 && (
          <Panel corners={false} className="p-6 col-span-3 text-center">
            <p className="font-mono-hud text-xs text-muted-foreground">
              no remote config sources — register a git repo of unified configs to sync presets across machines
            </p>
          </Panel>
        )}
        {sources.map((s) => (
          <Panel key={s.name} corners={false}
            className={cn('p-4 cursor-pointer transition-all group relative', activeSource === s.name && 'border-primary/60')}
            onClick={() => setActiveSource(activeSource === s.name ? 'all' : s.name)}
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
                    <Button size="sm" variant="ghost" className="h-6 px-2 font-mono-hud text-[10px]" title="fetch_config" onClick={() => onFetchSource(s.name)}>
                      <RefreshCw className="h-3 w-3" />
                    </Button>
                    <Button size="sm" variant="ghost" className="h-6 px-2 font-mono-hud text-[10px] opacity-0 group-hover:opacity-100" title="remove_config_source" onClick={() => onRemoveSource(s.name)}>
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
        <table className="w-full text-sm">
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
            {filtered.map((c) => (
              <tr key={c.id} className="border-b border-border/60 hover:bg-secondary/40 transition-colors" title={c.description}>
                <td className="px-4 py-2.5">
                  <div className="flex items-center gap-2">
                    <FileJson className="h-3.5 w-3.5 text-primary/70 shrink-0" />
                    <span className="font-mono-hud text-[13px]">{c.name}</span>
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
                <td className="px-3 py-2.5">
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
                  ∅ no configs found in the workspace configs/ directory — run a project scan or fetch a source
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </Panel>

      {/* enhancement workflows */}
      <Panel className="p-5">
        <SectionHeader title="Enhancement workflows" sub={`${workflows.length} YAML presets chained via --enhance-workflow (mirrors the 5 workflow MCP tools)`} />
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-2.5 max-h-[420px] overflow-y-auto pr-1">
          {workflows.map((w) => (
            <div key={w.id} className="flex items-start gap-3 rounded border border-border bg-secondary/30 p-3.5 hover:border-primary/30 transition-colors group">
              <Sparkles className="h-4 w-4 text-[hsl(45_93%_55%)] shrink-0 mt-0.5" />
              <div className="min-w-0">
                <div className="font-mono-hud text-xs font-semibold">{w.id}.yaml</div>
                <p className="mt-1 text-[11px] text-muted-foreground leading-relaxed line-clamp-2">{w.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </Panel>

      {/* add source dialog */}
      <Dialog open={addOpen} onOpenChange={setAddOpen}>
        <DialogContent className="!fixed hud-panel border-border sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="font-mono-hud text-sm uppercase tracking-[0.2em] text-primary">// add_config_source</DialogTitle>
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
              disabled={!repo.trim()}
              onClick={() => {
                onAddSource(repo.trim());
                setAddOpen(false); setRepo('');
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
