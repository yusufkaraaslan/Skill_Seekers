import { useState } from 'react';
import { Panel, SectionHeader, StatusPill, Pager } from '@/components/hud';
import type { Job } from '@/lib/data';
import { Button } from '@/components/ui/button';
import { usePagination } from '@/hooks/use-pagination';
import { useStore } from '@/lib/store';
import { toast } from 'sonner';

export default function Jobs({ jobs, onCancel, onRetry }: {
  jobs: Job[];
  onCancel: (id: string) => Promise<boolean>;
  onRetry: (id: string) => Promise<boolean>;
}) {
  const { pending } = useStore();
  const [status, setStatus] = useState('all');
  const filtered = jobs.filter(j => status === 'all' || j.status === status);
  const pager = usePagination(filtered, 'jobs', status);
  const active = (j: Job) => ['running', 'queued', 'cancelling'].includes(j.status);
  return <div className="space-y-4">
    <SectionHeader title="Jobs" sub={`${jobs.filter(active).length} active · ${jobs.length} retained jobs — latest 100 finished plus active jobs`} />
    <select aria-label="Filter job status" value={status} onChange={e => setStatus(e.target.value)} className="rounded border bg-background p-2 text-sm">
      {['all', 'running', 'done', 'failed', 'cancelled'].map(s => <option key={s}>{s}</option>)}
    </select>
    {!filtered.length && <Panel className="p-6"><p>No matching jobs. Create a skill, scan a project, or install a skill to begin.</p></Panel>}
    {pager.slice.map(job => <Panel key={job.id} className="p-4 space-y-3">
      <div className="flex flex-wrap items-center gap-3"><span className="text-xs uppercase text-primary">{job.type}</span><strong className="break-all">{job.label}</strong><StatusPill status={job.status} /><time className="text-xs text-muted-foreground">{job.startedAt}</time>
        <div className="ml-auto flex gap-2">{active(job) ? <Button size="sm" variant="outline" disabled={pending || job.status === 'cancelling'} onClick={() => onCancel(job.id)}>Cancel</Button> : <Button size="sm" variant="outline" disabled={pending} onClick={() => onRetry(job.id)}>Retry</Button>}</div>
      </div>
      <p className="text-sm text-muted-foreground break-words">{job.detail}</p>
      {job.error && <p role="alert" className="text-sm text-destructive">{job.error}</p>}
      {active(job) && <progress aria-label={`${job.label} progress`} max={100} value={job.progress} className="w-full h-2" />}
      <details open={active(job) || job.status === 'failed'}><summary className="cursor-pointer text-sm">Worker log ({job.log.length} lines)</summary><pre className="mt-2 max-h-64 overflow-auto whitespace-pre-wrap break-words rounded border bg-black/30 p-3 text-xs">{job.log.join('\n')}</pre></details>
      {(job.artifacts ?? []).map((artifact, i) => <div key={artifact} className="flex flex-wrap gap-2 items-center text-sm"><span className="break-all flex-1">{artifact}</span><Button size="sm" variant="outline" onClick={() => navigator.clipboard.writeText(artifact).then(() => toast.success('Path copied')).catch(() => toast.error('Copy unavailable', { description: artifact }))}>Copy path</Button>{job.downloadableArtifacts?.includes(i) && <a className="underline text-primary" href={`/api/jobs/${job.id}/artifacts/${i}`} download>Download file</a>}</div>)}
    </Panel>)}
    <Pager page={pager.page} pageCount={pager.pageCount} pageSize={pager.pageSize} total={pager.total} onPage={pager.setPage} onPageSize={pager.setPageSize} />
  </div>;
}
