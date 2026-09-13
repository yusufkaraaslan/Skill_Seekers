import { SectionHeader } from '@/components/hud';
import { usePayload } from '@/hooks/use-payload';
import { api } from '@/lib/api';
import type { AnalysisManifest } from '@/lib/api';

// Placeholder: target picker, tool selection, depth/AI mode and the run
// history land in Task 13.
export default function Analyze() {
  const { data, error } = usePayload<AnalysisManifest[]>(() => api.recentAnalyses(), 'analyze');

  if (error) return <p role="alert" className="rounded border border-destructive p-3">{error}</p>;
  if (!data) return <p role="status">Loading analyses…</p>;

  return (
    <div className="space-y-5 animate-flicker">
      <SectionHeader
        title="Analyze a codebase"
        sub={`C3.x tools over a skill, directory or repo · ${data.length} past run(s)`}
      />
    </div>
  );
}
