export interface Repo {
  id: number;
  name: string;
  local_path: string;
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
  local_path: string;
  branch: string;
}
