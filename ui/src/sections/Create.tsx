import { useMemo, useState } from 'react';
import { Panel, SectionHeader } from '@/components/hud';
import { EXPORT_TARGETS, SOURCE_META } from '@/lib/data';
import type { SourceType, Workflow } from '@/lib/data';
import type { CreateSpec } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import { Checkbox } from '@/components/ui/checkbox';
import { cn } from '@/lib/utils';
import { ArrowRight, ArrowLeft, Rocket, Plus, X, Layers, Globe, Github, FolderOpen, FileText, Play, Rss, BookOpen, Database, MessageSquare, FileCode, Settings2 } from 'lucide-react';

// all 18 source types with per-type input hints
const SOURCES: { type: SourceType; hint: string; example: string; icon: typeof Globe }[] = [
  { type: 'docs',       hint: 'Any docs site — llms.txt fast path',        example: 'https://docs.react.dev/',   icon: Globe },
  { type: 'github',     hint: 'AST, API extract, issues, changelog',       example: 'facebook/react',            icon: Github },
  { type: 'local',      hint: 'Local dir — code or HTML mirror',           example: './my-project',              icon: FolderOpen },
  { type: 'pdf',        hint: 'OCR, tables, encrypted PDFs',               example: 'manual.pdf',                icon: FileText },
  { type: 'video',      hint: 'YouTube/local — transcript + frame OCR',    example: 'youtube.com/watch?v=…',     icon: Play },
  { type: 'notebook',   hint: 'Jupyter .ipynb cells + outputs',            example: 'analysis.ipynb',            icon: FileCode },
  { type: 'openapi',    hint: 'OpenAPI/Swagger → endpoint skill',          example: 'openapi.yaml',              icon: Settings2 },
  { type: 'wiki',       hint: 'Generic wiki mirror',                       example: './wiki-export',             icon: BookOpen },
  { type: 'confluence', hint: 'Confluence spaces',                         example: '--space-key TEAM',          icon: Database },
  { type: 'notion',     hint: 'Notion pages + databases',                  example: '--database-id …',           icon: Database },
  { type: 'chat',       hint: 'Slack / Discord exports',                   example: './slack-export',            icon: MessageSquare },
  { type: 'docx',       hint: 'Word documents',                            example: 'report.docx',               icon: FileText },
  { type: 'epub',       hint: 'E-books',                                   example: 'book.epub',                 icon: BookOpen },
  { type: 'pptx',       hint: 'PowerPoint decks',                          example: 'slides.pptx',               icon: FileText },
  { type: 'asciidoc',   hint: '.adoc files or directories',                example: 'guide.adoc',                icon: FileText },
  { type: 'html',       hint: 'Local .html or HTML-dominant dirs',         example: './mirror_output/site/',     icon: FileCode },
  { type: 'rss',        hint: 'RSS / Atom feeds',                          example: 'feed.rss',                  icon: Rss },
  { type: 'manpage',    hint: 'Unix man pages',                            example: 'curl.1',                    icon: FileText },
];

interface SourceEntry {
  id: number;
  type: SourceType;
  input: string;
}

let entrySeq = 1;

