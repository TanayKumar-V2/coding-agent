interface TopBarProps {
  status: 'idle' | 'running' | 'viewing' | 'error'
  onClear: () => void
  onCopy: () => void
}

function statusConfig(status: string) {
  switch (status) {
    case 'running':
      return { dot: 'bg-green animate-pulse-slow', label: 'Running' }
    case 'viewing':
      return { dot: 'bg-accent', label: 'Viewing Log' }
    case 'error':
      return { dot: 'bg-red-500', label: 'Error' }
    default:
      return { dot: 'bg-gray-500', label: 'Idle' }
  }
}

export default function TopBar({ status, onClear, onCopy }: TopBarProps) {
  const cfg = statusConfig(status)

  return (
    <div className="flex items-center justify-between px-7 py-4 border-b border-border bg-surface-secondary">
      <h2 className="text-sm font-medium text-gray-400 flex items-center gap-2.5">
        <span className={`w-2 h-2 rounded-full ${cfg.dot}`} />
        <span>{cfg.label}</span>
      </h2>
      <div className="flex items-center gap-2">
        <button onClick={onCopy} className="btn-secondary text-xs" title="Copy output">
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
          Copy
        </button>
        <button onClick={onClear} className="btn-secondary text-xs" title="Clear output">
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
          Clear
        </button>
      </div>
    </div>
  )
}
