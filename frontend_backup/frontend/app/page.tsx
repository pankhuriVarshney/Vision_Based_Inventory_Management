'use client'

import React, { useState, useEffect, useRef, useCallback } from 'react'
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { Activity, Settings, Play, Pause, Download, BarChart3, TrendingUp, Zap, Cpu, Wifi, Clock, AlertCircle } from 'lucide-react'
import { WS_CONFIG, DETECTION_CONFIG } from '@/config'

// ============================================================================
// TYPE DEFINITIONS
// ============================================================================

interface Detection {
  bbox: [number, number, number, number]
  confidence: number
  class_id: number
  class_name: string
  center: [number, number]
}

interface InventoryData {
  total_objects: number
  class_counts: Record<string, number>
  density_score: number
  coverage_ratio: number
}

interface WebSocketMessage {
  frame_id: number
  timestamp: number
  detections: Detection[]
  inventory: InventoryData
  density_map: number[][]
  system_health?: {
    cpu_usage: number
    memory_usage: number
    connection_latency: number
    uptime: number
  }
}

interface SystemHealth {
  cpu_usage: number
  memory_usage: number
  connection_latency: number
  uptime: number
}

// ============================================================================
// COMPONENTS
// ============================================================================

// Animated Counter Component
const AnimatedCounter = ({ value, label }: { value: number; label: string }) => {
  const [displayValue, setDisplayValue] = useState(value)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    if (!mounted) return
    
    const duration = 600
    const start = Date.now()
    const startValue = displayValue

    const animate = () => {
      const now = Date.now()
      const progress = Math.min((now - start) / duration, 1)
      setDisplayValue(Math.floor(startValue + (value - startValue) * progress))

      if (progress < 1) {
        requestAnimationFrame(animate)
      }
    }

    requestAnimationFrame(animate)
  }, [value, mounted])

  return (
    <div className="flex items-center gap-2">
      <div className="text-3xl font-bold text-blue-400">{mounted ? displayValue : 0}</div>
      <div className="text-sm text-muted-foreground">{label}</div>
    </div>
  )
}

// Health Gauge Component
const HealthGauge = ({ value, label, unit }: { value: number; label: string; unit: string }) => {
  const color = value < 60 ? 'text-green-400' : value < 80 ? 'text-amber-400' : 'text-red-400'
  return (
    <div className="flex items-center justify-between">
      <span className="text-xs text-muted-foreground">{label}</span>
      <span className={`text-sm font-semibold ${color}`}>{value.toFixed(1)}{unit}</span>
    </div>
  )
}

// Canvas Component for Video Display
const VideoCanvas = ({ detections, timeSeriesData }: { detections: Detection[]; timeSeriesData: Array<{ time: number; count: number }> }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    if (!mounted || !canvasRef.current) return

    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // Clear canvas
    ctx.fillStyle = '#0a0f1f'
    ctx.fillRect(0, 0, canvas.width, canvas.height)

    // Draw detections
    detections.forEach((det) => {
      const [x1, y1, x2, y2] = det.bbox

      // Draw bounding box
      ctx.strokeStyle = DETECTION_CONFIG.CLASS_COLORS[det.class_name] || '#3b82f6'
      ctx.lineWidth = 2
      ctx.strokeRect(x1, y1, x2 - x1, y2 - y1)

      // Draw label
      ctx.fillStyle = DETECTION_CONFIG.CLASS_COLORS[det.class_name] || '#3b82f6'
      ctx.font = 'bold 12px sans-serif'
      const label = `${det.class_name} ${(det.confidence * 100).toFixed(0)}%`
      ctx.fillText(label, x1, y1 - 5)
    })
  }, [detections, mounted])

  return (
    <canvas
      ref={canvasRef}
      width={640}
      height={480}
      className="w-full border border-border rounded-lg bg-black"
    />
  )
}

