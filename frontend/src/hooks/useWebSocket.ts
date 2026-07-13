import { useRef, useCallback, useEffect } from 'react'
import type { WsMessage } from '../types'
import { buildWsUrl } from '../utils/api'

type MessageHandler = (msg: WsMessage) => void
type StatusHandler = (status: 'connecting' | 'connected' | 'disconnected' | 'error') => void

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null)
  const onMessageRef = useRef<MessageHandler | null>(null)
  const onStatusRef = useRef<StatusHandler | null>(null)

  const connect = useCallback((runId: string) => {
    if (wsRef.current) {
      wsRef.current.close()
    }

    onStatusRef.current?.('connecting')

    const ws = new WebSocket(buildWsUrl(runId))
    wsRef.current = ws

    ws.onopen = () => {
      onStatusRef.current?.('connected')
    }

    ws.onmessage = (event) => {
      try {
        const msg: WsMessage = JSON.parse(event.data)
        onMessageRef.current?.(msg)
      } catch {
        // ignore malformed messages
      }
    }

    ws.onerror = () => {
      onStatusRef.current?.('error')
    }

    ws.onclose = () => {
      onStatusRef.current?.('disconnected')
      if (wsRef.current === ws) {
        wsRef.current = null
      }
    }
  }, [])

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
  }, [])

  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [])

  return {
    connect,
    disconnect,
    set onMessage(handler: MessageHandler) {
      onMessageRef.current = handler
    },
    set onStatus(handler: StatusHandler) {
      onStatusRef.current = handler
    },
  }
}
