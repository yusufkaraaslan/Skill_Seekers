// ── Seeker HUD · domain model + static metadata ─────────────────────────────
// Dynamic data (skills, jobs, projects, marketplaces, …) is fetched from the
// Skill Seekers backend (see lib/api.ts + lib/store.tsx). This module keeps
// the shared types and static lookup tables only.

export type CliId =
  | 'claude'
  | 'kimi'
  | 'cursor'
  | 'windsurf'
  | 'gemini'
  | 'codex'
  | 'opencode';

export interface Cli {
  id: CliId;
  name: string;
  short: string;
  color: string; // hsl string
  version: string;
  globalPath: string;
  detected: boolean;
  skillCount: number;
}

// Mutable — populated by the store from /api/overview (falls back to static
// defaults until the first fetch resolves).
export const CLIS: Cli[] = [
  { id: 'claude',   name: 'Claude Code', short: 'CLA', color: '24 85% 60%',  version: '—', globalPath: '~/.claude/skills',              detected: false, skillCount: 0 },
  { id: 'kimi',     name: 'Kimi CLI',    short: 'KIM', color: '258 90% 66%', version: '—', globalPath: '~/.kimi/skills',                detected: false, skillCount: 0 },
  { id: 'cursor',   name: 'Cursor',      short: 'CUR', color: '199 89% 55%', version: '—', globalPath: '~/.cursor/rules',               detected: false, skillCount: 0 },
  { id: 'windsurf', name: 'Windsurf',    short: 'WIN', color: '172 70% 45%', version: '—', globalPath: '~/.codeium/windsurf/memories',  detected: false, skillCount: 0 },
  { id: 'gemini',   name: 'Gemini CLI',  short: 'GEM', color: '217 89% 61%', version: '—', globalPath: '~/.gemini/skills',              detected: false, skillCount: 0 },
  { id: 'codex',    name: 'Codex CLI',   short: 'CDX', color: '152 60% 42%', version: '—', globalPath: '~/.codex/instructions',         detected: false, skillCount: 0 },
  { id: 'opencode', name: 'OpenCode',    short: 'OPC', color: '330 70% 60%', version: '—', globalPath: '~/.config/opencode/agent',      detected: false, skillCount: 0 },
];

export function setClis(clis: Cli[]): void {
  CLIS.splice(0, CLIS.length, ...clis);
}

export const cliById = (id: CliId): Cli =>
  CLIS.find((c) => c.id === id) ?? {
    id, name: id, short: id.slice(0, 3).toUpperCase(), color: '217 12% 52%',
    version: '—', globalPath: '', detected: false, skillCount: 0,
  };

// ── Skills ──────────────────────────────────────────────────────────────────

export type Scope = 'global' | 'project';

export interface SkillFile {
  path: string;
  size: string;
}

export interface Skill {
  id: string;
  name: string;
  description: string;
  scope: Scope;
  projectId?: string;
  installs: CliId[];           // which CLIs currently have this skill
  source: string;              // where it was built from
  sourceType: SourceType;
  version: string;
  sizeKb: number;
  updatedAt: string;
  quality: number;             // 0–100 heuristic score
  tags: string[];
  files: SkillFile[];
  content: string;             // SKILL.md body
  dir?: string;                // absolute path on disk (from backend)
}

export type SourceType =
  | 'docs' | 'github' | 'local' | 'pdf' | 'video'
  | 'notebook' | 'wiki' | 'openapi' | 'chat'
  | 'docx' | 'epub' | 'pptx' | 'asciidoc' | 'html'
  | 'rss' | 'manpage' | 'confluence' | 'notion' | 'config';

export const SOURCE_META: Record<SourceType, { label: string; icon: string }> = {
  docs:       { label: 'Docs site',   icon: '◎' },
  github:     { label: 'GitHub repo', icon: '◈' },
  local:      { label: 'Local code',  icon: '▣' },
  pdf:        { label: 'PDF',         icon: '▤' },
  video:      { label: 'Video',       icon: '▶' },
  notebook:   { label: 'Notebook',    icon: '◫' },
  wiki:       { label: 'Wiki',        icon: '❖' },
  openapi:    { label: 'OpenAPI',     icon: '⇄' },
  chat:       { label: 'Chat export', icon: '✦' },
  docx:       { label: 'Word',        icon: '▥' },
  epub:       { label: 'EPUB',        icon: '▦' },
  pptx:       { label: 'PowerPoint',  icon: '◧' },
  asciidoc:   { label: 'AsciiDoc',    icon: '◨' },
  html:       { label: 'HTML files',  icon: '◩' },
  rss:        { label: 'RSS / Atom',  icon: '≋' },
  manpage:    { label: 'Man page',    icon: '§' },
  confluence: { label: 'Confluence',  icon: '❖' },
  notion:     { label: 'Notion',      icon: '◪' },
  config:     { label: 'Config JSON', icon: '⚙' },
};

