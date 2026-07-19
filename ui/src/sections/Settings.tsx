import { useState } from 'react';
import { Panel, SectionHeader, CliChip } from '@/components/hud';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { RefreshCw, CheckCircle2, XCircle, KeyRound } from 'lucide-react';
import type { SettingsPayload } from '@/lib/api';

const KEY_TARGETS: Record<string, string> = {
  ANTHROPIC_API_KEY: 'Claude enhance + upload',
  GOOGLE_API_KEY: 'Gemini enhance + upload',
  OPENAI_API_KEY: 'GPT packaging',
  MOONSHOT_API_KEY: 'Kimi enhancement agent',
  MINIMAX_API_KEY: 'MiniMax enhancement agent',
  GITHUB_TOKEN: 'GitHub scraping rate limits',
};

export default function Settings({
  settings,
  onSetKey,
  onSetDefaults,
  onReprobe,
}: {
  settings: SettingsPayload | null;
  onSetKey: (name: string, value: string) => void;
  onSetDefaults: (s: Record<string, unknown>) => void;
  onReprobe: () => void;
}) {
  const [keyDrafts, setKeyDrafts] = useState<Record<string, string>>({});
  const clis = settings?.clis ?? [];
  const keys = settings?.keys ?? [];
  const defaults = (settings?.defaults ?? {}) as Record<string, unknown>;
  const [defaultAgent, setDefaultAgent] = useState<string | null>(null);
  const [outputDir, setOutputDir] = useState<string | null>(null);
  const [configsDir, setConfigsDir] = useState<string | null>(null);

  const agent = defaultAgent ?? String(defaults.default_agent ?? 'claude');
  const out = outputDir ?? String(defaults.output_dir ?? 'output');
  const cfg = configsDir ?? String(defaults.configs_dir ?? 'configs');

  const saveDefaults = () =>
    onSetDefaults({ default_agent: agent, output_dir: out, configs_dir: cfg });

  return (
    <div className="space-y-5 animate-flicker">
      <SectionHeader
        title="Environment"
        sub="detected CLIs, install paths, credentials"
        right={
          <Button size="sm" variant="outline" onClick={onReprobe} className="font-mono-hud text-xs uppercase tracking-wider">
            <RefreshCw className="mr-1.5 h-3.5 w-3.5" /> Reprobe
          </Button>
        }
      />

      {/* CLI detection grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        {clis.map((cli) => (
          <Panel key={cli.id} corners={false} className="p-4 flex items-center gap-4">
            <CliChip id={cli.id} />
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold">{cli.name}</span>
                {cli.detected ? (
                  <span className="flex items-center gap-1 font-mono-hud text-[10px] text-[hsl(152_60%_50%)]">
                    <CheckCircle2 className="h-3 w-3" /> v{cli.version}
                  </span>
                ) : (
                  <span className="flex items-center gap-1 font-mono-hud text-[10px] text-muted-foreground">
                    <XCircle className="h-3 w-3" /> not found
                  </span>
                )}
              </div>
              <div className="font-mono-hud text-[11px] text-muted-foreground truncate">{cli.globalPath}</div>
            </div>
            <div className="text-right shrink-0">
              <div className="font-mono-hud text-lg font-bold" style={{ color: cli.detected ? `hsl(${cli.color})` : 'hsl(217 12% 40%)' }}>
                {cli.skillCount}
              </div>
              <div className="font-mono-hud text-[9px] uppercase tracking-widest text-muted-foreground">skills</div>
            </div>
          </Panel>
        ))}
      </div>

      {/* API keys */}
      <Panel className="p-5">
        <SectionHeader title="Credentials" sub="stored via config manager — never written to configs" />
        <div className="space-y-2.5">
          {keys.map((k) => (
            <div key={k.name} className="flex items-center gap-3">
              <KeyRound className={`h-3.5 w-3.5 shrink-0 ${k.set ? 'text-[hsl(152_60%_50%)]' : 'text-muted-foreground'}`} />
              <span className="font-mono-hud text-xs w-44 shrink-0">{k.name}</span>
              <Input
                type="password"
                value={keyDrafts[k.name] ?? ''}
                onChange={(e) => setKeyDrafts((d) => ({ ...d, [k.name]: e.target.value }))}
                placeholder={k.set ? '•••••••• set — enter to replace' : 'not set'}
                className="font-mono-hud text-xs h-8 bg-secondary/50"
              />
              <Button
                size="sm"
                variant="outline"
                disabled={!keyDrafts[k.name]?.trim()}
                onClick={() => {
                  onSetKey(k.name, keyDrafts[k.name].trim());
                  setKeyDrafts((d) => ({ ...d, [k.name]: '' }));
                }}
                className="h-8 font-mono-hud text-[10px] uppercase tracking-wider shrink-0"
              >
                save
              </Button>
              <span className="font-mono-hud text-[10px] text-muted-foreground w-48 shrink-0 hidden xl:block">
                {KEY_TARGETS[k.name] ?? ''}
              </span>
            </div>
          ))}
        </div>
      </Panel>

      {/* defaults */}
      <Panel className="p-5">
        <SectionHeader title="Defaults" sub="applied to every new job unless overridden" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="font-mono-hud text-[10px] uppercase tracking-widest text-muted-foreground">enhancement agent</label>
            <Input value={agent} onChange={(e) => setDefaultAgent(e.target.value)} className="mt-1.5 font-mono-hud text-xs h-8 bg-secondary/50" />
          </div>
          <div>
            <label className="font-mono-hud text-[10px] uppercase tracking-widest text-muted-foreground">output directory</label>
            <Input value={out} onChange={(e) => setOutputDir(e.target.value)} className="mt-1.5 font-mono-hud text-xs h-8 bg-secondary/50" />
          </div>
          <div>
            <label className="font-mono-hud text-[10px] uppercase tracking-widest text-muted-foreground">configs directory</label>
            <Input value={cfg} onChange={(e) => setConfigsDir(e.target.value)} className="mt-1.5 font-mono-hud text-xs h-8 bg-secondary/50" />
          </div>
        </div>
        <div className="mt-4">
          <Button size="sm" onClick={saveDefaults} className="font-mono-hud text-xs uppercase tracking-wider">
            save defaults
          </Button>
        </div>
      </Panel>

      {/* workspace */}
      <Panel className="p-5">
        <SectionHeader title="Workspace" sub="server root — where output/ and configs/ live" />
        <div className="font-mono-hud text-xs text-foreground/80">{settings?.root ?? '…'}</div>
      </Panel>
    </div>
  );
}
