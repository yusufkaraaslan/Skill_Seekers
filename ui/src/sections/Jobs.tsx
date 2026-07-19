import { Panel, SectionHeader, StatusPill } from '@/components/hud';
import type { Job } from '@/lib/data';
import { Terminal } from 'lucide-react';
import { cn } from '@/lib/utils';

const TYPE_COLOR: Record<string, string> = {
  create: '187 92% 50%',
  scan: '258 90% 66%',
  package: '152 60% 45%',
  enhance: '45 93% 55%',
  port: '199 89% 55%',
  fetch: '258 90% 66%',
  publish: '330 70% 60%',
  install: '152 60% 45%',
};

export default function Jobs({ jobs }: { jobs: Job[] }) {
  return (
    <div className="space-y-4 animate-flicker">
      <SectionHeader
        title="Jobs"
        sub="create · scan · package · enhance · port — live worker output"
        right={
          <span className="font-mono-hud text-[10px] uppercase tracking-widest text-muted-foreground">
            {jobs.filter((j) => j.status === 'running').length} running · {jobs.length} total
          </span>
        }
      />

      <div className="space-y-3">
        {jobs.length === 0 && (
          <Panel corners={false} className="p-10 text-center">
            <Terminal className="mx-auto h-8 w-8 text-muted-foreground/40 mb-3" />
            <p className="font-mono-hud text-xs text-muted-foreground">
              no jobs yet — create a skill, scan a project, or port to a CLI to see live worker output
            </p>
          </Panel>
        )}
        {jobs.map((j) => (
          <Panel key={j.id} corners={false} className="p-4">
            <div className="flex items-center gap-3 flex-wrap">
              <span
                className="rounded border px-1.5 py-0.5 font-mono-hud text-[10px] uppercase tracking-wider"
                style={{
                  color: `hsl(${TYPE_COLOR[j.type] ?? '217 12% 55%'})`,
                  borderColor: `hsl(${TYPE_COLOR[j.type] ?? '217 12% 55%'} / 0.4)`,
                  background: `hsl(${TYPE_COLOR[j.type] ?? '217 12% 55%'} / 0.08)`,
                }}
              >
                {j.type}
              </span>
              <span className="font-mono-hud text-sm font-semibold">{j.label}</span>
              <span className="font-mono-hud text-[11px] text-muted-foreground truncate">{j.detail}</span>
              <div className="ml-auto flex items-center gap-3">
                <span className="font-mono-hud text-[10px] text-muted-foreground">{j.startedAt}</span>
                <StatusPill status={j.status} />
              </div>
            </div>

            {(j.status === 'running' || j.status === 'queued') && (
              <div className="mt-3 h-1.5 rounded-full bg-secondary overflow-hidden">
                <div
                  className={cn('h-full transition-all duration-700', j.status === 'running' ? 'bg-primary' : 'bg-muted-foreground/40')}
                  style={{ width: `${j.progress}%`, boxShadow: j.status === 'running' ? '0 0 10px hsl(187 92% 50% / 0.7)' : 'none' }}
                />
              </div>
            )}

            <div className="mt-3 rounded border border-border bg-black/50 px-3 py-2">
              <div className="flex items-center gap-1.5 text-muted-foreground mb-1">
                <Terminal className="h-3 w-3" />
                <span className="font-mono-hud text-[9px] uppercase tracking-widest">worker log</span>
              </div>
              <div className="font-mono-hud text-[11px] leading-relaxed space-y-0.5 max-h-28 overflow-y-auto">
                {j.log.map((line, i) => (
                  <div
                    key={i}
                    className={cn(
                      line.includes('✗') ? 'text-destructive' : line.includes('✓') ? 'text-[hsl(152_60%_50%)]' : 'text-foreground/60',
                      i === j.log.length - 1 && j.status === 'running' && 'text-primary'
                    )}
                  >
                    {line}
                    {i === j.log.length - 1 && j.status === 'running' && <span className="animate-pulse"> ▌</span>}
                  </div>
                ))}
              </div>
            </div>
          </Panel>
        ))}
      </div>
    </div>
  );
}
