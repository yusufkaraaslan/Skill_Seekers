import { useCallback, useEffect, useMemo, useState } from 'react';
import { Panel, SectionHeader } from '@/components/hud';
import { MCP_CATEGORY_COLOR } from '@/lib/data';
import type { McpTool } from '@/lib/data';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Plug, Search, Copy, RefreshCw } from 'lucide-react';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';
import { api } from '@/lib/api';
import type { McpStatus } from '@/lib/api';

const CATEGORIES = Object.keys(MCP_CATEGORY_COLOR) as McpTool['category'][];

const STDIO_SNIPPET = JSON.stringify(
  { mcpServers: { 'skill-seekers': { command: 'python', args: ['-m', 'skill_seekers.mcp.server_fastmcp'] } } },
  null,
  2,
);
const httpSnippet = (url: string) =>
  JSON.stringify({ mcpServers: { 'skill-seekers': { url } } }, null, 2);

async function copyText(label: string, text: string) {
  try {
    await navigator.clipboard.writeText(text);
    toast.success(`${label} copied`);
  } catch {
    toast.error('clipboard unavailable', { description: text });
  }
}

function StatusCard({
  title,
  sub,
  hint,
  live,
  liveLabel,
  downLabel,
  onCopy,
}: {
  title: string;
  sub: string;
  hint: string;          // replaces `sub` while the transport is down: how to bring it up
  live: boolean | null;
  liveLabel: string;
  downLabel: string;
  onCopy: () => void;
}) {
  const color = live === null ? '217 12% 55%' : live ? '152 60% 50%' : '45 93% 55%';
  const label = live === null ? '… probing' : live ? `● ${liveLabel}` : `○ ${downLabel}`;
  return (
    <Panel className="p-4 flex items-center gap-3">
      <Plug className="h-4 w-4 shrink-0" style={{ color: `hsl(${color})` }} />
      <div className="min-w-0">
        <div className="text-sm font-semibold whitespace-nowrap">{title}</div>
        <div className="font-mono-hud text-[10px] text-muted-foreground truncate" title={live === false ? hint : sub}>
          {live === false ? hint : sub}
        </div>
      </div>
      <span className="ml-auto shrink-0 font-mono-hud text-[10px] whitespace-nowrap" style={{ color: `hsl(${color})` }}>{label}</span>
      <Button size="sm" variant="ghost" className="h-7 px-2" title="copy client config" aria-label={`Copy ${title} configuration`} onClick={onCopy}>
        <Copy className="h-3.5 w-3.5" />
      </Button>
    </Panel>
  );
}

export default function Mcp({ tools }: { tools: McpTool[] }) {
  const [query, setQuery] = useState('');
  const [cat, setCat] = useState<string>('all');
  const [probeError, setProbeError] = useState('');

  const [status, setStatus] = useState<McpStatus | null>(null);
  const fetchStatus = useCallback(
    () => api.mcpStatus().then(value => { setStatus(value); setProbeError(''); }).catch(error => { setStatus(null); setProbeError(String(error)); }),
    [],
  );
  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);
  const reprobe = () => {
    setStatus(null);
    fetchStatus();
  };

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


  return (
    <div className="space-y-5 animate-flicker">
      <SectionHeader
        title="Seeker MCP"
        sub={`Skill Seekers' own MCP server — ${tools.length} tools it exposes to agents (stdio + HTTP)`}
        right={
          <Button size="sm" variant="ghost" className="h-7 font-mono-hud text-[10px] uppercase tracking-wider" onClick={reprobe}>
            <RefreshCw className="mr-1.5 h-3 w-3" /> re-probe
          </Button>
        }
      />

      {probeError && <p role="alert" className="rounded border border-destructive p-3 text-sm">Status unavailable: {probeError}. Use Re-probe to retry.</p>}
      {/* server status strip */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
        <StatusCard
          title="stdio transport"
          sub={status?.stdio.command ?? 'python -m skill_seekers.mcp.server_fastmcp'}
          hint="pip install 'skill-seekers[mcp]'"
          live={probeError ? false : status ? status.stdio.state === 'installed' : null}
          liveLabel="installed"
          downLabel={probeError ? "unavailable" : "not installed"}
          onCopy={() => copyText('.mcp.json snippet', STDIO_SNIPPET)}
        />
        <StatusCard
          title="http transport"
          sub={status ? status.http.url : 'http://127.0.0.1:8000/sse'}
          hint="start: python -m skill_seekers.mcp.server_fastmcp --http"
          live={probeError ? false : status ? status.http.state === 'live' : null}
          liveLabel="live"
          downLabel={probeError ? "unavailable" : "not running"}
          onCopy={() => copyText('Cursor / Windsurf snippet', httpSnippet(status?.http.url ?? 'http://127.0.0.1:8000/sse'))}
        />
        <Panel className="p-4 space-y-2">
          <p className="font-semibold text-sm">Use tools in your connected agent</p>
          <p className="text-sm text-muted-foreground">Copy a client configuration, connect your agent to Seeker MCP, then ask it to use a tool below. This page provides connection help and examples.</p>
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
            <div className="flex flex-wrap items-center gap-2">
              <span className="status-dot inline-block h-[6px] w-[6px] rounded-full shrink-0" style={{ background: `hsl(${MCP_CATEGORY_COLOR[t.category]})`, color: `hsl(${MCP_CATEGORY_COLOR[t.category]})` }} />
              <span className="font-mono-hud text-[13px] font-semibold break-all">{t.name}</span>
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
