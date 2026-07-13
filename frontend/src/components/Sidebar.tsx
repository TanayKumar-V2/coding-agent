import type { RunInfo } from '../types'

interface SidebarProps {
  runs: RunInfo[]
  onSelectRun: (runId: string) => void
}

function formatTime(iso: string): string {
  try {
    const d = new Date(iso)
    return isNaN(d.getTime()) ? iso : d.toLocaleString()
  } catch {
    return iso
  }
}

function statusColor(status: string): string {
  switch (status) {
    case 'running':
      return 'bg-green text-green bg-green-glow/50'
    case 'completed':
      return 'bg-accent/20 text-accent'
    case 'error':
      return 'bg-red-500/20 text-red-400'
    default:
      return 'bg-gray-500/20 text-gray-400'
  }
}

export default function Sidebar({ runs, onSelectRun }: SidebarProps) {
  return (
    <aside className="w-80 min-w-80 bg-surface-secondary border-r border-border flex flex-col overflow-hidden">
      <div className="flex items-center gap-3 px-6 py-5 border-b border-border">
        <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-accent to-purple-400 flex items-center justify-center text-sm font-bold text-white">
          &lt;/&gt;
        </div>
        <div>
          <h1 className="text-base font-semibold tracking-tight">Coding Agent</h1>
          <span className="text-[10px] text-gray-500 bg-surface px-1.5 py-0.5 rounded">v1.0</span>
        </div>
      </div>

      <div className="flex border-b border-border">
        <button className="flex-1 py-2.5 text-xs font-medium text-accent border-b-2 border-accent bg-transparent">
          History
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {runs.length === 0 ? (
          <div className="text-center py-10 text-gray-500">
            <div className="text-3xl mb-3 opacity-40">&#128213;</div>
            <p className="text-sm">No runs yet.</p>
          </div>
        ) : (
          runs.map((run) => (
            <button
              key={run.run_id}
              onClick={() => onSelectRun(run.run_id)}
              className="w-full text-left bg-surface-card border border-border rounded-md px-4 py-3
                         hover:border-accent hover:bg-accent/5 transition-all duration-200 cursor-pointer"
            >
              <div className="flex items-center justify-between mb-1">
                <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full uppercase tracking-wider ${statusColor(run.status)}`}>
                  {run.status}
                </span>
              </div>
              <div className="text-sm text-gray-200 truncate">{run.task || 'No task'}</div>
              <div className="text-[10px] text-gray-500 mt-1">{formatTime(run.created_at)}</div>
            </button>
          ))
        )}
      </div>
    </aside>
  )
}
