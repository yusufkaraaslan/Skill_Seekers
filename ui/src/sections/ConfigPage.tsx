import { SectionHeader } from '@/components/hud';
import { usePayload } from '@/hooks/use-payload';
import { api } from '@/lib/api';
import type { ConfigDetail } from '@/lib/api';

// Placeholder: the JSON editor, validation, estimate, split, push/submit and
// sync controls land in Task 11.
export default function ConfigPage({ id }: { id: string }) {
  const { data, error } = usePayload<ConfigDetail>(() => api.configDetail(id), id);

  if (error) return <p role="alert" className="rounded border border-destructive p-3">{error}</p>;
  if (!data) return <p role="status">Loading config…</p>;

  return (
    <div className="space-y-5 animate-flicker">
      <SectionHeader title={data.name} sub={`${data.framework} · ${data.origin} · v${data.version}`} />
    </div>
  );
}
