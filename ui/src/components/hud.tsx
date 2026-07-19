import type { ReactNode } from 'react';
import { cn } from '@/lib/utils';
import { cliById } from '@/lib/data';
import type { CliId } from '@/lib/data';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';

// ── Panel: HUD card with corner ticks ────────────────────────────────────────
export function Panel({
  children,
  className,
  corners = true,
  ...rest
}: {
  children: ReactNode;
  className?: string;
  corners?: boolean;
} & React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn('hud-panel rounded-md', corners && 'hud-corners', className)}
      {...rest}
    >
      {children}
    </div>
  );
}

// ── Section header ───────────────────────────────────────────────────────────
export function SectionHeader({
  title,
  sub,
  right,
}: {
  title: string;
  sub?: string;
  right?: ReactNode;
}) {
  return (
    <div className="flex items-end justify-between gap-4 mb-3">
      <div>
        <div className="flex items-center gap-2">
          <span className="inline-block h-3.5 w-[3px] bg-primary shadow-[0_0_8px_hsl(187_92%_50%/0.8)]" />
          <h2 className="font-mono-hud text-[13px] font-semibold uppercase tracking-[0.18em] text-foreground">
            {title}
          </h2>
        </div>
        {sub && <p className="mt-1 text-xs text-muted-foreground pl-[11px]">{sub}</p>}
      </div>
      {right}
    </div>
  );
}

// ── CLI chip ─────────────────────────────────────────────────────────────────
export function CliChip({
  id,
  size = 'md',
  dim = false,
}: {
  id: CliId;
  size?: 'sm' | 'md';
  dim?: boolean;
}) {
  const cli = cliById(id);
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <span
          className={cn(
            'inline-flex items-center justify-center rounded-[4px] border font-mono-hud font-semibold tracking-wider select-none',
            size === 'sm' ? 'h-[18px] px-1 text-[9px]' : 'h-[22px] px-1.5 text-[10px]',
            dim && 'opacity-30 saturate-0'
          )}
          style={{
            color: `hsl(${cli.color})`,
            borderColor: `hsl(${cli.color} / 0.4)`,
            background: `hsl(${cli.color} / 0.08)`,
            textShadow: dim ? 'none' : `0 0 8px hsl(${cli.color} / 0.5)`,
          }}
        >
          {cli.short}
        </span>
      </TooltipTrigger>
      <TooltipContent side="top" className="font-mono-hud text-xs">
        {cli.name} {cli.detected ? `· v${cli.version}` : '· not detected'}
      </TooltipContent>
    </Tooltip>
  );
}

// ── Install dots: which CLIs carry a skill ──────────────────────────────────
export const ALL_CLI_IDS: CliId[] = ['claude', 'kimi', 'cursor', 'windsurf', 'gemini', 'codex', 'opencode'];

export function InstallSet({ installs }: { installs: CliId[] }) {
  return (
    <div className="flex items-center gap-1">
      {ALL_CLI_IDS.map((id) => (
        <CliChip key={id} id={id} size="sm" dim={!installs.includes(id)} />
      ))}
    </div>
  );
}

// ── Scope tag ────────────────────────────────────────────────────────────────
export function ScopeTag({ scope, project }: { scope: 'global' | 'project'; project?: string }) {
  return scope === 'global' ? (
    <span className="inline-flex items-center gap-1 rounded-[4px] border border-primary/40 bg-primary/10 px-1.5 py-0.5 font-mono-hud text-[10px] uppercase tracking-wider text-primary">
      ◈ global
    </span>
  ) : (
    <span className="inline-flex items-center gap-1 rounded-[4px] border border-[hsl(45_93%_55%/0.4)] bg-[hsl(45_93%_55%/0.08)] px-1.5 py-0.5 font-mono-hud text-[10px] tracking-wider text-[hsl(45_93%_60%)]">
      ▣ {project ?? 'project'}
    </span>
  );
}

// ── Quality meter ────────────────────────────────────────────────────────────
export function QualityMeter({ q, showNum = true }: { q: number; showNum?: boolean }) {
  const color = q >= 85 ? '187 92% 50%' : q >= 70 ? '45 93% 55%' : '0 72% 55%';
  return (
    <div className="flex items-center gap-2">
      <div className="h-[3px] w-14 rounded-full bg-secondary overflow-hidden">
        <div
          className="h-full rounded-full transition-all"
          style={{ width: `${q}%`, background: `hsl(${color})`, boxShadow: `0 0 6px hsl(${color})` }}
        />
      </div>
      {showNum && (
        <span className="font-mono-hud text-[11px]" style={{ color: `hsl(${color})` }}>
          {q}
        </span>
      )}
    </div>
  );
}

// ── Status pill ──────────────────────────────────────────────────────────────
const STATUS_STYLE: Record<string, [string, string]> = {
  clean:         ['152 60% 45%', 'clean'],
  stale:         ['45 93% 55%', 'stale'],
  scanning:      ['187 92% 50%', 'scanning'],
  'new-configs': ['258 90% 66%', 'new configs'],
  running:       ['187 92% 50%', 'running'],
  queued:        ['217 12% 55%', 'queued'],
  done:          ['152 60% 45%', 'done'],
  failed:        ['0 72% 55%', 'failed'],
};

export function StatusPill({ status }: { status: string }) {
  const [color, label] = STATUS_STYLE[status] ?? ['217 12% 55%', status];
  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 font-mono-hud text-[10px] uppercase tracking-wider"
      style={{
        color: `hsl(${color})`,
        borderColor: `hsl(${color} / 0.35)`,
        background: `hsl(${color} / 0.08)`,
      }}
    >
      <span
        className={cn('status-dot inline-block h-[5px] w-[5px] rounded-full', status === 'scanning' || status === 'running' ? 'animate-pulse' : '')}
        style={{ background: `hsl(${color})`, color: `hsl(${color})` }}
      />
      {label}
    </span>
  );
}

// ── Kbd ──────────────────────────────────────────────────────────────────────
export function Kbd({ children }: { children: ReactNode }) {
  return (
    <kbd className="rounded border border-border bg-secondary px-1.5 py-0.5 font-mono-hud text-[10px] text-muted-foreground">
      {children}
    </kbd>
  );
}
