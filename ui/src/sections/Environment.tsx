import { useEffect, useMemo, useRef, useState } from 'react';
import { Panel, SectionHeader } from '@/components/hud';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { usePayload } from '@/hooks/use-payload';
import { api } from '@/lib/api';
import type { AgentRow, DoctorCheck, EnvironmentPayload, McpStatus, ServerRow } from '@/lib/api';
import { useStore } from '@/lib/store';
import { MCP_CATEGORY_COLOR } from '@/lib/data';
import type { McpTool } from '@/lib/data';
import { DEFAULT_HTTP_URL, DEFAULT_STDIO_COMMAND, STDIO_SNIPPET, httpSnippet } from '@/lib/mcp-snippets';
import { cn } from '@/lib/utils';
import { toast } from 'sonner';
import { Copy, RefreshCw, Search, Stethoscope } from 'lucide-react';

const CATEGORIES = Object.keys(MCP_CATEGORY_COLOR) as McpTool['category'][];

const LEVEL_META: Record<DoctorCheck['level'], { mark: string; color: string }> = {
  ok: { mark: '✓', color: '152 60% 50%' },
  warning: { mark: '!', color: '45 93% 55%' },
  error: { mark: '✗', color: '0 72% 55%' },
};

const DOCTOR_PILL_META: Record<'ok' | 'warning' | 'error', { color: string; label: string }> = {
  ok: { color: '152 60% 45%', label: 'all clear' },
  warning: { color: '45 93% 55%', label: 'warnings' },
  error: { color: '0 72% 55%', label: 'errors found' },
};

// mcp-stdio/http rows fold in the live `api.mcpStatus()` probe; embedding has
// no equivalent probe so it only ever shows the environment payload's state.
const SERVER_STATE_META: Record<string, { color: string; label: string }> = {
  running: { color: '152 60% 50%', label: 'running' },
  live: { color: '152 60% 50%', label: 'live' },
  installed: { color: '152 60% 50%', label: 'installed' },
  stopped: { color: '217 12% 55%', label: 'stopped' },
  missing: { color: '0 72% 55%', label: 'missing' },
  unavailable: { color: '0 72% 55%', label: 'unavailable' },
};

async function copyText(label: string, text: string) {
  try {
    await navigator.clipboard.writeText(text);
    toast.success(`${label} copied`);
  } catch {
    toast.error('clipboard unavailable', { description: text });
  }
}

