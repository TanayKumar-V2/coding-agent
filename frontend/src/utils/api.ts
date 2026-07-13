import type { RunRequest, RunInfo } from '../types'

const BASE = '/api'

export async function startRun(req: RunRequest): Promise<{ run_id: string; status: string; created_at: string }> {
  const res = await fetch(`${BASE}/runs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
  if (!res.ok) throw new Error(`Failed to start run: ${res.statusText}`)
  return res.json()
}

export async function listRuns(): Promise<{ runs: RunInfo[] }> {
  const res = await fetch(`${BASE}/runs`)
  if (!res.ok) throw new Error(`Failed to list runs: ${res.statusText}`)
  return res.json()
}

export async function getRun(runId: string): Promise<RunInfo & { transcript?: unknown[] }> {
  const res = await fetch(`${BASE}/runs/${runId}`)
  if (!res.ok) throw new Error(`Failed to get run: ${res.statusText}`)
  return res.json()
}

export function buildWsUrl(runId: string): string {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${protocol}//${window.location.host}/api/ws/${runId}`
}
