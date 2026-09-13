import { useState } from 'react';
import type { ReactNode } from 'react';
import { useNavigate } from 'react-router';
import { Panel, SectionHeader } from '@/components/hud';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import { usePayload } from '@/hooks/use-payload';
import { api } from '@/lib/api';
import type { AnalysisManifest, AnalyzeBody } from '@/lib/api';
import { useStore } from '@/lib/store';
import { cn } from '@/lib/utils';
import { Play } from 'lucide-react';

type TargetKind = AnalyzeBody['target']['kind'];
type Depth = AnalyzeBody['depth'];
type AiMode = AnalyzeBody['ai_mode'];

const TARGET_KINDS: { id: TargetKind; label: string }[] = [
  { id: 'dir', label: 'Directory' },
  { id: 'skill', label: 'Existing skill' },
  { id: 'repo', label: 'GitHub repo' },
];

const DEPTHS: { id: Depth; label: string; hint: string; estimate: string }[] = [
  { id: 'basic', label: 'basic', hint: '1–2 min · AST + surface patterns', estimate: '1–2 min' },
  { id: 'c3x', label: 'c3x', hint: '20–60 min · deep patterns, examples, AI guides', estimate: '20–60 min' },
];

const AI_MODES: AiMode[] = ['off', 'auto', 'api', 'local'];

// Tool ids match the backend exactly (routes/analyze.py:TOOLS).
const TOOLS: { id: string; label: string; hint: string }[] = [
  { id: 'patterns', label: 'Design patterns', hint: '10 GoF-style design patterns across 9 languages' },
  { id: 'tests', label: 'Test examples', hint: 'Real usage examples mined from the test suite' },
  { id: 'guides', label: 'How-to guides', hint: 'AI-authored guides — only runs when Test examples is also selected in this run' },
  { id: 'config', label: 'Config patterns', hint: 'Configuration option usage across the codebase' },
  { id: 'router', label: 'Architecture router', hint: 'Runs when the target is a skill with configs' },
  { id: 'quality', label: 'Quality check', hint: 'Documentation completeness and freshness score' },
];

// Approximate `create --analysis-only` flags per standard tool — for display
// only, the analyze job never shells out to `create`.
const SKIP_FLAGS: Record<string, string> = {
  patterns: '--skip-patterns',
  tests: '--skip-test-examples',
  guides: '--skip-how-to-guides',
  config: '--skip-config-patterns',
};

function slugFor(value: string): string {
  const base = value.trim().split(/[/\\]/).filter(Boolean).pop() ?? '';
  return base.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '') || '<target>';
}