// Sidebar Component
const Sidebar = ({
  wsUrl,
  setWsUrl,
  isConnected,
  model,
  setModel,
  gridSize,
  setGridSize,
}: {
  wsUrl: string
  setWsUrl: (url: string) => void
  isConnected: boolean
  model: string
  setModel: (model: string) => void
  gridSize: number
  setGridSize: (size: number) => void
}) => {
  return (
    <div className="w-80 border-r border-border bg-card flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-border">
        <div className="flex items-center gap-2">
          <Settings size={20} className="text-blue-400" />
          <h3 className="font-semibold text-foreground">Configuration</h3>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* WebSocket URL */}
        <div>
          <label className="text-xs font-semibold text-foreground block mb-2">WebSocket URL</label>
          <input
            type="text"
            value={wsUrl}
            onChange={(e) => setWsUrl(e.target.value)}
            placeholder="ws://192.168.1.100:8000/ws/detections"
            className="w-full px-3 py-2 bg-muted border border-border rounded-lg text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <div className="flex items-center gap-2 mt-2">
            <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
            <span className="text-xs text-muted-foreground">{isConnected ? 'Connected' : 'Disconnected'}</span>
          </div>
        </div>

        {/* Model Selector */}
        <div>
          <label className="text-xs font-semibold text-foreground block mb-2">Detection Model</label>
          <select
            value={model}
            onChange={(e) => setModel(e.target.value)}
            className="w-full px-3 py-2 bg-muted border border-border rounded-lg text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option>YOLOv8n</option>
            <option>YOLOv8s</option>
            <option>YOLOv8m</option>
          </select>
        </div>

        {/* Grid Size */}
        <div>
          <label className="text-xs font-semibold text-foreground block mb-2">Heatmap Grid Size</label>
          <select
            value={gridSize}
            onChange={(e) => setGridSize(Number(e.target.value) as 2 | 3 | 4)}
            className="w-full px-3 py-2 bg-muted border border-border rounded-lg text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value={2}>2x2</option>
            <option value={3}>3x3</option>
            <option value={4}>4x4</option>
          </select>
        </div>

        {/* Export */}
        <button className="w-full py-2 px-3 rounded-lg border border-border hover:bg-muted text-foreground text-sm font-medium transition-all flex items-center justify-center gap-2">
          <Download size={16} />
          Export Data
        </button>
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-border text-xs text-muted-foreground">
        <p>Real-time streaming from backend</p>
      </div>
    </div>
  )
}

// ============================================================================
// MAIN DASHBOARD COMPONENT
// ============================================================================

