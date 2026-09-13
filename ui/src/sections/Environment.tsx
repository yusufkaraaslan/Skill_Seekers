import { SectionHeader } from '@/components/hud';
import { usePayload } from '@/hooks/use-payload';
import { api } from '@/lib/api';
import type { EnvironmentPayload } from '@/lib/api';

// Placeholder: doctor checks, server start/stop, agent skill installation and
// the MCP client snippets (see lib/mcp-snippets.ts) land in Task 14.
export default function Environment() {
  const { data, error } = usePayload<EnvironmentPayload>(() => api.environment(), 'environment');

  if (error) return <p role="alert" className="rounded border border-destructive p-3">{error}</p>;
  if (!data) return <p role="status">Loading environment…</p>;

  return (
    <div className="space-y-5 animate-flicker">
      <SectionHeader
        title="Doctor"
        sub={`${data.doctor.checks.length} check(s) · last run ${data.doctor.ranAt}`}
      />
    </div>
  );
}
