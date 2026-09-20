import { useEffect, useState } from 'react';
import { Panel, SectionHeader } from '@/components/hud';
import type { MarketSkill, Marketplace, Skill, Cli } from '@/lib/data';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import { Store, Plus, RefreshCw, Download, CheckCircle2, Star, Upload, Search, Trash2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Checkbox } from '@/components/ui/checkbox';
import { useStore } from '@/lib/store';

const TYPE_STYLE: Record<string, string> = {
  official:  '187 92% 50%',
  community: '258 90% 66%',
  private:   '45 93% 55%',
};

export default function Marketplace({
  markets,
  skills,
  localSkills,
  onAdd,
  onRemove,
  onInstall,
  onPublish,
  onRefresh,
  onSync,
  clis,
}: {
  markets: Marketplace[];
  skills: MarketSkill[];
  localSkills: Skill[];
  onAdd: (repo: string) => Promise<boolean>;
  onRemove: (name: string) => void;
  onInstall: (s: MarketSkill, targets: string[], replace: boolean) => Promise<boolean>;
  onPublish: (skillName: string, marketplace: string) => Promise<boolean>;
  onRefresh: () => void;
  onSync: () => Promise<boolean>;
  clis: Cli[];
}) {
  const { pending } = useStore();
  const [installItem, setInstallItem] = useState<MarketSkill | null>(null);
  const [installTargets, setInstallTargets] = useState<string[]>([]);
  const [replace, setReplace] = useState(false);
  const [activeMarket, setActiveMarket] = useState<string>('all');
  const [query, setQuery] = useState('');
  const [addOpen, setAddOpen] = useState(false);
  const [publishOpen, setPublishOpen] = useState(false);
  const [repo, setRepo] = useState('');
  const [pubSkill, setPubSkill] = useState('');
  const [pubMarket, setPubMarket] = useState('');

  useEffect(() => {
    onRefresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const filtered = skills.filter((s) => {
    if (activeMarket !== 'all' && s.market !== activeMarket) return false;
    if (query) return (s.name + s.desc + s.tags.join()).toLowerCase().includes(query.toLowerCase());
    return true;
  });

  return (
    <div className="space-y-5 animate-flicker">
      <SectionHeader
        title="Marketplace"
        sub="remote skill repositories — sync, install, publish (mirrors the 4 marketplace MCP tools)"
        right={
          <Button size="sm" onClick={() => setAddOpen(true)} className="font-mono-hud text-xs uppercase tracking-wider">
            <Plus className="mr-1.5 h-3.5 w-3.5" /> Add marketplace
          </Button>
        }
      />

      {/* registered marketplaces */}
      {markets.length === 0 && (
        <Panel className="p-8 text-center">
          <Store className="mx-auto h-8 w-8 text-muted-foreground/40 mb-3" />
          <p className="font-mono-hud text-xs text-muted-foreground">
            no marketplaces registered — add a git repo containing skills to browse + install
          </p>
        </Panel>
      )}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3">
        {markets.map((m) => (
          <div
            role="button"
            tabIndex={0}
            onKeyDown={e => { if (e.target === e.currentTarget && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); setActiveMarket(activeMarket === m.id ? "all" : m.id); } }}
            key={m.id}
            onClick={() => setActiveMarket(activeMarket === m.id ? 'all' : m.id)}
            className={cn(
              'hud-panel rounded-md p-4 text-left transition-all group relative',
              activeMarket === m.id && 'border-primary/60 shadow-[0_0_16px_hsl(187_92%_50%/0.1)]'
            )}
          >
            <div className="flex items-center gap-2.5">
              <Store className="h-4 w-4 shrink-0" style={{ color: `hsl(${TYPE_STYLE[m.type] ?? TYPE_STYLE.community})` }} />
              <span className="text-sm font-semibold truncate">{m.name}</span>
              <span
                className="ml-auto rounded border px-1.5 py-0.5 font-mono-hud text-[9px] uppercase tracking-wider shrink-0"
                style={{
                  color: `hsl(${TYPE_STYLE[m.type] ?? TYPE_STYLE.community})`,
                  borderColor: `hsl(${TYPE_STYLE[m.type] ?? TYPE_STYLE.community} / 0.4)`,
                }}
              >
                {m.type}
              </span>
            </div>
            <div className="mt-1.5 font-mono-hud text-[10px] text-muted-foreground truncate">{m.repo}</div>
            <div className="mt-3 flex items-center justify-between font-mono-hud text-[10px]">
              <span className="text-muted-foreground">{m.skills} skills · sync {m.lastSync}</span>
              <span className={m.connected ? 'text-[hsl(152_60%_50%)]' : 'text-muted-foreground'}>
                {m.connected ? '● connected' : '○ offline'}
              </span>
            </div>
            {m.error && <p role="alert" className="mt-2 text-xs text-destructive break-words">{m.error}</p>}
            <button
              aria-label={`Remove marketplace ${m.name}`}
              onClick={(e) => { e.stopPropagation(); if (window.confirm(`Remove marketplace ${m.name}? Cached files will remain.`)) onRemove(m.name); }}
              className="absolute bottom-1 right-1 text-muted-foreground hover:text-destructive"
            >
              <Trash2 className="h-3.5 w-3.5" />
            </button>
          </div>
        ))}
      </div>

      {/* browser */}
      <Panel corners={false} className="p-4">
        <div className="flex items-center gap-3 mb-4">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
            <Input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="search marketplace skills…" className="pl-8 h-8 font-mono-hud text-xs bg-secondary/50" />
          </div>
          <span className="font-mono-hud text-[10px] text-muted-foreground">{filtered.length} results {activeMarket !== 'all' && `· ${activeMarket}`}</span>
          <Button variant="ghost" size="sm" className="ml-auto font-mono-hud text-[10px] uppercase tracking-widest text-muted-foreground"
            disabled={pending} onClick={onSync}>
            <RefreshCw className="mr-1.5 h-3 w-3" /> sync all
          </Button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-2.5">
          {filtered.map((s) => (
            <div key={s.id} className="flex items-start gap-3 rounded border border-border bg-secondary/30 p-3.5 hover:border-primary/30 transition-colors">
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-mono-hud text-[13px] font-semibold">{s.name}</span>
                  <span className="font-mono-hud text-[10px] text-muted-foreground">by {s.author}</span>
                  {s.tags.map((t) => (
                    <span key={t} className="rounded border border-border px-1 py-px font-mono-hud text-[9px] text-muted-foreground">{t}</span>
                  ))}
                </div>
                <p className="mt-1 text-[11px] text-muted-foreground leading-relaxed">{s.desc}</p>
                <div className="mt-2 flex items-center gap-3 font-mono-hud text-[10px] text-muted-foreground">
                  <span className="flex items-center gap-1"><Download className="h-3 w-3" /> {s.installs.toLocaleString()}</span>
                  {s.stars > 0 && <span className="flex items-center gap-1"><Star className="h-3 w-3" /> {s.stars.toLocaleString()}</span>}
                  <span>upd {s.updated}</span>
                  <span className="text-primary/60">{s.kind}</span>
                </div>
              </div>
              {s.installed ? (
                <span className="flex items-center gap-1.5 font-mono-hud text-[10px] text-[hsl(152_60%_50%)] shrink-0 pt-1">
                  <CheckCircle2 className="h-3.5 w-3.5" /> installed
                </span>
              ) : (
                <Button size="sm" variant="outline" disabled={pending} onClick={() => { setInstallItem(s); setInstallTargets([]); setReplace(false); }} className="h-7 font-mono-hud text-[10px] uppercase tracking-widest shrink-0">
                  install
                </Button>
              )}
            </div>
          ))}
          {filtered.length === 0 && markets.length > 0 && (
            <div className="col-span-2 py-8 text-center font-mono-hud text-xs text-muted-foreground">
              ∅ no skills indexed — check the marketplace repo layout (SKILL.md dirs or config JSONs)
            </div>
          )}
        </div>
      </Panel>

      {/* publish strip */}
      <Panel className="p-4 flex items-center gap-4 flex-wrap">
        <Upload className="h-4 w-4 text-primary shrink-0" />
        <div className="min-w-0 flex-1">
          <div className="text-sm font-semibold">Publish skill</div>
          <div className="text-[11px] text-muted-foreground">Push any local skill to a registered marketplace repo — opens a PR with SKILL.md + bundle manifest.</div>
        </div>
        <Button
          variant="outline"
          size="sm"
          disabled={markets.length === 0 || localSkills.length === 0}
          className="font-mono-hud text-[10px] uppercase tracking-wider"
          onClick={() => {
            setPubSkill(localSkills[0]?.id ?? '');
            setPubMarket(markets[0]?.name ?? '');
            setPublishOpen(true);
          }}
        >
          publish a skill…
        </Button>
      </Panel>

      <Dialog open={!!installItem} onOpenChange={() => { if (!pending) setInstallItem(null); }}><DialogContent className="hud-panel"><DialogHeader><DialogTitle>Install {installItem?.name}</DialogTitle><DialogDescription>The item is copied to this workspace. Choose any additional CLI destinations explicitly.</DialogDescription></DialogHeader>
        {installItem?.kind === 'skill' && clis.map(cli => <label key={cli.id} className="flex items-center gap-2 text-sm"><Checkbox checked={installTargets.includes(cli.id)} onCheckedChange={v => setInstallTargets(t => v ? [...t, cli.id] : t.filter(x => x !== cli.id))} />{cli.name} · {cli.globalPath}</label>)}
        <label className="flex items-center gap-2 text-sm"><Checkbox checked={replace} onCheckedChange={v => setReplace(v === true)} />Replace existing CLI copies or config file</label>
        <p className="text-xs text-muted-foreground">Existing workspace skills are preserved. Archive or rename a conflicting skill before installing.</p>
        <DialogFooter><Button disabled={pending || !installItem} onClick={async () => { if (installItem && await onInstall(installItem, installTargets, replace)) setInstallItem(null); }}>Install</Button></DialogFooter>
      </DialogContent></Dialog>
      {/* add marketplace dialog */}
      <Dialog open={addOpen} onOpenChange={setAddOpen}>
        <DialogContent className="!fixed hud-panel border-border sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="font-mono-hud text-sm uppercase tracking-[0.2em] text-primary">// Add marketplace</DialogTitle>
            <DialogDescription className="text-xs text-muted-foreground">
              Register any git repo as a skill marketplace. Synchronization runs as a background job; watch Jobs for progress.
            </DialogDescription>
          </DialogHeader>
          <div className="py-2">
            <Input value={repo} onChange={(e) => setRepo(e.target.value)} placeholder="owner/repo or git url" className="font-mono-hud text-sm bg-secondary/50" />
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setAddOpen(false)} className="font-mono-hud text-xs">Cancel</Button>
            <Button
              disabled={pending || !repo.trim()}
              onClick={async () => {
                if (await onAdd(repo.trim())) { setAddOpen(false); setRepo(''); }
              }}
              className="font-mono-hud text-xs uppercase tracking-wider"
            >
              register
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* publish dialog */}
      <Dialog open={publishOpen} onOpenChange={setPublishOpen}>
        <DialogContent className="!fixed hud-panel border-border sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="font-mono-hud text-sm uppercase tracking-[0.2em] text-primary">// Publish skill</DialogTitle>
            <DialogDescription className="text-xs text-muted-foreground">
              Pick a local skill and target marketplace.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3 py-2">
            <label className="font-mono-hud text-[10px] uppercase tracking-widest text-muted-foreground">skill</label>
            <select
              aria-label="Skill to publish"
              value={pubSkill}
              onChange={(e) => setPubSkill(e.target.value)}
              className="w-full h-9 rounded border border-border bg-secondary/50 px-2 font-mono-hud text-xs"
            >
              {localSkills.map((s) => (
                <option key={s.id} value={s.id}>{s.name}</option>
              ))}
            </select>
            <label className="font-mono-hud text-[10px] uppercase tracking-widest text-muted-foreground">marketplace</label>
            <select
              aria-label="Destination marketplace"
              value={pubMarket}
              onChange={(e) => setPubMarket(e.target.value)}
              className="w-full h-9 rounded border border-border bg-secondary/50 px-2 font-mono-hud text-xs"
            >
              {markets.map((m) => (
                <option key={m.id} value={m.name}>{m.name}</option>
              ))}
            </select>
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setPublishOpen(false)} className="font-mono-hud text-xs">Cancel</Button>
            <Button
              disabled={pending || !pubSkill || !pubMarket}
              onClick={async () => {
                if (await onPublish(pubSkill, pubMarket)) setPublishOpen(false);
              }}
              className="font-mono-hud text-xs uppercase tracking-wider"
            >
              publish
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
