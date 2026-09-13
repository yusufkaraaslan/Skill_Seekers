// Shared "Generate a config with AI" form — used by ConfigPage's Generate tab
// and by Library's "Generate with AI" dialog (POST /api/configs/generate).
import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import { useStore } from '@/lib/store';
import { cn } from '@/lib/utils';
import { Sparkles } from 'lucide-react';

const GENERATE_KINDS: { id: 'url' | 'name' | 'dir'; label: string; placeholder: string }[] = [
  { id: 'url', label: 'Docs URL', placeholder: 'https://docs.example.com/' },
  { id: 'name', label: 'Framework name', placeholder: 'react' },
  { id: 'dir', label: 'Project directory', placeholder: './my-project' },
];

export function GenerateConfigForm({ onGenerated }: { onGenerated?: () => void }) {
  const store = useStore();
  const [kind, setKind] = useState<'url' | 'name' | 'dir'>('url');
  const [value, setValue] = useState('');
  const [probe, setProbe] = useState(true);
  const agents = store.settings?.capabilities.agents ?? [];
  const [agent, setAgent] = useState(String(store.settings?.defaults.default_agent ?? 'claude'));
  const active = GENERATE_KINDS.find((k) => k.id === kind) ?? GENERATE_KINDS[0];

  const submit = async () => {
    if (await store.generateConfig({ kind, value: value.trim(), probe_urls: probe })) {
      setValue('');
      onGenerated?.();
    }
  };

  return (
    <div className="space-y-3">
      <p className="text-xs text-muted-foreground">
        Writes a new unified config by inspecting a documentation site, resolving a framework name against the registry, or scanning a
        local project directory. Runs as a background job — check Jobs for progress.
      </p>
      <div className="flex flex-wrap gap-1.5">
        {GENERATE_KINDS.map((k) => (
          <button
            key={k.id}
            aria-pressed={kind === k.id}
            onClick={() => setKind(k.id)}
            className={cn(
              'rounded border px-2.5 py-1 font-mono-hud text-[11px] transition-colors',
              kind === k.id ? 'border-primary/50 bg-primary/10 text-primary' : 'border-border text-muted-foreground hover:text-foreground',
            )}
          >
            {k.label}
          </button>
        ))}
      </div>
      <div className="space-y-1">
        <div className="font-mono-hud text-[10px] uppercase tracking-[0.2em] text-muted-foreground">{active.label}</div>
        <Input
          aria-label={active.label}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder={active.placeholder}
          className="h-8 font-mono-hud text-xs"
        />
      </div>
      <div className="space-y-1">
        <div className="font-mono-hud text-[10px] uppercase tracking-[0.2em] text-muted-foreground">enhancement agent (display only)</div>
        <select
          aria-label="Enhancement agent"
          value={agent}
          onChange={(e) => setAgent(e.target.value)}
          className="h-8 w-full rounded border border-border bg-secondary/40 px-2 font-mono-hud text-xs outline-none focus:border-primary/50"
        >
          {agents.map((a) => <option key={a} value={a}>{a}</option>)}
        </select>
        <p className="text-[10px] text-muted-foreground">Config generation is not agent-driven — this only previews which agent later enhancement passes would use.</p>
      </div>
      <label className="flex items-center gap-2.5 font-mono-hud text-[11px] text-foreground/80 cursor-pointer select-none">
        <Checkbox checked={probe} onCheckedChange={(v) => setProbe(v === true)} />
        probe discovered URLs before writing the config
      </label>
      <Button
        className="w-full font-mono-hud text-[11px] uppercase tracking-wider"
        disabled={store.pending || !value.trim()}
        onClick={submit}
      >
        <Sparkles className="mr-1.5 h-3.5 w-3.5" /> Generate config
      </Button>
    </div>
  );
}
