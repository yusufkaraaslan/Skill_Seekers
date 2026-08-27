import { Panel, SectionHeader, StatusPill, CliChip } from '@/components/hud';
import Radar from '@/components/Radar';
import { fmtSize, qualityColor } from '@/lib/data';
import type { Activity, Cli, Job, Skill } from '@/lib/data';
import { ArrowUpRight, ScanSearch, Plus, Package, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';

const ACT_ICON: Record<string, string> = {
  scan: '◎', create: '✚', move: '⇢', port: '⇄', delete: '✕', package: '▣', enhance: '✦',
};

export default function Overview({
  skills,
  jobs,
  clis,
  activity,
  onNavigate,
  onNewScan,
  onNewSkill,
}: {
  skills: Skill[];
  jobs: Job[];
  clis: Cli[];
  activity: Activity[];
  onNavigate: (v: string) => void;
  onNewScan: () => void;
  onNewSkill: () => void;
}) {
  const running = jobs.filter((j) => j.status === 'running');
  const totalSize = skills.reduce((a, s) => a + s.sizeKb, 0);
  const seekerCount = skills.filter((s) => s.origin === 'seeker').length;
  const pluginCount = skills.filter((s) => s.origin === 'plugin').length;
  const manualCount = skills.length - seekerCount - pluginCount;
  const avgQ = skills.length ? Math.round(skills.reduce((a, s) => a + s.quality, 0) / skills.length) : 0;
  const detected = clis.filter((c) => c.detected);

  const stats = [
    { label: 'Skills tracked', value: String(seekerCount), sub: `+${pluginCount} plugin · +${manualCount} manual`, accent: true },
    { label: 'CLIs detected', value: `${detected.length}/${clis.length}`, sub: detected.map((c) => c.id).join(' · ') || 'none' },
    { label: 'Skill footprint', value: fmtSize(totalSize), sub: 'across all installs' },
    { label: 'Avg quality', value: String(avgQ), sub: 'heuristic score' },
  ];

  const needsEnhance = skills.filter((s) => s.quality < 70).length;

  return (
    <div className="space-y-5 animate-flicker">
      {/* hero strip */}
      <div className="grid grid-cols-12 gap-5">
        <Panel className="col-span-12 lg:col-span-8 p-5 scanline overflow-hidden relative">
          <div className="absolute inset-0 bg-grid opacity-40 pointer-events-none" />
          <div className="relative flex items-center gap-8">
            <Radar size={190} blips={skills.length + 6} />
            <div className="flex-1 min-w-0">
              <div className="font-mono-hud text-[10px] uppercase tracking-[0.3em] text-primary/70 mb-1">
                // seeker hud · mission control
              </div>
              <h1 className="text-2xl font-bold tracking-tight">
                Every skill. Every CLI. <span className="text-primary text-glow-cyan">One scope.</span>
              </h1>
              <p className="mt-2 text-sm text-muted-foreground max-w-md">
                Scanning local machine + tracked projects. {skills.length} skills indexed across{' '}
                {detected.length} detected CLIs.
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                <Button size="sm" onClick={onNewScan} className="font-mono-hud text-xs uppercase tracking-wider">
                  <ScanSearch className="mr-1.5 h-3.5 w-3.5" /> Scan project
                </Button>
                <Button size="sm" variant="outline" onClick={onNewSkill} className="font-mono-hud text-xs uppercase tracking-wider">
                  <Plus className="mr-1.5 h-3.5 w-3.5" /> New skill
                </Button>
                <Button size="sm" variant="ghost" onClick={() => onNavigate('skills')} className="font-mono-hud text-xs uppercase tracking-wider text-muted-foreground">
                  Browse all <ArrowUpRight className="ml-1 h-3.5 w-3.5" />
                </Button>
              </div>
            </div>
          </div>
        </Panel>

        {/* pipeline mini */}
        <Panel className="col-span-12 lg:col-span-4 p-5">
          <SectionHeader title="Pipeline" sub="ingest → analyze → structure → enhance → export" />
          <div className="space-y-2.5 mt-4">
            {running.length === 0 && (
              <p className="text-xs text-muted-foreground font-mono-hud">idle — no active jobs</p>
            )}
            {running.map((j) => (
              <div key={j.id} className="rounded border border-border bg-secondary/40 p-2.5">
                <div className="flex items-center justify-between gap-2">
                  <span className="font-mono-hud text-xs truncate">{j.label}</span>
                  <StatusPill status={j.status} />
                </div>
                <div className="mt-2 h-1 rounded-full bg-secondary overflow-hidden">
                  <div
                    className="h-full bg-primary transition-all duration-500 shadow-[0_0_8px_hsl(187_92%_50%/0.7)]"
                    style={{ width: `${j.progress}%` }}
                  />
                </div>
                <div className="mt-1.5 font-mono-hud text-[10px] text-muted-foreground truncate">
                  {j.log[j.log.length - 1]}
                </div>
              </div>
            ))}
            <Button variant="ghost" size="sm" onClick={() => onNavigate('jobs')} className="w-full font-mono-hud text-[10px] uppercase tracking-widest text-muted-foreground">
              all jobs →
            </Button>
          </div>
        </Panel>
      </div>

      {/* stat strip */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((s) => (
          <Panel key={s.label} corners={false} className="p-4">
            <div className="font-mono-hud text-[10px] uppercase tracking-[0.2em] text-muted-foreground">{s.label}</div>
            <div className={`mt-1.5 font-mono-hud text-3xl font-bold ${s.accent ? 'text-primary text-glow-cyan' : ''}`}>
              {s.value}
            </div>
            <div className="mt-1 text-[11px] text-muted-foreground">{s.sub}</div>
          </Panel>
        ))}
      </div>

      <div className="grid grid-cols-12 gap-5">
        {/* CLI coverage matrix */}
        <Panel className="col-span-12 lg:col-span-5 p-5">
          <SectionHeader
            title="CLI coverage"
            sub="install footprint per agent"
            right={<Button variant="ghost" size="sm" onClick={() => onNavigate('settings')} className="font-mono-hud text-[10px] uppercase tracking-widest text-muted-foreground">manage →</Button>}
          />
          <div className="space-y-2">
            {detected.map((cli) => {
              const count = skills.filter((s) => s.installs.includes(cli.id)).length;
              const max = Math.max(...clis.map((c) => c.skillCount), 1);
              return (
                <div key={cli.id} className="flex items-center gap-3">
                  <CliChip id={cli.id} />
                  <div className="flex-1 h-[6px] rounded-full bg-secondary overflow-hidden">
                    <div
                      className="h-full rounded-full"
                      style={{
                        width: `${(count / Math.max(max, skills.length)) * 100}%`,
                        background: `hsl(${cli.color})`,
                        boxShadow: `0 0 6px hsl(${cli.color} / 0.6)`,
                      }}
                    />
                  </div>
                  <span className="font-mono-hud text-xs text-muted-foreground w-8 text-right">{count}</span>
                </div>
              );
            })}
          </div>
          <div className="mt-4 border-t border-border pt-3 flex items-center justify-between">
            <span className="font-mono-hud text-[10px] uppercase tracking-widest text-muted-foreground">quality distribution</span>
            <div className="flex gap-1">
              {skills.map((s) => (
                <span
                  key={s.id}
                  title={`${s.name}: ${s.quality}`}
                  className="inline-block w-[10px] rounded-[2px]"
                  style={{
                    height: `${8 + (s.quality / 100) * 18}px`,
                    background: `hsl(${qualityColor(s.quality)} / 0.7)`,
                  }}
                />
              ))}
            </div>
          </div>
        </Panel>

        {/* activity */}
        <Panel className="col-span-12 lg:col-span-7 p-5">
          <SectionHeader title="Recent ops" sub="last 24h across all targets" />
          <div className="space-y-1 max-h-[264px] overflow-y-auto pr-1">
            {activity.map((a) => (
              <div key={a.id} className="flex items-start gap-3 rounded px-2 py-1.5 hover:bg-secondary/40 transition-colors">
                <span className="font-mono-hud text-[10px] text-muted-foreground w-10 pt-0.5 shrink-0">{a.time}</span>
                <span className="w-5 text-center text-primary font-mono-hud text-xs pt-px shrink-0">{ACT_ICON[a.icon]}</span>
                <span className="text-xs text-foreground/85 leading-relaxed">{a.text}</span>
              </div>
            ))}
          </div>
        </Panel>
      </div>

      {/* quick actions */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { icon: ScanSearch, t: 'Scan a project', d: 'AI reads manifests → emits one config per framework', act: onNewScan },
          { icon: Plus, t: 'Create from source', d: 'Docs, GitHub, PDF, video — 18 source types', act: onNewSkill },
          { icon: Sparkles, t: 'Enhance queue', d: needsEnhance ? `${needsEnhance} skill(s) below quality 70` : 'all skills above quality 70', act: () => onNavigate('skills') },
          { icon: Package, t: 'Bulk export', d: 'Package one asset to 21 platform targets', act: () => onNavigate('create') },
        ].map((q) => (
          <button key={q.t} onClick={q.act} className="hud-panel hud-corners rounded-md p-4 text-left group hover:border-primary/40 transition-colors">
            <q.icon className="h-4 w-4 text-primary mb-2.5 group-hover:drop-shadow-[0_0_6px_hsl(187_92%_50%)]" />
            <div className="text-sm font-semibold">{q.t}</div>
            <div className="mt-1 text-[11px] text-muted-foreground leading-relaxed">{q.d}</div>
          </button>
        ))}
      </div>
    </div>
  );
}