export default function Environment() {
  const store = useStore();
  const { data, error, reload } = usePayload<EnvironmentPayload>(() => api.environment(), 'environment');
  // Probed independently of the environment payload: this can fail (server
  // down, network blip) even while /api/environment itself loads fine, and a
  // failure here should degrade the mcp-stdio/http rows, not the whole page.
  const { data: mcpStatus, error: mcpStatusError } = usePayload<McpStatus>(() => api.mcpStatus(), 'environment-mcp-status');

  const [doctorOverride, setDoctorOverride] = useState<EnvironmentPayload['doctor'] | null>(null);
  const [doctorPending, setDoctorPending] = useState(false);
  const [query, setQuery] = useState('');
  const [cat, setCat] = useState<string>('all');

  // `reload` is a fresh closure every render (usePayload doesn't memoize it) —
  // stash it in a ref so the poll effect below can stay mount-once instead of
  // tearing down and rebuilding its timer on every render.
  const reloadRef = useRef(reload);
  useEffect(() => { reloadRef.current = reload; });

  // A manually re-run doctor result is merged in directly (see runDoctor);
  // once the next full payload arrives, that becomes the source of truth again.
  useEffect(() => { setDoctorOverride(null); }, [data]);

  useEffect(() => {
    let stopped = false;
    let timer: ReturnType<typeof setTimeout>;
    const tick = () => {
      reloadRef.current();
      if (!stopped) timer = setTimeout(tick, 10000);
    };
    timer = setTimeout(tick, 10000);
    return () => { stopped = true; clearTimeout(timer); };
  }, []);

  const filteredTools = useMemo(
    () =>
      store.mcpTools.filter((t) => {
        if (cat !== 'all' && t.category !== cat) return false;
        if (query) return (t.name + t.desc + t.nl).toLowerCase().includes(query.toLowerCase());
        return true;
      }),
    [store.mcpTools, query, cat],
  );

  if (error) return <p role="alert" className="rounded border border-destructive p-3">{error}</p>;
  if (!data) return <p role="status">Loading environment…</p>;

  const doctor = doctorOverride ?? data.doctor;
  const pillLevel: 'ok' | 'warning' | 'error' = doctor.checks.some((c) => c.level === 'error')
    ? 'error'
    : doctor.checks.some((c) => c.level === 'warning')
      ? 'warning'
      : 'ok';
  const pillMeta = DOCTOR_PILL_META[pillLevel];

  const runDoctor = async () => {
    setDoctorPending(true);
    try {
      const result = await api.rerunDoctor();
      setDoctorOverride(result);
      toast.success('Doctor re-run');
    } catch (e) {
      toast.error('Doctor re-run failed', { description: e instanceof Error ? e.message : String(e) });
    } finally {
      setDoctorPending(false);
    }
  };

  // Marks only, not the `found` values — those already render in the checks
  // table and duplicating them here trips strict-mode text lookups in tests.
  const cliSummary = [
    'skill-seekers doctor',
    '',
    ...doctor.checks.map((c) => `${LEVEL_META[c.level].mark} ${c.name}`),
  ].join('\n');

  return (
    <div className="space-y-5 animate-flicker">
      <SectionHeader
        title="Doctor"
        sub={`${doctor.checks.length} check(s) · last run ${doctor.ranAt}`}
        right={
          <span
            className="inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 font-mono-hud text-[10px] uppercase tracking-wider"
            style={{ color: `hsl(${pillMeta.color})`, borderColor: `hsl(${pillMeta.color} / 0.35)`, background: `hsl(${pillMeta.color} / 0.08)` }}
          >
            <span className="status-dot inline-block h-[5px] w-[5px] rounded-full" style={{ background: `hsl(${pillMeta.color})`, color: `hsl(${pillMeta.color})` }} />
            {pillMeta.label}
          </span>
        }
      />

      <div className="grid grid-cols-12 gap-5">
        {/* ── left: doctor ── */}
        <div className="col-span-12 lg:col-span-6 space-y-4">
          <Panel className="p-5 space-y-3">
            <div className="flex items-center justify-between gap-3">
              <span className="font-mono-hud text-[10px] uppercase tracking-[0.2em] text-muted-foreground">diagnostic checks</span>
              <Button
                size="sm"
                variant="outline"
                disabled={doctorPending}
                onClick={runDoctor}
                className="font-mono-hud text-[11px] uppercase tracking-wider"
              >
                <Stethoscope className="mr-1.5 h-3.5 w-3.5" /> Run doctor
              </Button>
            </div>
            <div className="overflow-x-auto" role="region" aria-label="Doctor checks table" tabIndex={0}>
              <table className="w-full min-w-[420px] text-sm">
                <thead>
                  <tr className="border-b border-border font-mono-hud text-[10px] uppercase tracking-[0.15em] text-muted-foreground">
                    <th className="w-8 px-3 py-2.5 text-left font-medium" aria-label="status" />
                    <th className="px-3 py-2.5 text-left font-medium">check</th>
                    <th className="px-3 py-2.5 text-left font-medium">found</th>
                    <th className="px-3 py-2.5 text-right font-medium">fix</th>
                  </tr>
                </thead>
                <tbody>
                  {doctor.checks.map((c) => {
                    const meta = LEVEL_META[c.level];
                    return (
                      <tr key={c.name} className="border-b border-border/60 align-top">
                        <td className="px-3 py-2.5">
                          <span aria-hidden="true" style={{ color: `hsl(${meta.color})` }}>{meta.mark}</span>
                        </td>
                        <td className="px-3 py-2.5">
                          <div className="text-xs font-semibold">{c.name}</div>
                          {c.hint && <div className="mt-0.5 text-[11px] text-muted-foreground">{c.hint}</div>}
                        </td>
                        <td className="px-3 py-2.5 font-mono-hud text-[11px] text-muted-foreground">{c.found || '—'}</td>
                        <td className="px-3 py-2.5 text-right">
                          {c.fix && (
                            <Button
                              size="sm"
                              variant="ghost"
                              className="h-7 px-2 font-mono-hud text-[10px] uppercase tracking-wider"
                              onClick={() => copyText(`${c.name} fix`, c.fix)}
                            >
                              Fix
                            </Button>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </Panel>

          <Panel corners={false} className="p-4">
            <div className="mb-2 font-mono-hud text-[10px] uppercase tracking-[0.2em] text-muted-foreground">equivalent CLI</div>
            <pre className="overflow-auto whitespace-pre-wrap break-all rounded border border-border bg-black/30 p-3 font-mono-hud text-[11px]">{cliSummary}</pre>
          </Panel>
        </div>

        {/* ── right: servers, mcp tools, agents ── */}
        <div className="col-span-12 lg:col-span-6 space-y-4">
          {mcpStatusError && (
            <p role="alert" className="rounded border border-destructive p-3 text-sm text-destructive">
              MCP status probe failed: {mcpStatusError}
            </p>
          )}

          <Panel className="p-5 space-y-2.5">
            <span className="font-mono-hud text-[10px] uppercase tracking-[0.2em] text-muted-foreground">servers</span>
            <div className="space-y-2">
              {data.servers.map((row) => (
                <ServerRowView key={row.id} row={row} mcpStatus={mcpStatus} mcpDown={!!mcpStatusError} onReload={reload} />
              ))}
            </div>
          </Panel>

          <details className="hud-panel rounded-md p-4">
            <summary className="cursor-pointer font-mono-hud text-[11px] uppercase tracking-widest text-muted-foreground">
              MCP tools ({store.mcpTools.length})
            </summary>
            <div className="mt-3 space-y-3">
              {store.sectionErrors.mcp && (
                <div role="alert" className="flex flex-wrap items-center gap-2 rounded border border-destructive p-2 text-xs text-destructive">
                  <span className="min-w-0 break-words">{store.sectionErrors.mcp}</span>
                  <Button
                    size="sm"
                    variant="outline"
                    className="ml-auto h-7 font-mono-hud text-[10px] uppercase tracking-wider"
                    onClick={() => store.refreshMcp()}
                  >
                    <RefreshCw className="mr-1.5 h-3 w-3" /> Retry
                  </Button>
                </div>
              )}

              <div className="flex flex-wrap items-center gap-1.5">
                <CatButton active={cat === 'all'} onClick={() => setCat('all')} label={`all · ${store.mcpTools.length}`} color={null} />
                {CATEGORIES.map((c) => {
                  const n = store.mcpTools.filter((t) => t.category === c).length;
                  return (
                    <CatButton
                      key={c}
                      active={cat === c}
                      onClick={() => setCat(cat === c ? 'all' : c)}
                      label={`${c} · ${n}`}
                      color={MCP_CATEGORY_COLOR[c]}
                    />
                  );
                })}
                <div className="relative ml-auto w-48">
                  <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
                  <Input
                    aria-label="filter MCP tools"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="filter tools…"
                    className="pl-8 h-8 font-mono-hud text-xs bg-secondary/50"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {filteredTools.map((t) => (
                  <div key={t.name} className="rounded border border-border/60 bg-secondary/20 p-2.5">
                    <div className="flex items-center gap-2">
                      <span className="font-mono-hud text-[12px] font-semibold break-all">{t.name}</span>
                      <span
                        className="ml-auto shrink-0 rounded border px-1.5 py-px font-mono-hud text-[9px] uppercase tracking-wider"
                        style={{ color: `hsl(${MCP_CATEGORY_COLOR[t.category]})`, borderColor: `hsl(${MCP_CATEGORY_COLOR[t.category]} / 0.35)` }}
                      >
                        {t.category}
                      </span>
                    </div>
                    <p className="mt-1 text-[11px] text-muted-foreground">{t.desc}</p>
                  </div>
                ))}
                {filteredTools.length === 0 && <p className="text-xs text-muted-foreground">No tools match.</p>}
              </div>
            </div>
          </details>

          <Panel className="p-5 space-y-2.5">
            <span className="font-mono-hud text-[10px] uppercase tracking-[0.2em] text-muted-foreground">agents</span>
            <div className="space-y-2">
              {data.agents.map((agent) => (
                <AgentRowView key={agent.id} agent={agent} onReload={reload} />
              ))}
            </div>
          </Panel>
        </div>
      </div>
    </div>
  );
}

function ServerRowView({
  row,
  mcpStatus,
  mcpDown,
  onReload,
}: {
  row: ServerRow;
  mcpStatus: McpStatus | null;
  mcpDown: boolean;
  onReload: () => void;
}) {
  const store = useStore();
  const isMcp = row.id === 'mcp-stdio' || row.id === 'mcp-http';
  const state = isMcp && mcpDown ? 'unavailable' : row.state;
  const meta = SERVER_STATE_META[state] ?? SERVER_STATE_META.stopped;
  const address =
    row.id === 'mcp-stdio' ? mcpStatus?.stdio.command || row.address || DEFAULT_STDIO_COMMAND
    : row.id === 'mcp-http' ? mcpStatus?.http.url || row.address || DEFAULT_HTTP_URL
    : row.address;
  const running = row.state === 'running' || row.state === 'live';

  return (
    <Panel corners={false} className="p-3.5 flex items-center gap-3">
      <span
        className="status-dot inline-block h-[6px] w-[6px] shrink-0 rounded-full"
        style={{ background: `hsl(${meta.color})`, color: `hsl(${meta.color})` }}
      />
      <div className="min-w-0 flex-1">
        <div className="text-sm font-semibold">{row.name}</div>
        <div className="font-mono-hud text-[10px] text-muted-foreground truncate" title={address}>{address}</div>
      </div>
      <span className="font-mono-hud text-[10px] uppercase tracking-wider shrink-0" style={{ color: `hsl(${meta.color})` }}>{meta.label}</span>
      {row.id === 'mcp-stdio' && (
        <Button
          size="sm"
          variant="ghost"
          className="h-7 px-2"
          aria-label="Copy stdio client configuration"
          title="copy .mcp.json snippet"
          onClick={() => copyText('.mcp.json snippet', STDIO_SNIPPET)}
        >
          <Copy className="h-3.5 w-3.5" />
        </Button>
      )}
      {row.id === 'mcp-http' && (
        <Button
          size="sm"
          variant="ghost"
          className="h-7 px-2"
          aria-label="Copy HTTP client configuration"
          title="copy HTTP client snippet"
          onClick={() => copyText('HTTP client snippet', httpSnippet(address))}
        >
          <Copy className="h-3.5 w-3.5" />
        </Button>
      )}
      {(row.id === 'mcp-http' || row.id === 'embedding') && (
        <Button
          size="sm"
          disabled={store.pending}
          onClick={async () => {
            const ok = running ? await store.stopServer(row.id) : await store.startServer(row.id);
            if (ok) onReload();
          }}
        >
          {running ? `Stop ${row.name}` : `Start ${row.name}`}
        </Button>
      )}
    </Panel>
  );
}

function AgentRowView({ agent, onReload }: { agent: AgentRow; onReload: () => void }) {
  const store = useStore();
  return (
    <Panel corners={false} className="p-3.5 flex items-center gap-3">
      <AgentChip agent={agent} />
      <div className="min-w-0 flex-1">
        <div className="text-sm font-semibold">{agent.name}</div>
        <div className="font-mono-hud text-[10px] text-muted-foreground">
          {agent.detected ? `v${agent.version ?? '—'}` : 'not detected'} · {agent.skillInstalled ? 'skill installed' : 'not installed'}
        </div>
      </div>
      <Button
        size="sm"
        disabled={!agent.detected || store.pending}
        onClick={async () => {
          const ok = await store.installAgent(agent.id, { force: agent.skillInstalled });
          if (ok) onReload();
        }}
      >
        {agent.skillInstalled ? 'Reinstall' : `Install skill into ${agent.name}`}
      </Button>
    </Panel>
  );
}

function AgentChip({ agent }: { agent: AgentRow }) {
  return (
    <span
      className={cn(
        'inline-flex h-[22px] shrink-0 items-center justify-center rounded-[4px] border px-1.5 font-mono-hud text-[10px] font-semibold tracking-wider select-none',
        !agent.detected && 'opacity-30 saturate-0',
      )}
      style={{
        color: `hsl(${agent.color})`,
        borderColor: `hsl(${agent.color} / 0.4)`,
        background: `hsl(${agent.color} / 0.08)`,
      }}
    >
      {agent.short}
    </span>
  );
}

function CatButton({ active, onClick, label, color }: { active: boolean; onClick: () => void; label: string; color: string | null }) {
  return (
    <button
      onClick={onClick}
      className={cn(
        'rounded border px-2.5 py-1 font-mono-hud text-[10px] uppercase tracking-wider transition-colors',
        !color && active && 'border-primary/60 bg-primary/10 text-primary',
        !color && !active && 'border-border text-muted-foreground hover:text-foreground',
        color && active ? 'text-foreground' : color ? 'text-muted-foreground hover:text-foreground' : '',
      )}
      style={color ? (active ? { borderColor: `hsl(${color} / 0.6)`, background: `hsl(${color} / 0.1)` } : { borderColor: 'hsl(var(--border))' }) : undefined}
    >
      {label}
    </button>
  );
}
