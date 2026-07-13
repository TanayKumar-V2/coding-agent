import { useState, useEffect, useCallback, useRef } from 'react'
import Sidebar from './components/Sidebar'
import TopBar from './components/TopBar'
import ConfigPanel from './components/ConfigPanel'
import OutputArea from './components/OutputArea'
import { useWebSocket } from './hooks/useWebSocket'
import { listRuns, startRun, getRun } from './utils/api'
import type { RunInfo, LineItem, WsMessage } from './types'

export default function App() {
  const [runs, setRuns] = useState<RunInfo[]>([])
  const [lines, setLines] = useState<LineItem[]>([])
  const [status, setStatus] = useState<'idle' | 'running' | 'viewing' | 'error'>('idle')
  const [isRunning, setIsRunning] = useState(false)
  const ws = useWebSocket()
  const currentRunIdRef = useRef<string | null>(null)

  const loadRuns = useCallback(async () => {
    try {
      const data = await listRuns()
      setRuns(data.runs)
    } catch {
      // ignore
    }
  }, [])

  useEffect(() => {
    loadRuns()
  }, [loadRuns])

  const appendLine = useCallback((type: LineItem['type'], text: string) => {
    setLines((prev) => [...prev, ...text.split('\n').map((t) => ({ type, text: t }))])
  }, [])

  const handleWsMessage = useCallback(
    (msg: WsMessage) => {
      switch (msg.type) {
        case 'stdout':
          appendLine('stdout', String(msg.data ?? ''))
          break
        case 'stderr':
          appendLine('stderr', String(msg.data ?? ''))
          break
        case 'info':
          appendLine('info', String(msg.data ?? ''))
          break
        case 'done':
          appendLine('success', 'Run completed.')
          setStatus('idle')
          setIsRunning(false)
          currentRunIdRef.current = null
          loadRuns()
          break
        case 'error':
          appendLine('stderr', `Error: ${String(msg.data ?? '')}`)
          setStatus('error')
          setIsRunning(false)
          currentRunIdRef.current = null
          break
      }
    },
    [appendLine, loadRuns],
  )

  const handleWsStatus = useCallback((wsStatus: string) => {
    if (wsStatus === 'disconnected' || wsStatus === 'error') {
      if (currentRunIdRef.current) {
        setIsRunning(false)
        setStatus('idle')
        loadRuns()
      }
    }
  }, [loadRuns])

  useEffect(() => {
    ws.onMessage = handleWsMessage
    ws.onStatus = handleWsStatus
  }, [ws, handleWsMessage, handleWsStatus])

  const handleStartRun = useCallback(
    async (config: {
      task: string
      max_steps: number
      repo_dir: string | null
      test_cmd: string | null
      lint_cmd: string | null
    }) => {
      setLines([])
      setIsRunning(true)
      setStatus('running')
      appendLine('system', 'Starting agent run...')
      appendLine('system', `Task: ${config.task}`)
      appendLine('system', '')

      try {
        const result = await startRun(config)
        currentRunIdRef.current = result.run_id
        appendLine('info', `Run ID: ${result.run_id}`)
        appendLine('info', `Started at: ${result.created_at}`)
        appendLine('system', '')
        ws.connect(result.run_id)
      } catch (err) {
        appendLine('stderr', `Failed to start run: ${err instanceof Error ? err.message : String(err)}`)
        setIsRunning(false)
        setStatus('error')
      }
    },
    [appendLine, ws],
  )

  const handleSelectRun = useCallback(async (runId: string) => {
    setLines([])
    setStatus('viewing')
    appendLine('system', `Loading run ${runId}...`)

    try {
      const data = await getRun(runId)
      appendLine('system', `Run: ${runId}`)
      appendLine('system', `Status: ${data.status}`)
      appendLine('system', `Task: ${data.task ?? 'N/A'}`)
      appendLine('system', `Created: ${data.created_at ?? 'N/A'}`)
      appendLine('system', '')

      if (data.transcript) {
        for (const entry of data.transcript as Array<{ type: string; content: string | Record<string, unknown> }>) {
          appendLine('system', `[${entry.type}]`)
          if (typeof entry.content === 'string') {
            for (const line of entry.content.split('\n')) {
              if (line.trim()) appendLine('stdout', line)
            }
          }
        }
      }
    } catch {
      appendLine('stderr', 'Failed to load run transcript.')
      setStatus('error')
    }
  }, [appendLine])

  const handleClear = useCallback(() => {
    setLines([])
    setStatus('idle')
  }, [])

  const handleCopy = useCallback(async () => {
    const text = lines.map((l) => l.text).join('\n')
    try {
      await navigator.clipboard.writeText(text)
    } catch {
      // fallback
      const ta = document.createElement('textarea')
      ta.value = text
      document.body.appendChild(ta)
      ta.select()
      document.execCommand('copy')
      document.body.removeChild(ta)
    }
  }, [lines])

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-surface">
      <Sidebar runs={runs} onSelectRun={handleSelectRun} />
      <main className="flex-1 flex flex-col overflow-hidden">
        <TopBar status={status} onClear={handleClear} onCopy={handleCopy} />
        <ConfigPanel onStartRun={handleStartRun} isRunning={isRunning} />
        <OutputArea lines={lines} isRunning={isRunning} />
      </main>
    </div>
  )
}