// ── Projects ────────────────────────────────────────────────────────────────

export interface Project {
  id: string;
  name: string;
  path: string;
  frameworks: { name: string; version: string }[];
  lastScan: string;
  status: 'clean' | 'stale' | 'scanning' | 'new-configs' | 'new';
  configsFound: number;
}

// ── Jobs ────────────────────────────────────────────────────────────────────

export type JobType = 'create' | 'scan' | 'package' | 'enhance' | 'port' | 'fetch' | 'publish' | 'install';
export type JobStatus = 'queued' | 'running' | 'done' | 'failed';

export interface Job {
  id: string;
  type: JobType;
  label: string;
  detail: string;
  progress: number; // 0–100
  status: JobStatus;
  startedAt: string;
  log: string[];
}

// ── Activity feed ───────────────────────────────────────────────────────────

export interface Activity {
  id: string;
  time: string;
  icon: 'scan' | 'create' | 'move' | 'port' | 'delete' | 'package' | 'enhance';
  text: string;
}

// ── Export targets (for the port/package UI) ────────────────────────────────

export const EXPORT_TARGETS = [
  { id: 'claude',     label: 'Claude Skill (.zip)',     group: 'skill' },
  { id: 'gemini',     label: 'Gemini Skill (.tar.gz)',  group: 'skill' },
  { id: 'openai',     label: 'OpenAI GPT (.zip)',       group: 'skill' },
  { id: 'kimi',       label: 'Kimi Skill (.zip)',       group: 'skill' },
  { id: 'cursor',     label: 'Cursor (.cursorrules)',   group: 'ide' },
  { id: 'windsurf',   label: 'Windsurf (.windsurfrules)', group: 'ide' },
  { id: 'cline',      label: 'Cline (.clinerules)',     group: 'ide' },
  { id: 'langchain',  label: 'LangChain Documents',     group: 'rag' },
  { id: 'llama-index',label: 'LlamaIndex TextNodes',    group: 'rag' },
  { id: 'pinecone',   label: 'Pinecone Markdown',       group: 'rag' },
  { id: 'chroma',     label: 'ChromaDB',                group: 'vector' },
  { id: 'qdrant',     label: 'Qdrant',                  group: 'vector' },
] as const;

export const fmtSize = (kb: number) =>
  kb >= 1024 ? `${(kb / 1024).toFixed(1)} MB` : `${kb} KB`;

export const qualityColor = (q: number) =>
  q >= 85 ? '187 92% 50%' : q >= 70 ? '45 93% 55%' : '0 72% 55%';

// ── Marketplace ─────────────────────────────────────────────────────────────

export interface Marketplace {
  id: string;
  name: string;
  repo: string;
  type: 'official' | 'community' | 'private';
  skills: number;
  lastSync: string;
  connected: boolean;
}

export interface MarketSkill {
  id: string;
  name: string;
  author: string;
  desc: string;
  market: string; // marketplace id
  installs: number;
  stars: number;
  updated: string;
  tags: string[];
  installed: boolean;
  path: string;   // absolute path inside the marketplace cache (backend)
  kind: 'skill' | 'config';
}

// ── Config library + remote sources ─────────────────────────────────────────

export interface ConfigSource {
  id: string;
  name: string;
  repo: string;
  kind: 'official' | 'custom';
  branch: string;
  configs: number;
  lastFetch: string;
  autoSync: boolean;
}

export interface ConfigEntry {
  id: string;
  name: string;
  framework: string;
  origin: 'preset' | 'scanned' | 'custom' | 'synced';
  source: string; // config source id or 'local' or 'official'
  version: string;
  pages: number;
  usedIn: string[]; // skill names built from it
  status: 'ready' | 'update-available' | 'building';
  path?: string;    // absolute path (backend)
  description?: string;
  sources?: string; // source types inside a unified config
  remote?: boolean; // lives only in the remote registry until fetched
  fetched?: boolean;
  category?: string;
}

// ── MCP tools ───────────────────────────────────────────────────────────────

export interface McpTool {
  name: string;
  desc: string;
  category: 'Core' | 'Extended' | 'Config Sources' | 'Splitting' | 'Publishing' | 'Marketplace' | 'Vector DB' | 'Workflows';
  nl: string; // natural-language trigger example
}

export const MCP_CATEGORY_COLOR: Record<McpTool['category'], string> = {
  'Core':           '187 92% 50%',
  'Extended':       '199 89% 55%',
  'Config Sources': '258 90% 66%',
  'Splitting':      '45 93% 55%',
  'Publishing':     '152 60% 45%',
  'Marketplace':    '330 70% 60%',
  'Vector DB':      '24 85% 60%',
  'Workflows':      '172 70% 45%',
};

// ── Enhancement workflows ───────────────────────────────────────────────────

export interface Workflow {
  id: string;
  desc: string;
}
