export type EvidenceRecord = {
  kind: string;
  subject: string;
  source_file: string;
  source_line: number | null;
  quote: string;
  confidence: number;
  freshness: string;
};

export type AtlasModule = {
  name: string;
  display_name: string;
  purpose: string;
  simple_description: string;
  confidence_label: string;
  safety_label: string;
  files: string[];
  tests: string[];
  confidence: number;
  freshness: string;
  reachability: string;
  evidence?: EvidenceRecord[];
};

export type ProjectCandidate = {
  name: string;
  path: string;
  description: string;
  looks_like_project: boolean;
};

export type ProjectListResponse = {
  home_root: string;
  projects: ProjectCandidate[];
};

export type ScanResponse = {
  repo: string;
  root_path: string;
  head_commit: string | null;
  file_count: number;
  modules: AtlasModule[];
};

export type PromptMode = 'diagnose_bug' | 'audit_quality' | 'cleanup_risk';

export type PromptBuildResponse = {
  prompt: string;
  markdown: string;
  mode: PromptMode;
  mode_label: string;
  trigger_label: string;
  destructive_actions_allowed: boolean;
};

export type PacketResponse = {
  markdown: string;
  destructive_actions_allowed: boolean;
  needs_full_smac: boolean;
};