export default function Create({ workflows: workflowPresets, onLaunch }: { workflows: Workflow[]; onLaunch: (spec: CreateSpec) => void }) {
  const [step, setStep] = useState(0);
  const [entries, setEntries] = useState<SourceEntry[]>([{ id: 0, type: 'docs', input: '' }]);
  const [name, setName] = useState('');
  const [desc, setDesc] = useState('');

  // flags (mirror real CLI)
  const [enhanceLevel, setEnhanceLevel] = useState(2);
  const [agent, setAgent] = useState('claude');
  const [preset, setPreset] = useState('standard');
  const [workflows, setWorkflows] = useState<string[]>([]);
  const [maxPages, setMaxPages] = useState('');
  const [rateLimit, setRateLimit] = useState('0.5');
  const [workers, setWorkers] = useState('1');
  const [asyncMode, setAsyncMode] = useState(false);
  const [chunkForRag, setChunkForRag] = useState(false);
  const [chunkTokens, setChunkTokens] = useState('512');
  const [chunkOverlap, setChunkOverlap] = useState('50');
  const [mergeMode, setMergeMode] = useState<'claude-enhanced' | 'rule-based'>('claude-enhanced');
  const [skipCodebase, setSkipCodebase] = useState(false);
  const [dryRun, setDryRun] = useState(false);
  const [fresh, setFresh] = useState(false);
  const [resume, setResume] = useState(false);
  const [targets, setTargets] = useState<string[]>(['claude']);
  const [localSkips, setLocalSkips] = useState<string[]>([]);

  const multi = entries.length > 1;
  const hasLocal = entries.some((e) => e.type === 'local');
  const hasWeb = entries.some((e) => ['docs', 'wiki', 'confluence', 'notion'].includes(e.type));

  const addEntry = (type: SourceType) => {
    // replace the single empty placeholder, otherwise append
    setEntries((es) => {
      if (es.length === 1 && !es[0].input && es[0].type === type) return es;
      if (es.length === 1 && !es[0].input) return [{ ...es[0], type }];
      return [...es, { id: entrySeq++, type, input: '' }];
    });
  };

  const removeEntry = (id: number) =>
    setEntries((es) => (es.length > 1 ? es.filter((e) => e.id !== id) : es));

  const setInput = (id: number, input: string) =>
    setEntries((es) => es.map((e) => (e.id === id ? { ...e, input } : e)));

  const toggleTarget = (id: string) =>
    setTargets((t) => (t.includes(id) ? t.filter((x) => x !== id) : [...t, id]));

  const toggleWorkflow = (id: string) =>
    setWorkflows((w) => (w.includes(id) ? w.filter((x) => x !== id) : [...w, id]));

  const toggleSkip = (flag: string) =>
    setLocalSkips((s) => (s.includes(flag) ? s.filter((x) => x !== flag) : [...s, flag]));

  const buildSpec = (): CreateSpec => ({
    entries: entries.map((e) => ({ type: e.type, input: e.input.trim() })).filter((e) => e.input),
    name: name.trim(),
    description: desc.trim(),
    targets,
    flags: {
      enhance_level: enhanceLevel,
      agent,
      preset,
      workflows,
      max_pages: maxPages,
      rate_limit: rateLimit,
      workers,
      async_mode: asyncMode,
      chunk_for_rag: chunkForRag,
      chunk_tokens: chunkTokens,
      chunk_overlap: chunkOverlap,
      merge_mode: mergeMode,
      skip_codebase: skipCodebase,
      dry_run: dryRun,
      fresh,
      resume,
      local_skips: localSkips,
    },
  });

  const launchDisabled =
    targets.length === 0 || entries.every((e) => !e.input.trim());

  // live equivalent CLI / unified config
  const cliPreview = useMemo(() => {
    const flagStr = [
      name && `--name ${name}`,
      `--enhance-level ${enhanceLevel}`,
      preset !== 'standard' && `--preset ${preset}`,
      agent !== 'claude' && `--agent ${agent}`,
      ...workflows.map((w) => `--enhance-workflow ${w}`),
      maxPages && `--max-pages ${maxPages}`,
      rateLimit !== '0.5' && `--rate-limit ${rateLimit}`,
      workers !== '1' && `--workers ${workers}`,
      asyncMode && '--async',
      chunkForRag && `--chunk-for-rag --chunk-tokens ${chunkTokens} --chunk-overlap-tokens ${chunkOverlap}`,
      multi && `--merge-mode ${mergeMode}`,
      skipCodebase && '--skip-codebase-analysis',
      dryRun && '--dry-run',
      fresh && '--fresh',
      resume && '--resume',
    ].filter(Boolean).join(' \\\n  ');

    if (multi) {
      const cfg = {
        name: name || 'my-skill',
        sources: entries.map((e) => ({
          type: e.type,
          ...(e.type === 'github' ? { repo: e.input || 'owner/repo' } : e.type === 'docs' ? { base_url: e.input || 'https://…' } : { path: e.input || '…' }),
        })),
      };
      return {
        head: `# unified multi-source → configs/${name || 'my-skill'}-unified.json`,
        json: JSON.stringify(cfg, null, 2),
        cmd: `skill-seekers create --config configs/${name || 'my-skill'}-unified.json \\\n  ${flagStr}`,
      };
    }
    const e = entries[0];
    const src = e.input || SOURCES.find((s) => s.type === e.type)!.example;
    return { head: '# equivalent CLI', json: null, cmd: `skill-seekers create ${src} \\\n  ${flagStr}` };
  }, [entries, name, enhanceLevel, preset, agent, workflows, maxPages, rateLimit, workers, asyncMode, chunkForRag, chunkTokens, chunkOverlap, multi, mergeMode, skipCodebase, dryRun, fresh, resume]);

  const STEPS = ['sources', 'options', 'export'];

  return (
    <div className="space-y-5 animate-flicker">
      <SectionHeader title="Create skill" sub="single or unified multi-source — one asset, every AI target" />

      {/* wizard step strip */}
      <Panel corners={false} className="px-5 py-4">
        <div className="flex items-center">
          {STEPS.map((p, i) => (
            <div key={p} className="flex items-center flex-1 last:flex-none">
              <div className="flex flex-col items-center gap-1.5">
                <div className={cn(
                  'flex h-7 w-7 items-center justify-center rounded-full border font-mono-hud text-[10px] transition-colors',
                  i <= step ? 'border-primary text-primary shadow-[0_0_10px_hsl(187_92%_50%/0.4)]' : 'border-border text-muted-foreground'
                )}>
                  {i + 1}
                </div>
                <span className={cn('font-mono-hud text-[9px] uppercase tracking-widest', i <= step ? 'text-primary' : 'text-muted-foreground')}>
                  {p}
                </span>
              </div>
              {i < STEPS.length - 1 && (
                <svg className="flex-1 h-4 mx-1" preserveAspectRatio="none" viewBox="0 0 100 4">
                  <line x1="0" y1="2" x2="100" y2="2" stroke={i < step ? 'hsl(187 92% 50% / 0.7)' : 'hsl(220 16% 18%)'} strokeWidth="1.5" strokeDasharray="5 5" className={i === step ? 'animate-dash' : ''} />
                </svg>
              )}
            </div>
          ))}
        </div>
      </Panel>

      <div className="grid grid-cols-12 gap-5">
        <Panel className="col-span-12 lg:col-span-8 p-5 min-h-[480px] flex flex-col">
          {/* ── STEP 0: sources (multi) ── */}
          {step === 0 && (
            <>
              <StepTitle n="01" t="Pick sources" s="click to add — combine multiple into one unified skill with conflict detection" />
              <div className="grid grid-cols-2 xl:grid-cols-3 gap-2 mt-4">
                {SOURCES.map((s) => {
                  const active = entries.some((e) => e.type === s.type);
                  return (
                    <button
                      key={s.type}
                      onClick={() => addEntry(s.type)}
                      className={cn(
                        'rounded border p-3 text-left transition-all',
                        active
                          ? 'border-primary/60 bg-primary/10'
                          : 'border-border bg-secondary/30 hover:border-primary/30'
                      )}
                    >
                      <div className="flex items-center gap-2">
                        <s.icon className={cn('h-3.5 w-3.5', active ? 'text-primary' : 'text-muted-foreground')} />
                        <span className="font-mono-hud text-[11px] font-semibold">{SOURCE_META[s.type].label}</span>
                        {active && <Plus className="ml-auto h-3 w-3 text-primary rotate-45" />}
                      </div>
                      <p className="mt-1 text-[10px] text-muted-foreground leading-snug">{s.hint}</p>
                    </button>
                  );
                })}
              </div>

              {/* merge list */}
              <div className="mt-4 space-y-2">
                {entries.map((e, idx) => {
                  const meta = SOURCES.find((s) => s.type === e.type)!;
                  return (
                    <div key={e.id} className="flex items-center gap-2 rounded border border-border bg-secondary/30 p-2 animate-flicker">
                      <span className="font-mono-hud text-[10px] text-primary/70 w-12 shrink-0">src_{idx + 1}</span>
                      <span className="rounded border border-primary/40 bg-primary/10 px-1.5 py-0.5 font-mono-hud text-[9px] uppercase tracking-wider text-primary shrink-0">
                        {SOURCE_META[e.type].label}
                      </span>
                      <Input
                        value={e.input}
                        onChange={(ev) => setInput(e.id, ev.target.value)}
                        placeholder={meta.example}
                        className="h-7 font-mono-hud text-xs bg-black/30 border-border/60"
                      />
                      {entries.length > 1 && (
                        <button onClick={() => removeEntry(e.id)} className="text-muted-foreground hover:text-destructive shrink-0">
                          <X className="h-3.5 w-3.5" />
                        </button>
                      )}
                    </div>
                  );
                })}
              </div>

              {multi && (
                <div className="mt-3 flex items-center gap-2 rounded border border-[hsl(258_90%_66%/0.4)] bg-[hsl(258_90%_66%/0.08)] px-3 py-2 animate-flicker">
                  <Layers className="h-3.5 w-3.5 text-[hsl(258_90%_66%)] shrink-0" />
                  <span className="font-mono-hud text-[11px] text-foreground/80">
                    unified mode — {entries.length} sources merge into one skill with docs-vs-code conflict detection
                  </span>
                </div>
              )}
            </>
          )}

          {/* ── STEP 1: options (real flags) ── */}
          {step === 1 && (
            <>
              <StepTitle n="02" t="Options" s="every flag from the CLI, grouped — preview updates live" />
              <div className="mt-4 grid grid-cols-2 gap-x-6 gap-y-4">
                <div>
                  <FL>skill name <Flag>--name</Flag></FL>
                  <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="auto-derived" className="mt-1 h-8 font-mono-hud text-xs bg-secondary/50" />
                </div>
                <div>
                  <FL>description <Flag>--description</Flag></FL>
                  <Input value={desc} onChange={(e) => setDesc(e.target.value)} placeholder="auto-generated" className="mt-1 h-8 font-mono-hud text-xs bg-secondary/50" />
                </div>
                <div>
                  <FL>enhancement <Flag>--enhance-level</Flag></FL>
                  <div className="mt-1 flex rounded-md border border-border overflow-hidden">
                    {['0 off', '1 skill.md', '2 +config', '3 full'].map((l, i) => (
                      <button key={i} onClick={() => setEnhanceLevel(i)}
                        className={cn('flex-1 py-1.5 font-mono-hud text-[10px] transition-colors', enhanceLevel === i ? 'bg-primary/15 text-primary' : 'text-muted-foreground hover:text-foreground')}>
                        {l}
                      </button>
                    ))}
                  </div>
                </div>
                <div>
                  <FL>analysis preset <Flag>--preset</Flag></FL>
                  <div className="mt-1 flex rounded-md border border-border overflow-hidden">
                    {['quick', 'standard', 'comprehensive'].map((p) => (
                      <button key={p} onClick={() => setPreset(p)}
                        className={cn('flex-1 py-1.5 font-mono-hud text-[10px] transition-colors', preset === p ? 'bg-primary/15 text-primary' : 'text-muted-foreground hover:text-foreground')}>
                        {p}
                      </button>
                    ))}
                  </div>
                </div>
                <div>
                  <FL>enhancement agent <Flag>--agent</Flag></FL>
                  <div className="mt-1 flex rounded-md border border-border overflow-hidden">
                    {['claude', 'kimi', 'codex', 'local'].map((a) => (
                      <button key={a} onClick={() => setAgent(a)}
                        className={cn('flex-1 py-1.5 font-mono-hud text-[10px] transition-colors', agent === a ? 'bg-primary/15 text-primary' : 'text-muted-foreground hover:text-foreground')}>
                        {a}
                      </button>
                    ))}
                  </div>
                </div>
                <div>
                  <FL>workflow presets <Flag>--enhance-workflow</Flag></FL>
                  <div className="mt-1 flex flex-wrap gap-1">
                    {workflowPresets.map((w) => (
                      <button key={w.id} onClick={() => toggleWorkflow(w.id)} title={w.desc}
                        className={cn('rounded border px-1.5 py-1 font-mono-hud text-[9px] transition-colors',
                          workflows.includes(w.id) ? 'border-[hsl(45_93%_55%/0.6)] bg-[hsl(45_93%_55%/0.1)] text-[hsl(45_93%_60%)]' : 'border-border text-muted-foreground hover:text-foreground')}>
                        {w.id}
                      </button>
                    ))}
                  </div>
                </div>

                {hasWeb && (
                  <>
                    <div>
                      <FL>max pages <Flag>--max-pages</Flag></FL>
                      <Input value={maxPages} onChange={(e) => setMaxPages(e.target.value)} placeholder="unlimited" className="mt-1 h-8 font-mono-hud text-xs bg-secondary/50" />
                    </div>
                    <div>
                      <FL>rate limit (s) <Flag>--rate-limit</Flag></FL>
                      <Input value={rateLimit} onChange={(e) => setRateLimit(e.target.value)} className="mt-1 h-8 font-mono-hud text-xs bg-secondary/50" />
                    </div>
                    <div>
                      <FL>workers <Flag>--workers</Flag></FL>
                      <Input value={workers} onChange={(e) => setWorkers(e.target.value)} placeholder="1–10" className="mt-1 h-8 font-mono-hud text-xs bg-secondary/50" />
                    </div>
                    <Toggle label="async mode" flag="--async" v={asyncMode} set={setAsyncMode} />
                  </>
                )}

                {multi && (
                  <>
                    <div className="col-span-2">
                      <FL>merge mode <Flag>--merge-mode</Flag></FL>
                      <div className="mt-1 flex rounded-md border border-border overflow-hidden">
                        {(['claude-enhanced', 'rule-based'] as const).map((m) => (
                          <button key={m} onClick={() => setMergeMode(m)}
                            className={cn('flex-1 py-1.5 font-mono-hud text-[10px] transition-colors', mergeMode === m ? 'bg-[hsl(258_90%_66%/0.15)] text-[hsl(258_90%_70%)]' : 'text-muted-foreground hover:text-foreground')}>
                            {m}
                          </button>
                        ))}
                      </div>
                    </div>
                    <Toggle label="skip codebase analysis for github sources" flag="--skip-codebase-analysis" v={skipCodebase} set={setSkipCodebase} />
                  </>
                )}

                {hasLocal && (
                  <div className="col-span-2 rounded border border-border p-3">
                    <FL>local analysis skips</FL>
                    <div className="mt-2 grid grid-cols-2 gap-1.5">
                      {['--skip-api-reference', '--skip-dependency-graph', '--skip-patterns', '--skip-test-examples', '--skip-how-to-guides', '--skip-docs'].map((f) => (
                        <label key={f} className="flex items-center gap-2 font-mono-hud text-[10px] text-muted-foreground hover:text-foreground cursor-pointer">
                          <Checkbox checked={localSkips.includes(f)} onCheckedChange={() => toggleSkip(f)} /> {f}
                        </label>
                      ))}
                    </div>
                  </div>
                )}

                <Toggle label="chunk for RAG" flag="--chunk-for-rag" v={chunkForRag} set={setChunkForRag} />
                {chunkForRag && (
                  <div className="flex gap-2">
                    <div className="flex-1">
                      <FL>tokens <Flag>--chunk-tokens</Flag></FL>
                      <Input value={chunkTokens} onChange={(e) => setChunkTokens(e.target.value)} className="mt-1 h-8 font-mono-hud text-xs bg-secondary/50" />
                    </div>
                    <div className="flex-1">
                      <FL>overlap <Flag>--chunk-overlap-tokens</Flag></FL>
                      <Input value={chunkOverlap} onChange={(e) => setChunkOverlap(e.target.value)} className="mt-1 h-8 font-mono-hud text-xs bg-secondary/50" />
                    </div>
                  </div>
                )}

                <Toggle label="dry run (preview only)" flag="--dry-run" v={dryRun} set={setDryRun} />
                <Toggle label="fresh (clear checkpoint)" flag="--fresh" v={fresh} set={setFresh} />
                <Toggle label="resume interrupted job" flag="--resume" v={resume} set={setResume} />
              </div>
            </>
          )}

          {/* ── STEP 2: targets ── */}
          {step === 2 && (
            <>
              <StepTitle n="03" t="Export targets" s="package the same asset everywhere — no re-scraping" />
              <div className="mt-4 grid grid-cols-2 gap-2">
                {EXPORT_TARGETS.map((t) => (
                  <label key={t.id}
                    className={cn('flex items-center gap-2.5 rounded border px-3 py-2.5 cursor-pointer transition-colors',
                      targets.includes(t.id) ? 'border-primary/60 bg-primary/10' : 'border-border bg-secondary/30 hover:border-primary/30')}>
                    <Checkbox checked={targets.includes(t.id)} onCheckedChange={() => toggleTarget(t.id)} />
                    <div>
                      <div className="font-mono-hud text-xs">{t.label}</div>
                      <div className="font-mono-hud text-[9px] uppercase tracking-widest text-muted-foreground">{t.group}</div>
                    </div>
                  </label>
                ))}
              </div>
            </>
          )}

          {/* nav */}
          <div className="mt-auto pt-6 flex items-center justify-between border-t border-border">
            <Button variant="ghost" disabled={step === 0} onClick={() => setStep(step - 1)} className="font-mono-hud text-xs uppercase tracking-wider">
              <ArrowLeft className="mr-1.5 h-3.5 w-3.5" /> back
            </Button>
            {step < 2 ? (
              <Button onClick={() => setStep(step + 1)} className="font-mono-hud text-xs uppercase tracking-wider">
                next <ArrowRight className="ml-1.5 h-3.5 w-3.5" />
              </Button>
            ) : (
              <Button
                disabled={launchDisabled}
                onClick={() => onLaunch(buildSpec())}
                className="font-mono-hud text-xs uppercase tracking-wider"
              >
                <Rocket className="mr-1.5 h-3.5 w-3.5" /> launch job
              </Button>
            )}
          </div>
        </Panel>

        {/* side: live CLI preview */}
        <Panel className="col-span-12 lg:col-span-4 p-5">
          <SectionHeader title="Command preview" sub="what the daemon will run" />
          <div className="rounded border border-border bg-black/40 p-4 font-mono-hud text-[11px] leading-relaxed overflow-x-auto">
            <div className="text-primary/70 whitespace-pre">{cliPreview.head}</div>
            {cliPreview.json && (
              <pre className="mt-2 text-[hsl(258_90%_75%)] whitespace-pre-wrap">{cliPreview.json}</pre>
            )}
            <div className="mt-2.5 text-foreground/85 whitespace-pre-wrap break-all">$ {cliPreview.cmd}</div>
            <div className="mt-3 pt-3 border-t border-border/60 text-foreground/70 whitespace-pre-wrap">
              $ skill-seekers package output/{name || 'skill'} \<br />
              &nbsp;&nbsp;--target {targets.join(' --target ') || '…'}
            </div>
          </div>
          <div className="mt-4 space-y-2 font-mono-hud text-[10px] text-muted-foreground">
            <SpecRow k="sources" v={`${entries.length} (${entries.map((e) => SOURCE_META[e.type].label).join(' + ')})`} />
            <SpecRow k="mode" v={multi ? `unified · ${mergeMode}` : 'single source'} />
            <SpecRow k="enhance" v={`level ${enhanceLevel} · ${agent}`} />
            <SpecRow k="workflows" v={workflows.length ? workflows.join(', ') : '—'} />
            <SpecRow k="targets" v={targets.length ? `${targets.length} selected` : '—'} />
          </div>
        </Panel>
      </div>
    </div>
  );
}

