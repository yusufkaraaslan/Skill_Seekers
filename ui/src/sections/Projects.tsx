import { useState } from 'react';
import { Panel, SectionHeader, StatusPill, InstallSet } from '@/components/hud';
import { fmtSize } from '@/lib/data';
import type { Project, Skill } from '@/lib/data';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { FolderGit2, FolderPlus, RefreshCw, ScanSearch, Loader2 } from 'lucide-react';

export default function Projects({
  projects,
  skills,
  onRescan,
  onAdd,
  onViewSkills,
}: {
  projects: Project[];
  skills: Skill[];
  onRescan: (id: string) => void;
  onAdd: (path: string) => void;
  onViewSkills: (pid: string) => void;
}) {
  const [addOpen, setAddOpen] = useState(false);
  const [path, setPath] = useState('');

  const projectSkills = (pid: string) => skills.filter((s) => s.projectId === pid);

  return (
    <div className="space-y-5 animate-flicker">
      <SectionHeader
        title="Projects"
        sub="tracked codebases — AI scan emits one config per detected framework"
        right={
          <Button size="sm" onClick={() => setAddOpen(true)} className="font-mono-hud text-xs uppercase tracking-wider">
            <FolderPlus className="mr-1.5 h-3.5 w-3.5" /> Add project
          </Button>
        }
      />

      {projects.length === 0 && (
        <Panel className="p-10 text-center">
          <FolderGit2 className="mx-auto h-8 w-8 text-muted-foreground/40 mb-3" />
          <p className="font-mono-hud text-xs text-muted-foreground">
            no projects tracked yet — add a local codebase to scan its frameworks into configs
          </p>
        </Panel>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        {projects.map((p) => (
          <ProjectCard
            key={p.id}
            project={p}
            skills={projectSkills(p.id)}
            scanning={p.status === 'scanning'}
            onRescan={() => onRescan(p.id)}
            onViewSkills={() => onViewSkills(p.id)}
          />
        ))}
      </div>

      <Dialog open={addOpen} onOpenChange={setAddOpen}>
        <DialogContent className="!fixed hud-panel border-border sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="font-mono-hud text-sm uppercase tracking-[0.2em] text-primary">// add project</DialogTitle>
            <DialogDescription className="text-xs text-muted-foreground">
              Point Seeker at a local path or git URL. First scan runs automatically.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3 py-2">
            <label className="font-mono-hud text-[10px] uppercase tracking-widest text-muted-foreground">path or git url</label>
            <Input
              value={path}
              onChange={(e) => setPath(e.target.value)}
              placeholder="~/dev/my-project  ·  github.com/user/repo"
              className="font-mono-hud text-sm bg-secondary/50"
            />
            <div className="rounded border border-dashed border-border p-3 text-[11px] text-muted-foreground leading-relaxed">
              Scan reads package.json, requirements.txt, Dockerfile, CI config + sampled imports — then writes{' '}
              <span className="text-primary font-mono-hud">configs/scanned/*.json</span> with pinned versions.
            </div>
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setAddOpen(false)} className="font-mono-hud text-xs">Cancel</Button>
            <Button
              disabled={!path.trim()}
              onClick={() => {
                setAddOpen(false);
                onAdd(path.trim());
                setPath('');
              }}
              className="font-mono-hud text-xs uppercase tracking-wider"
            >
              <ScanSearch className="mr-1.5 h-3.5 w-3.5" /> Add + scan
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function ProjectCard({
  project: p,
  skills,
  scanning,
  onRescan,
  onViewSkills,
}: {
  project: Project;
  skills: Skill[];
  scanning: boolean;
  onRescan: () => void;
  onViewSkills: () => void;
}) {
  const totalKb = skills.reduce((a, s) => a + s.sizeKb, 0);

  return (
    <Panel className="p-5 relative overflow-hidden">
      {scanning && (
        <div className="absolute left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-primary to-transparent animate-scan-bar pointer-events-none" />
      )}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3 min-w-0">
          <div className="flex h-9 w-9 items-center justify-center rounded border border-border bg-secondary/60 shrink-0">
            <FolderGit2 className="h-4 w-4 text-primary" />
          </div>
          <div className="min-w-0">
            <div className="font-semibold truncate">{p.name}</div>
            <div className="font-mono-hud text-[11px] text-muted-foreground truncate">{p.path}</div>
          </div>
        </div>
        <StatusPill status={scanning ? 'scanning' : p.status} />
      </div>

      {/* frameworks */}
      <div className="mt-4 flex flex-wrap gap-1.5">
        {(p.frameworks ?? []).map((f) => (
          <span key={f.name} className="rounded border border-border bg-secondary/50 px-2 py-0.5 font-mono-hud text-[10px] text-foreground/80">
            {f.name}<span className="text-primary/80">@{f.version}</span>
          </span>
        ))}
        {(p.frameworks ?? []).length === 0 && (
          <span className="font-mono-hud text-[10px] text-muted-foreground">detecting…</span>
        )}
      </div>

      {/* skills in project */}
      <div className="mt-4 border-t border-border pt-3 space-y-1.5">
        {skills.length === 0 && (
          <div className="font-mono-hud text-[11px] text-muted-foreground py-1">no project skills yet — run a scan to generate configs</div>
        )}
        {skills.map((s) => (
          <div key={s.id} className="flex items-center gap-2.5 text-xs group">
            <span className="text-primary/70 font-mono-hud">▸</span>
            <span className="font-mono-hud truncate">{s.name}</span>
            <span className="text-muted-foreground font-mono-hud text-[10px]">v{s.version}</span>
            <div className="ml-auto flex items-center gap-2">
              <InstallSet installs={s.installs} />
            </div>
          </div>
        ))}
      </div>

      <div className="mt-4 flex items-center justify-between border-t border-border pt-3">
        <div className="font-mono-hud text-[10px] text-muted-foreground space-x-3">
          <span>last scan <span className="text-foreground/70">{p.lastScan}</span></span>
          <span>skills <span className="text-foreground/70">{skills.length}</span></span>
          <span>size <span className="text-foreground/70">{totalKb ? fmtSize(totalKb) : '—'}</span></span>
        </div>
        <div className="flex items-center gap-1.5">
          <Button
            size="sm"
            variant="ghost"
            disabled={skills.length === 0}
            onClick={onViewSkills}
            className="font-mono-hud text-[10px] uppercase tracking-widest h-7 text-muted-foreground"
          >
            view skills →
          </Button>
          <Button
            size="sm"
            variant="outline"
            disabled={scanning}
            onClick={onRescan}
            className="font-mono-hud text-[10px] uppercase tracking-widest h-7"
          >
            {scanning ? <Loader2 className="mr-1 h-3 w-3 animate-spin" /> : <RefreshCw className="mr-1 h-3 w-3" />}
            {scanning ? 'scanning' : 'rescan'}
          </Button>
        </div>
      </div>
    </Panel>
  );
}
