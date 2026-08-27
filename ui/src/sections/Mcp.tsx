import { useMemo, useState } from 'react';
import { Panel, SectionHeader } from '@/components/hud';
import { MCP_CATEGORY_COLOR } from '@/lib/data';
import type { McpTool } from '@/lib/data';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Plug, Search, TerminalSquare, Play } from 'lucide-react';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';

const CATEGORIES = Object.keys(MCP_CATEGORY_COLOR) as McpTool['category'][];

export default function Mcp({ tools }: { tools: McpTool[] }) {
  const [query, setQuery] = useState('');
  const [cat, setCat] = useState<string>('all');
  const [nl, setNl] = useState('');

  const filtered = useMemo(
    () =>
      tools.filter((t) => {
        if (cat !== 'all' && t.category !== cat) return false;
        if (query) return (t.name + t.desc + t.nl).toLowerCase().includes(query.toLowerCase());
        return true;
      }),
    [tools, query, cat]
  );

  const counts = CATEGORIES.map((c) => ({ c, n: tools.filter((t) => t.category === c).length }));

  const dispatch = () => {
    const match = tools.find((t) => nl.toLowerCase().includes(t.name.split('_')[0]));
    toast.success(`→ ${match?.name ?? 'install_skill'}`, {
      description: 'natural-language dispatch happens inside an MCP-connected agent — start one with: skill-seekers-mcp',
    });
    setNl('');
  };

  return (
    <div className="space-y-5 animate-flicker">
      <SectionHeader title="Seeker MCP" sub={`Skill Seekers' own MCP server — ${tools.length} tools it exposes to agents (stdio + HTTP)`} />

      {/* server status strip */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
        <Panel className="p-4 flex items-center gap-3">
          <Plug className="h-4 w-4 text-[hsl(152_60%_50%)] shrink-0" />
          <div>
            <div className="text-sm font-semibold">stdio transport</div>
            <div className="font-mono-hud text-[10px] text-muted-foreground">skill-seekers-mcp · claude code + cline</div>
          </div>
          <span className="ml-auto font-mono-hud text-[10px] text-[hsl(152_60%_50%)]">● live</span>
        </Panel>
        <Panel className="p-4 flex items-center gap-3">
          <Plug className="h-4 w-4 text-[hsl(152_60%_50%)] shrink-0" />
          <div>
            <div className="text-sm font-semibold">http transport</div>
            <div className="font-mono-hud text-[10px] text-muted-foreground">:8765 · cursor + windsurf</div>
          </div>
          <span className="ml-auto font-mono-hud text-[10px] text-[hsl(152_60%_50%)]">● live</span>
        </Panel>
        {/* natural language runner */}
        <Panel className="p-4">
          <div className="flex items-center gap-2 mb-2">
            <TerminalSquare className="h-4 w-4 text-primary" />
            <span className="font-mono-hud text-[10px] uppercase tracking-widest text-muted-foreground">natural language → tool</span>
          </div>
          <div className="flex gap-2">
            <Input
              value={nl}
              onChange={(e) => setNl(e.target.value)}
              placeholder='"Package output/react for Claude"'
              className="h-8 font-mono-hud text-xs bg-secondary/50"
              onKeyDown={(e) => {
                if (e.key === 'Enter' && nl.trim()) dispatch();
              }}
            />
            <Button size="sm" className="h-8 px-2.5" disabled={!nl.trim()} onClick={dispatch}>
              <Play className="h-3.5 w-3.5" />
            </Button>
          </div>
        </Panel>
      </div>

      {/* category filter */}
      <div className="flex flex-wrap gap-1.5">
        <button
          onClick={() => setCat('all')}
          className={cn(
            'rounded border px-2.5 py-1 font-mono-hud text-[10px] uppercase tracking-wider transition-colors',
            cat === 'all' ? 'border-primary/60 bg-primary/10 text-primary' : 'border-border text-muted-foreground hover:text-foreground'
          )}
        >
          all · {tools.length}
        </button>
        {counts.map(({ c, n }) => (
          <button
            key={c}
            onClick={() => setCat(cat === c ? 'all' : c)}
            className={cn(
              'rounded border px-2.5 py-1 font-mono-hud text-[10px] uppercase tracking-wider transition-colors',
              cat === c ? 'text-foreground' : 'text-muted-foreground hover:text-foreground'
            )}
            style={cat === c ? { borderColor: `hsl(${MCP_CATEGORY_COLOR[c]} / 0.6)`, background: `hsl(${MCP_CATEGORY_COLOR[c]} / 0.1)` } : { borderColor: 'hsl(var(--border))' }}
          >
            {c} · {n}
          </button>
        ))}
        <div className="relative ml-auto w-56">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
          <Input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="filter tools…" className="pl-8 h-8 font-mono-hud text-xs bg-secondary/50" />
        </div>
      </div>

      {/* tool grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-2.5">
        {filtered.map((t) => (
          <div key={t.name} className="hud-panel rounded-md p-3.5 hover:border-primary/30 transition-colors group">
            <div className="flex items-center gap-2">
              <span className="status-dot inline-block h-[6px] w-[6px] rounded-full shrink-0" style={{ background: `hsl(${MCP_CATEGORY_COLOR[t.category]})`, color: `hsl(${MCP_CATEGORY_COLOR[t.category]})` }} />
              <span className="font-mono-hud text-[13px] font-semibold">{t.name}</span>
              <span
                className="ml-auto rounded border px-1.5 py-px font-mono-hud text-[9px] uppercase tracking-wider shrink-0"
                style={{ color: `hsl(${MCP_CATEGORY_COLOR[t.category]})`, borderColor: `hsl(${MCP_CATEGORY_COLOR[t.category]} / 0.35)` }}
              >
                {t.category}
              </span>
            </div>
            <p className="mt-1.5 text-[11px] text-muted-foreground">{t.desc}</p>
            <div className="mt-2 rounded border border-border/60 bg-black/30 px-2 py-1 font-mono-hud text-[10px] text-foreground/60 group-hover:text-primary/80 transition-colors">
              “{t.nl}”
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