function StepTitle({ n, t, s }: { n: string; t: string; s: string }) {
  return (
    <div>
      <div className="font-mono-hud text-[10px] text-primary/70 tracking-[0.3em]">STEP {n}</div>
      <h3 className="mt-1 text-lg font-bold">{t}</h3>
      <p className="text-xs text-muted-foreground">{s}</p>
    </div>
  );
}

function FL({ children }: { children: React.ReactNode }) {
  return <label className="font-mono-hud text-[10px] uppercase tracking-widest text-muted-foreground flex items-center gap-2">{children}</label>;
}

function Flag({ children }: { children: React.ReactNode }) {
  return <span className="rounded bg-primary/10 px-1 py-px font-mono-hud text-[9px] normal-case tracking-normal text-primary/80">{children}</span>;
}

function Toggle({ label, flag, v, set }: { label: string; flag: string; v: boolean; set: (b: boolean) => void }) {
  return (
    <label className="flex items-center gap-2.5 font-mono-hud text-[11px] text-foreground/80 cursor-pointer select-none">
      <Switch checked={v} onCheckedChange={set} className="scale-90" />
      {label} <Flag>{flag}</Flag>
    </label>
  );
}

function SpecRow({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex items-baseline justify-between gap-3 border-b border-border/50 pb-1.5">
      <span className="uppercase tracking-widest shrink-0">{k}</span>
      <span className="text-foreground/80 truncate" title={v}>{v}</span>
    </div>
  );
}
