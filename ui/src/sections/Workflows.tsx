import { SectionHeader } from '@/components/hud';
import { usePayload } from '@/hooks/use-payload';
import { api } from '@/lib/api';
import type { WorkflowRow } from '@/lib/api';

// Placeholder: the YAML editor, copy/validate/delete controls and the
// /workflows/:name selection land in Task 12.
export default function Workflows({ selected }: { selected: string | null }) {
  const { data, error } = usePayload<WorkflowRow[]>(() => api.workflows(), 'workflows');

  if (error) return <p role="alert" className="rounded border border-destructive p-3">{error}</p>;
  if (!data) return <p role="status">Loading workflows…</p>;

  return (
    <div className="space-y-5 animate-flicker">
      <SectionHeader
        title="Enhancement workflows"
        sub={`${data.length} preset(s) — bundled and your own${selected ? ` · ${selected}` : ''}`}
      />
    </div>
  );
}
