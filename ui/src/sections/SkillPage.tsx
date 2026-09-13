import { SectionHeader } from '@/components/hud';
import { usePayload } from '@/hooks/use-payload';
import { api } from '@/lib/api';
import type { SkillDetail } from '@/lib/api';

// Placeholder: the tabs (Overview / SKILL.md editor / Installs / Jobs /
// Analysis) land in Task 10.
export default function SkillPage({ id }: { id: string }) {
  const { data, error } = usePayload<SkillDetail>(() => api.skillDetail(id), id);

  if (error) return <p role="alert" className="rounded border border-destructive p-3">{error}</p>;
  if (!data) return <p role="status">Loading skill…</p>;

  return (
    <div className="space-y-5 animate-flicker">
      <SectionHeader title={data.name} sub={data.description} />
    </div>
  );
}
