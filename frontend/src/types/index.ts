export interface RunRequest {
  task: string
  max_steps: number
  repo_dir: string | null
  test_cmd: string | null
  lint_cmd: string | null
}

export interface RunInfo {
  run_id: string
  status: 'running' | 'completed' | 'error' | 'idle'
  task: string
  created_at: string
  log_path?: string
}

export interface TranscriptEntry {
  timestamp: string
  type: string
  content: string | Record<string, unknown>
}

export interface WsMessage {
  type: 'stdout' | 'stderr' | 'info' | 'done' | 'error' | 'ping'
  data?: string | Record<string, unknown>
}

export interface LineItem {
  type: 'stdout' | 'stderr' | 'info' | 'success' | 'warning' | 'system'
  text: string
}
