export interface Repo {
  id: number;
  name: string;
  local_path: string;
  git_url: string | null;
  source_type: string;
  clone_status: string | null;
  branch: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface DailyStat {
  date: string;
  commit_count: number;
  insertions: number;
  deletions: number;
  files_changed: number;
}

export interface WeeklyStat {
  week: string;
  commit_count: number;
  insertions: number;
  deletions: number;
  files_changed: number;
}

export interface AnalysisReport {
  repo_id: number;
  repo_name: string;
  total_commits: number;
  date_range: [string, string];
  daily_stats: DailyStat[];
  weekly_stats: WeeklyStat[];
  streak_current: number;
  streak_longest: number;
}

export interface TaskStatus {
  task_id: string;
  status: 'PENDING' | 'STARTED' | 'PROGRESS' | 'SUCCESS' | 'FAILURE';
  progress: number | null;
  result: Record<string, unknown> | null;
  error: string | null;
}

export interface RepoCreate {
  name: string;
  local_path?: string;
  git_url?: string;
  branch: string;
}

export interface FileModStat {
  extension: string;
  file_count: number;
  modification_count: number;
}

export interface KeywordStat {
  keyword: string;
  score: number;
}

export interface CommitFrequency {
  period: string;
  commit_count: number;
  insertions: number;
  deletions: number;
  files_changed: number;
}

export interface CollaborationNode {
  id: string;
  commit_count: number;
}

export interface CollaborationEdge {
  source: string;
  target: string;
  weight: number;
  shared_files: string[];
}

export interface CollaborationGraph {
  nodes: CollaborationNode[];
  edges: CollaborationEdge[];
}

export interface Violation {
  id: number;
  commit_hash: string;
  rule_name: string;
  severity: string;
  description: string | null;
  author: string | null;
  detected_at: string;
}

export interface ViolationSummary {
  total: number;
  by_rule: Record<string, number>;
  violations: Violation[];
}