export default function Analyze() {
  const store = useStore();
  const navigate = useNavigate();
  const { data, error, reload } = usePayload<AnalysisManifest[]>(() => api.recentAnalyses(), 'analyze');

  const [targetKind, setTargetKind] = useState<TargetKind>('dir');
  const [dirValue, setDirValue] = useState('');
  const [skillValue, setSkillValue] = useState('');
  const [repoValue, setRepoValue] = useState('');
  const [depth, setDepth] = useState<Depth>('basic');
  const [tools, setTools] = useState<string[]>([]);
  const [minConfidence, setMinConfidence] = useState('0.7');
  const [aiMode, setAiMode] = useState<AiMode>('off');
  const [attachTo, setAttachTo] = useState('');

  if (error) return <p role="alert" className="rounded border border-destructive p-3">{error}</p>;
  if (!data) return <p role="status">Loading analyses…</p>;

  const targetValue = targetKind === 'dir' ? dirValue : targetKind === 'skill' ? skillValue : repoValue;
  const toggleTool = (id: string) => setTools((t) => (t.includes(id) ? t.filter((x) => x !== id) : [...t, id]));
  // Canonical TOOLS order, not click order — keeps the submitted body and the
  // CLI preview deterministic regardless of which cards were checked first.
  const selectedTools = TOOLS.filter((t) => tools.includes(t.id)).map((t) => t.id);
  const depthMeta = DEPTHS.find((d) => d.id === depth)!;
  const slug = slugFor(targetValue);

  const cliCommand = [
    'skill-seekers create', targetValue.trim() || '<target>', '--analysis-only', '--depth', depth,
    ...(['patterns', 'tests', 'guides', 'config'].filter((id) => !tools.includes(id)).map((id) => SKIP_FLAGS[id])),
    ...(tools.includes('quality') ? ['--quality-check'] : []),
  ].join(' ');

  // The number input's min/max only constrain the spinner, not typed text —
  // a typed 2 must disable the run rather than reach the backend, which
  // rejects min_confidence outside 0–1 with a 400.
  const minConfidenceNumber = Number(minConfidence);
  const minConfidenceInvalid = minConfidence.trim() === '' || Number.isNaN(minConfidenceNumber) || minConfidenceNumber < 0 || minConfidenceNumber > 1;

  const runDisabled = store.pending || selectedTools.length === 0 || !targetValue.trim() || minConfidenceInvalid;

  const run = async () => {
    const body: AnalyzeBody = {
      target: { kind: targetKind, value: targetValue.trim() },
      tools: selectedTools,
      depth,
      min_confidence: Math.min(1, Math.max(0, Number(minConfidence) || 0)),
      ai_mode: aiMode,
      attach_to: attachTo || null,
    };
    if (await store.analyze(body)) reload();
  };

  return (
    <div className="space-y-5 animate-flicker">
      <SectionHeader
        title="Analyze a codebase"
        sub={`C3.x tools over a skill, directory or repo · ${data.length} past run(s)`}
      />

      <div className="grid grid-cols-12 gap-5">
        <div className="col-span-12 lg:col-span-8 space-y-4">
          {/* ── target + depth ── */}
          <Panel className="p-5 space-y-4">
            <div>
              <FL>target</FL>
              <div className="mt-1 flex rounded-md border border-border overflow-hidden">
                {TARGET_KINDS.map((k) => (
                  <button
                    key={k.id}
                    onClick={() => setTargetKind(k.id)}
                    className={cn(
                      'flex-1 py-1.5 font-mono-hud text-[10px] transition-colors',
                      targetKind === k.id ? 'bg-primary/15 text-primary' : 'text-muted-foreground hover:text-foreground',
                    )}
                  >
                    {k.label}
                  </button>
                ))}
              </div>
              <div className="mt-2">
                {targetKind === 'dir' && (
                  <Input
                    aria-label="local path"
                    value={dirValue}
                    onChange={(e) => setDirValue(e.target.value)}
                    placeholder="~/dev/my-project"
                    className="h-8 font-mono-hud text-xs bg-secondary/50"
                  />
                )}
                {targetKind === 'skill' && (
                  <select
                    aria-label="skill"
                    value={skillValue}
                    onChange={(e) => setSkillValue(e.target.value)}
                    className="h-8 w-full rounded border border-border bg-secondary/40 px-2 font-mono-hud text-xs outline-none focus:border-primary/50"
                  >
                    <option value="">select a skill…</option>
                    {store.skills.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
                  </select>
                )}
                {targetKind === 'repo' && (
                  <Input
                    aria-label="owner/repo"
                    value={repoValue}
                    onChange={(e) => setRepoValue(e.target.value)}
                    placeholder="facebook/react"
                    className="h-8 font-mono-hud text-xs bg-secondary/50"
                  />
                )}
              </div>
            </div>

            <div>
              <FL>depth</FL>
              <div className="mt-1 flex rounded-md border border-border overflow-hidden">
                {DEPTHS.map((d) => (
                  <button
                    key={d.id}
                    onClick={() => setDepth(d.id)}
                    className={cn(
                      'flex-1 py-1.5 font-mono-hud text-[10px] transition-colors',
                      depth === d.id ? 'bg-primary/15 text-primary' : 'text-muted-foreground hover:text-foreground',
                    )}
                  >
                    {d.label}
                  </button>
                ))}
              </div>
              <p className="mt-1 text-[11px] text-muted-foreground">{depthMeta.hint}</p>
            </div>
          </Panel>

          {/* ── tools + options ── */}
          <Panel className="p-5 space-y-4">
            <FL>tools</FL>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {TOOLS.map((t) => {
                const active = tools.includes(t.id);
                return (
                  <label
                    key={t.id}
                    className={cn(
                      'flex items-start gap-2.5 rounded border px-3 py-2.5 cursor-pointer transition-colors',
                      active ? 'border-primary/60 bg-primary/10' : 'border-border bg-secondary/30 hover:border-primary/30',
                    )}
                  >
                    <Checkbox aria-label={t.label} checked={active} onCheckedChange={() => toggleTool(t.id)} className="mt-0.5" />
                    <div className="min-w-0">
                      <div className="font-mono-hud text-xs font-semibold">{t.label}</div>
                      <p className="mt-0.5 text-[10px] text-muted-foreground leading-snug">{t.hint}</p>
                    </div>
                  </label>
                );
              })}
            </div>

            <div className="grid grid-cols-2 gap-x-6 gap-y-4 border-t border-border pt-4">
              <div>
                <FL>languages</FL>
                <Input
                  aria-label="Languages"
                  placeholder="all detected"
                  disabled
                  title="Language filtering is not exposed by the analyze API yet — every detected language is analyzed"
                  className="mt-1 h-8 font-mono-hud text-xs bg-secondary/30 text-muted-foreground"
                />
              </div>
              <div>
                <FL>min confidence</FL>
                <Input
                  aria-label="Minimum confidence"
                  type="number"
                  min={0}
                  max={1}
                  step={0.05}
                  value={minConfidence}
                  onChange={(e) => setMinConfidence(e.target.value)}
                  aria-invalid={minConfidenceInvalid}
                  className="mt-1 h-8 font-mono-hud text-xs bg-secondary/50"
                />
                {minConfidenceInvalid && <p className="mt-1 text-[10px] text-destructive">must be between 0 and 1</p>}
              </div>
              <div>
                <FL>AI enhancement</FL>
                <div className="mt-1 flex rounded-md border border-border overflow-hidden">
                  {AI_MODES.map((m) => (
                    <button
                      key={m}
                      onClick={() => setAiMode(m)}
                      className={cn(
                        'flex-1 py-1.5 font-mono-hud text-[10px] transition-colors',
                        aiMode === m ? 'bg-primary/15 text-primary' : 'text-muted-foreground hover:text-foreground',
                      )}
                    >
                      {m}
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <FL>attach results to</FL>
                <select
                  aria-label="Attach results to"
                  value={attachTo}
                  onChange={(e) => setAttachTo(e.target.value)}
                  className="mt-1 h-8 w-full rounded border border-border bg-secondary/40 px-2 font-mono-hud text-xs outline-none focus:border-primary/50"
                >
                  <option value="">(none)</option>
                  {store.skills.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
                </select>
              </div>
            </div>

            <div className="flex justify-end border-t border-border pt-4">
              <Button disabled={runDisabled} onClick={run} className="font-mono-hud text-xs uppercase tracking-wider">
                <Play className="mr-1.5 h-3.5 w-3.5" /> Run analysis
              </Button>
            </div>
          </Panel>

          {/* ── recent analyses ── */}
          <Panel corners={false} className="overflow-hidden">
            <div className="px-4 pt-3">
              <span className="font-mono-hud text-[10px] uppercase tracking-[0.2em] text-muted-foreground">recent analyses</span>
            </div>
            <div className="mt-2 overflow-x-auto" role="region" aria-label="Recent analyses table" tabIndex={0}>
              <table className="w-full min-w-[520px] text-sm">
                <thead>
                  <tr className="border-b border-border font-mono-hud text-[10px] uppercase tracking-[0.15em] text-muted-foreground">
                    <th className="px-3 py-2.5 text-left font-medium">slug</th>
                    <th className="px-3 py-2.5 text-left font-medium">tools</th>
                    <th className="px-3 py-2.5 text-left font-medium">started</th>
                    <th className="px-3 py-2.5 text-left font-medium">attached to</th>
                  </tr>
                </thead>
                <tbody>
                  {data.length === 0 && (
                    <tr><td colSpan={4} className="px-3 py-4 text-center text-xs text-muted-foreground">No analysis runs yet.</td></tr>
                  )}
                  {data.map((m) => (
                    <tr key={m.slug} className="border-b border-border/60">
                      <td className="px-3 py-2.5 font-mono-hud text-[11px]">{m.slug}</td>
                      <td className="px-3 py-2.5 text-[11px] text-muted-foreground">
                        {m.tools.join(', ') || '—'}
                        {m.skipped?.length ? <span className="ml-1 text-muted-foreground/70">(skipped: {m.skipped.join(', ')})</span> : null}
                      </td>
                      <td className="px-3 py-2.5 font-mono-hud text-[11px] text-muted-foreground">{m.startedAt}</td>
                      <td className="px-3 py-2.5 text-[11px]">
                        {m.attachedTo ? (
                          <button onClick={() => navigate(`/skills/${m.attachedTo}`)} className="text-primary hover:underline">
                            {m.attachedTo}
                          </button>
                        ) : <span className="text-muted-foreground">—</span>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Panel>
        </div>

        {/* ── right: job preview ── */}
        <Panel className="col-span-12 lg:col-span-4 h-fit p-5">
          <SectionHeader title="Job preview" sub="What will run and roughly how long it takes" />
          <div className="space-y-2 font-mono-hud text-[10px] text-muted-foreground">
            <SpecRow k="target" v={`${TARGET_KINDS.find((k) => k.id === targetKind)!.label}: ${targetValue.trim() || '—'}`} />
            <SpecRow k="tools" v={selectedTools.length ? selectedTools.join(', ') : '—'} />
            <SpecRow k="depth" v={depth} />
            <SpecRow k="estimated" v={depthMeta.estimate} />
            <SpecRow k="output" v={`output/_analysis/${slug}/`} />
          </div>
          <div className="mt-4">
            <div className="mb-1 font-mono-hud text-[10px] uppercase tracking-[0.2em] text-muted-foreground">equivalent CLI (approximate)</div>
            <pre className="overflow-auto whitespace-pre-wrap break-all rounded border border-border bg-black/30 p-3 font-mono-hud text-[11px]">{cliCommand}</pre>
          </div>
        </Panel>
      </div>
    </div>
  );
}

function FL({ children }: { children: ReactNode }) {
  return <label className="flex items-center gap-2 font-mono-hud text-[10px] uppercase tracking-widest text-muted-foreground">{children}</label>;
}

function SpecRow({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex items-baseline justify-between gap-3 border-b border-border/50 pb-1.5">
      <span className="shrink-0 uppercase tracking-widest">{k}</span>
      <span className="truncate text-foreground/80" title={v}>{v}</span>
    </div>
  );
}
