"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Server, Cpu, HardDrive, Thermometer, Brain } from "lucide-react"
import { useEffect, useState } from "react"

interface SystemInfoProps {
  connected: boolean
  model: string
  framesProcessed: number
}

export function SystemInfo({ connected, model, framesProcessed }: SystemInfoProps) {
  const uptime = Math.floor(framesProcessed / 24) // approximate seconds at ~24fps
  const [learningStats, setLearningStats] = useState<any>(null)

  const formatUptime = (seconds: number) => {
    const h = Math.floor(seconds / 3600)
    const m = Math.floor((seconds % 3600) / 60)
    const s = seconds % 60
    return `${h.toString().padStart(2, "0")}:${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`
  }

  useEffect(() => {
    const fetchLearningStats = async () => {
      try {
        const res = await fetch('http://192.168.1.4:8000/api/learning/status')
        const data = await res.json()
        if (data.success) setLearningStats(data.data)
      } catch (e) {
        console.error('Failed to fetch learning stats:', e)
      }
    }
    fetchLearningStats()
    const interval = setInterval(fetchLearningStats, 15000)
    return () => clearInterval(interval)
  }, [])

  return (
    <Card className="border-border bg-card">
      <CardHeader className="pb-2">
        <div className="flex items-center gap-2">
          <Server className="h-4 w-4 text-primary" />
          <CardTitle className="text-sm font-medium text-card-foreground">System Info</CardTitle>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="flex flex-col gap-3">
          {/* Status */}
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground">Status</span>
            <Badge
              variant="outline"
              className={
                connected
                  ? "border-success/30 bg-success/10 text-success"
                  : "border-destructive/30 bg-destructive/10 text-destructive"
              }
            >
              {connected ? "Online" : "Offline"}
            </Badge>
          </div>

          {/* Device */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <Cpu className="h-3 w-3 text-muted-foreground" />
              <span className="text-xs text-muted-foreground">Device</span>
            </div>
            <span className="font-mono text-xs text-foreground">Raspberry Pi 5</span>
          </div>

          {/* Model */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <HardDrive className="h-3 w-3 text-muted-foreground" />
              <span className="text-xs text-muted-foreground">Model</span>
            </div>
            <span className="font-mono text-xs text-primary">{model}</span>
          </div>

          {/* Temperature */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <Thermometer className="h-3 w-3 text-muted-foreground" />
              <span className="text-xs text-muted-foreground">Temp</span>
            </div>
            <span className="font-mono text-xs text-warning">52.3 C</span>
          </div>

          {/* Uptime */}
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground">Uptime</span>
            <span className="font-mono text-xs text-foreground">{formatUptime(uptime)}</span>
          </div>

          {/* Divider */}
          <div className="border-t border-border my-1"></div>

          {/* Continual Learning Stats - ADDED HERE */}
          <div className="flex items-center gap-2 mt-1">
            <Brain className="h-3 w-3 text-primary" />
            <span className="text-xs font-medium text-foreground">Continual Learning</span>
          </div>

          {learningStats ? (
            <>
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">Learning Events</span>
                <span className="font-mono text-xs text-primary font-bold">
                  {learningStats.total_learning_events || 0}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">Experience Buffer</span>
                <span className="font-mono text-xs">
                  {learningStats.buffer_size || 0}/{learningStats.buffer_max || 500}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">Avg Confidence</span>
                <span className="font-mono text-xs">
                  {learningStats.avg_confidence ? (learningStats.avg_confidence * 100).toFixed(0) : 0}%
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">Auto-Learn</span>
                <Badge variant={learningStats.auto_learn_enabled ? "default" : "secondary"} className="text-xs">
                  {learningStats.auto_learn_enabled ? "ON" : "OFF"}
                </Badge>
              </div>
            </>
          ) : (
            <div className="text-center py-2">
              <span className="text-xs text-muted-foreground">Collecting experiences...</span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}