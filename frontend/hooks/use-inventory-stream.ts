"use client"

import { useState, useEffect, useCallback, useRef } from "react"
import type { FrameData, TimeSeriesPoint } from "@/lib/types"
import { INITIAL_FRAME, generateMockFrame, generateInitialTimeSeries } from "@/lib/mock-data"

const MAX_HISTORY_POINTS = 60

interface UseInventoryStreamOptions {
  /** WebSocket URL - set to your backend, e.g. "ws://localhost:8000/ws" */
  wsUrl?: string
  /** Use mock data instead of real WebSocket */
  useMock?: boolean
}

export function useInventoryStream({ wsUrl, useMock = true }: UseInventoryStreamOptions = {}) {
  const [currentFrame, setCurrentFrame] = useState<FrameData>(INITIAL_FRAME)
  const [timeSeries, setTimeSeries] = useState<TimeSeriesPoint[]>(generateInitialTimeSeries)
  const [connected, setConnected] = useState(false)
  const [framesProcessed, setFramesProcessed] = useState(0)
  const frameIdRef = useRef(0)
  const wsRef = useRef<WebSocket | null>(null)

  const addTimeSeriesPoint = useCallback((frame: FrameData) => {
    const date = new Date(frame.timestamp * 1000)
    const point: TimeSeriesPoint = {
      time: `${date.getMinutes().toString().padStart(2, "0")}:${date.getSeconds().toString().padStart(2, "0")}`,
      timestamp: frame.timestamp * 1000,
      total_objects: frame.inventory.total_objects,
      density_score: frame.inventory.density_score,
      fps: frame.fps || 0,
    }

    setTimeSeries((prev) => {
      const next = [...prev, point]
      if (next.length > MAX_HISTORY_POINTS) {
        return next.slice(next.length - MAX_HISTORY_POINTS)
      }
      return next
    })
  }, [])

  // Mock data stream
  useEffect(() => {
    if (!useMock) return

    setConnected(true)

    const interval = setInterval(() => {
      frameIdRef.current += 1
      const frame = generateMockFrame(frameIdRef.current)
      setCurrentFrame(frame)
      setFramesProcessed((prev) => prev + 1)
      addTimeSeriesPoint(frame)
    }, 1000)

    return () => {
      clearInterval(interval)
      setConnected(false)
    }
  }, [useMock, addTimeSeriesPoint])

  // Real WebSocket connection
  useEffect(() => {
    if (useMock || !wsUrl) return

    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => {
      setConnected(true)
    }

    ws.onmessage = (event) => {
      try {
        const frame: FrameData = JSON.parse(event.data)
        setCurrentFrame(frame)
        setFramesProcessed((prev) => prev + 1)
        addTimeSeriesPoint(frame)
      } catch {
        console.error("[v0] Failed to parse WebSocket message")
      }
    }

    ws.onclose = () => {
      setConnected(false)
    }

    ws.onerror = () => {
      setConnected(false)
    }

    return () => {
      ws.close()
      wsRef.current = null
    }
  }, [useMock, wsUrl, addTimeSeriesPoint])

  // Send configuration to backend
  const sendConfig = useCallback(
    (config: Record<string, unknown>) => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify(config))
      }
    },
    []
  )

  return {
    currentFrame,
    timeSeries,
    connected,
    framesProcessed,
    sendConfig,
  }
}
