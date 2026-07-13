import { useEffect, useRef } from 'react'
import type { LineItem } from '../types'

interface OutputAreaProps {
  lines: LineItem[]
  isRunning: boolean
}

function lineColor(type: string): string {
  switch (type) {
    case 'stdout':
      return 'text-gray-100'
    case 'stderr':
      return 'text-red-400'
    case 'info':
      return 'text-accent'
    case 'success':
      return 'text-green'
    case 'warning':
      return 'text-yellow-400'
    case 'system':
      return 'text-gray-500 italic'
    default:
      return 'text-gray-100'
  }
}

export default function OutputArea({ lines, isRunning }: OutputAreaProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [lines])

  if (lines.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center text-gray-500 px-8 py-12">
        <svg className="w-12 h-12 mb-4 opacity-30" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
        </svg>
        <h3 className="text-base font-medium text-gray-400 mb-1">Ready</h3>
        <p className="text-sm text-center max-w-sm">Configure your task above and click "Run Agent" to start.</p>
        <div className="flex gap-6 mt-5 text-[11px] text-gray-600">
          <span><kbd className="bg-surface-card border border-border rounded px-1.5 py-0.5 font-mono text-gray-400">Enter</kbd> Run</span>
          <span><kbd className="bg-surface-card border border-border rounded px-1.5 py-0.5 font-mono text-gray-400">Ctrl+L</kbd> Clear</span>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto p-6 font-mono text-sm leading-relaxed bg-surface">
      {lines.map((line, i) => (
        <div key={i} className={`terminal-line ${lineColor(line.type)}`}>
          {line.text}
        </div>
      ))}
      {isRunning && (
        <div className="terminal-line text-gray-500">
          <span className="inline-block w-2 h-4 bg-accent animate-pulse" />
        </div>
      )}
      <div ref={bottomRef} />
    </div>
  )
}
