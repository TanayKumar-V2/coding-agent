import { useState } from 'react'

interface ConfigPanelProps {
  onStartRun: (config: {
    task: string
    max_steps: number
    repo_dir: string | null
    test_cmd: string | null
    lint_cmd: string | null
  }) => void
  isRunning: boolean
}

export default function ConfigPanel({ onStartRun, isRunning }: ConfigPanelProps) {
  const [task, setTask] = useState('')
  const [maxSteps, setMaxSteps] = useState(15)
  const [repoDir, setRepoDir] = useState('')
  const [testCmd, setTestCmd] = useState('')
  const [lintCmd, setLintCmd] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!task.trim()) return
    onStartRun({
      task: task.trim(),
      max_steps: maxSteps,
      repo_dir: repoDir || null,
      test_cmd: testCmd || null,
      lint_cmd: lintCmd || null,
    })
  }

  return (
    <div className="bg-surface-secondary border-b border-border px-7 py-6">
      <form onSubmit={handleSubmit}>
        <div className="grid grid-cols-2 gap-3.5">
          <div className="col-span-2 flex flex-col gap-1">
            <label className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider">
              Task Description
            </label>
            <textarea
              value={task}
              onChange={(e) => setTask(e.target.value)}
              placeholder="e.g. Find the bug in the repository and fix it..."
              className="bg-surface-input border border-border rounded-md px-3 py-2.5 text-sm text-gray-100
                         placeholder-gray-600 focus:border-accent focus:ring-2 focus:ring-accent/20
                         transition-all duration-200 resize-vertical min-h-[60px]"
              required
            />
          </div>

          <Field label="Max Steps">
            <input
              type="number"
              value={maxSteps}
              onChange={(e) => setMaxSteps(Math.max(1, Math.min(100, Number(e.target.value))))}
              min={1}
              max={100}
              className="bg-surface-input border border-border rounded-md px-3 py-2.5 text-sm text-gray-100
                         focus:border-accent focus:ring-2 focus:ring-accent/20 transition-all duration-200"
            />
          </Field>

          <Field label="Repo Directory">
            <input
              type="text"
              value={repoDir}
              onChange={(e) => setRepoDir(e.target.value)}
              placeholder="/path/to/repo"
              className="bg-surface-input border border-border rounded-md px-3 py-2.5 text-sm text-gray-100
                         placeholder-gray-600 focus:border-accent focus:ring-2 focus:ring-accent/20
                         transition-all duration-200"
            />
          </Field>

          <Field label="Test Command">
            <input
              type="text"
              value={testCmd}
              onChange={(e) => setTestCmd(e.target.value)}
              placeholder="npm test"
              className="bg-surface-input border border-border rounded-md px-3 py-2.5 text-sm text-gray-100
                         placeholder-gray-600 focus:border-accent focus:ring-2 focus:ring-accent/20
                         transition-all duration-200"
            />
          </Field>

          <Field label="Lint Command">
            <input
              type="text"
              value={lintCmd}
              onChange={(e) => setLintCmd(e.target.value)}
              placeholder="npm run lint"
              className="bg-surface-input border border-border rounded-md px-3 py-2.5 text-sm text-gray-100
                         placeholder-gray-600 focus:border-accent focus:ring-2 focus:ring-accent/20
                         transition-all duration-200"
            />
          </Field>
        </div>

        <div className="flex items-center gap-3 mt-4">
          <button
            type="submit"
            disabled={isRunning || !task.trim()}
            className="btn-primary"
          >
            {isRunning ? (
              <>
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Running...
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                Run Agent
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  )
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider">{label}</label>
      {children}
    </div>
  )
}