export default function Dashboard() {
  const [data, setData] = useState<WebSocketMessage | null>(null)
  const [health, setHealth] = useState<SystemHealth>({
    cpu_usage: 0,
    memory_usage: 0,
    connection_latency: 0,
    uptime: 0,
  })
  const [isConnected, setIsConnected] = useState(false)
  const [fps, setFps] = useState(0)
  const [frameCount, setFrameCount] = useState(0)
  const [timeSeriesData, setTimeSeriesData] = useState<Array<{ time: number; count: number }>>([])
  const [mounted, setMounted] = useState(false)
  const [formattedTime, setFormattedTime] = useState('--:--:--')
  const [wsUrl, setWsUrl] = useState(WS_CONFIG.URL)
  const [model, setModel] = useState('YOLOv8n')
  const [gridSize, setGridSize] = useState<2 | 3 | 4>(3)
  const [error, setError] = useState<string | null>(null)

  const wsRef = useRef<WebSocket | null>(null)
  const fpsIntervalRef = useRef<NodeJS.Timeout | null>(null)
  const lastFrameTimeRef = useRef<number>(Date.now())

  // Mount check
  useEffect(() => {
    setMounted(true)
  }, [])

  // Update formatted time
  useEffect(() => {
    if (mounted && data) {
      setFormattedTime(new Date(data.timestamp).toLocaleTimeString())
    }
  }, [data?.timestamp, mounted])

  // WebSocket connection
  useEffect(() => {
    if (!mounted || !wsUrl) return

    const connectWebSocket = () => {
      try {
        console.log('[v0] Connecting to WebSocket:', wsUrl)
        const ws = new WebSocket(wsUrl)

        ws.onopen = () => {
          console.log('[v0] WebSocket connected')
          setIsConnected(true)
          setError(null)
        }

        ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data)
            setData(message)
            setFrameCount((prev) => prev + 1)

            // Update health if provided
            if (message.system_health) {
              setHealth(message.system_health)
            }

            // Update time series
            setTimeSeriesData((prev) => {
              const updated = [...prev, { time: prev.length, count: message.inventory.total_objects }]
              return updated.slice(-60) // Keep last 60 seconds
            })
          } catch (err) {
            console.error('[v0] Error parsing message:', err)
          }
        }

        ws.onerror = (event) => {
          console.error('[v0] WebSocket error:', event)
          setError('WebSocket connection error')
          setIsConnected(false)
        }

        ws.onclose = () => {
          console.log('[v0] WebSocket disconnected')
          setIsConnected(false)
          // Attempt reconnect after delay
          setTimeout(() => {
            if (mounted) {
              console.log('[v0] Attempting to reconnect...')
              connectWebSocket()
            }
          }, WS_CONFIG.RECONNECT_DELAY)
        }

        wsRef.current = ws
      } catch (err) {
        console.error('[v0] WebSocket connection error:', err)
        setError('Failed to connect to WebSocket')
        setIsConnected(false)
      }
    }

    connectWebSocket()

    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [wsUrl, mounted])

  // FPS counter
  useEffect(() => {
    fpsIntervalRef.current = setInterval(() => {
      const now = Date.now()
      const timeDiff = (now - lastFrameTimeRef.current) / 1000
      setFps(Math.round(frameCount / timeDiff))
      setFrameCount(0)
      lastFrameTimeRef.current = now
    }, 1000)

    return () => {
      if (fpsIntervalRef.current) clearInterval(fpsIntervalRef.current)
    }
  }, [frameCount])

  if (!mounted) {
    return (
      <div className="flex items-center justify-center h-screen bg-background">
        <div className="text-center">
          <div className="animate-spin mb-4">
            <Zap className="text-blue-400" size={40} />
          </div>
          <p className="text-foreground">Initializing...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      {/* Sidebar */}
      <Sidebar
        wsUrl={wsUrl}
        setWsUrl={setWsUrl}
        isConnected={isConnected}
        model={model}
        setModel={setModel}
        gridSize={gridSize}
        setGridSize={setGridSize}
      />

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <div className="border-b border-border bg-card p-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-foreground">Vision-Based Smart Inventory</h1>
              <p className="text-sm text-muted-foreground mt-1">Real-time retail shelf detection and monitoring</p>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-right">
                <p className="text-2xl font-bold text-blue-400">{fps} FPS</p>
                <p className="text-xs text-muted-foreground">Frame rate</p>
              </div>
              <div className={`flex items-center gap-2 px-3 py-2 rounded-lg ${isConnected ? 'bg-green-500/10 border border-green-500/30' : 'bg-red-500/10 border border-red-500/30'}`}>
                <Activity size={16} className={isConnected ? 'text-green-500 animate-pulse' : 'text-red-500'} />
                <span className="text-xs text-foreground">{isConnected ? 'Live' : 'Offline'}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Error Banner */}
        {error && (
          <div className="bg-red-500/10 border-b border-red-500/30 px-6 py-3 flex items-center gap-2">
            <AlertCircle size={16} className="text-red-500" />
            <p className="text-sm text-red-400">{error}</p>
          </div>
        )}

        {/* Main Content Area */}
        <div className="flex-1 overflow-auto">
          <div className="p-6 space-y-6">
            {!data ? (
              <div className="text-center py-12">
                <AlertCircle size={48} className="text-muted-foreground mx-auto mb-4" />
                <p className="text-muted-foreground">Waiting for data from backend...</p>
                <p className="text-xs text-muted-foreground mt-2">Make sure your backend is running and the WebSocket URL is correct</p>
              </div>
            ) : (
              <>
                {/* Live Stats */}
                <div className="grid grid-cols-4 gap-4">
                  <div className="bg-card border border-border rounded-lg p-4">
                    <p className="text-xs text-muted-foreground mb-2">Total Objects</p>
                    <AnimatedCounter value={data.inventory.total_objects} label="items" />
                  </div>
                  <div className="bg-card border border-border rounded-lg p-4">
                    <p className="text-xs text-muted-foreground mb-2">Density Score</p>
                    <div className="text-3xl font-bold text-amber-400">{(data.inventory.density_score * 100).toFixed(1)}%</div>
                  </div>
                  <div className="bg-card border border-border rounded-lg p-4">
                    <p className="text-xs text-muted-foreground mb-2">Coverage Ratio</p>
                    <div className="text-3xl font-bold text-cyan-400">{(data.inventory.coverage_ratio * 100).toFixed(1)}%</div>
                  </div>
                  <div className="bg-card border border-border rounded-lg p-4">
                    <p className="text-xs text-muted-foreground mb-2">Detections</p>
                    <AnimatedCounter value={data.detections.length} label="detections" />
                  </div>
                </div>

                {/* Video and Info */}
                <div className="grid grid-cols-3 gap-6">
                  {/* Video Feed */}
                  <div className="col-span-2">
                    <div className="bg-card border border-border rounded-lg p-4">
                      <h3 className="text-sm font-semibold text-foreground mb-3">Live Camera Feed</h3>
                      <VideoCanvas detections={data.detections} timeSeriesData={timeSeriesData} />
                      <p className="text-xs text-muted-foreground mt-3">
                        Frame #{data.frame_id} • Last updated {formattedTime}
                      </p>
                    </div>
                  </div>

                  {/* System Health */}
                  <div className="bg-card border border-border rounded-lg p-4">
                    <h3 className="text-sm font-semibold text-foreground mb-4 flex items-center gap-2">
                      <Cpu size={16} className="text-blue-400" />
                      System Health
                    </h3>
                    <div className="space-y-3">
                      <HealthGauge value={health.cpu_usage} label="CPU Usage" unit="%" />
                      <HealthGauge value={health.memory_usage} label="Memory" unit="%" />
                      <HealthGauge value={health.connection_latency} label="Latency" unit="ms" />
                      <div className="border-t border-border pt-3 mt-3">
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-muted-foreground">Uptime</span>
                          <span className="text-sm font-semibold text-cyan-400">
                            {Math.floor(health.uptime / 3600)}h {Math.floor((health.uptime % 3600) / 60)}m
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Object Labels & Inventory */}
                <div className="grid grid-cols-2 gap-6">
                  {/* Object Labels */}
                  <div className="bg-card border border-border rounded-lg p-4">
                    <h3 className="text-sm font-semibold text-foreground mb-4 flex items-center gap-2">
                      <BarChart3 size={16} className="text-green-400" />
                      Detected Objects
                    </h3>
                    <div className="space-y-2">
                      {Object.entries(data.inventory.class_counts).map(([className, count]) => (
                        <div key={className} className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <div
                              className="w-3 h-3 rounded-full"
                              style={{ backgroundColor: DETECTION_CONFIG.CLASS_COLORS[className] || '#8b5cf6' }}
                            ></div>
                            <span className="text-sm text-foreground">{className}</span>
                          </div>
                          <span className="text-sm font-semibold text-blue-400">{count}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Time Series Chart */}
                  <div className="bg-card border border-border rounded-lg p-4">
                    <h3 className="text-sm font-semibold text-foreground mb-4 flex items-center gap-2">
                      <TrendingUp size={16} className="text-amber-400" />
                      Object Count Trend
                    </h3>
                    {timeSeriesData.length > 0 ? (
                      <ResponsiveContainer width="100%" height={200}>
                        <LineChart data={timeSeriesData}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#1e2a42" />
                          <XAxis dataKey="time" stroke="#8892b0" style={{ fontSize: 12 }} />
                          <YAxis stroke="#8892b0" style={{ fontSize: 12 }} />
                          <Tooltip
                            contentStyle={{ backgroundColor: '#0f1528', border: '1px solid #1e2a42' }}
                            labelStyle={{ color: '#e8eaf6' }}
                          />
                          <Line
                            type="monotone"
                            dataKey="count"
                            stroke="#3b82f6"
                            dot={false}
                            isAnimationActive={false}
                            strokeWidth={2}
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    ) : (
                      <div className="h-[200px] flex items-center justify-center text-muted-foreground text-sm">
                        Collecting data...
                      </div>
                    )}
                  </div>
                </div>

                {/* Heatmap */}
                <div className="bg-card border border-border rounded-lg p-4">
                  <h3 className="text-sm font-semibold text-foreground mb-4">Shelf Density Heatmap</h3>
                  <div className="grid gap-1" style={{ gridTemplateColumns: `repeat(${gridSize}, 1fr)` }}>
                    {data.density_map.map((row, i) =>
                      row.map((intensity, j) => (
                        <div
                          key={`${i}-${j}`}
                          className="aspect-square rounded-lg border border-border/50 flex items-center justify-center text-xs font-semibold"
                          style={{
                            backgroundColor: `rgba(59, 130, 246, ${intensity})`,
                            color: intensity > 0.5 ? '#0a0f1f' : '#e8eaf6',
                          }}
                        >
                          {(intensity * 100).toFixed(0)}%
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
