"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Server, Cpu, HardDrive, Thermometer } from "lucide-react"

interface SystemInfoProps {
  connected: boolean
  model: string
  framesProcessed: number
}

export function SystemInfo({ connected, model, framesProcessed }: SystemInfoProps) {
  const uptime = Math.floor(framesProcessed / 24) // approximate seconds at ~24fps

  const formatUptime = (seconds: number) => {
    const h = Math.floor(seconds / 3600)
    const m = Math.floor((seconds % 3600) / 60)
    const s = seconds % 60
    return `${h.toString().padStart(2, "0")}:${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`
  }

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
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <Cpu className="h-3 w-3 text-muted-foreground" />
              <span className="text-xs text-muted-foreground">Device</span>
            </div>
            <span className="font-mono text-xs text-foreground">Raspberry Pi 5</span>
          </div>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <HardDrive className="h-3 w-3 text-muted-foreground" />
              <span className="text-xs text-muted-foreground">Model</span>
            </div>
            <span className="font-mono text-xs text-primary">{model}</span>
          </div>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <Thermometer className="h-3 w-3 text-muted-foreground" />
              <span className="text-xs text-muted-foreground">Temp</span>
            </div>
            <span className="font-mono text-xs text-warning">52.3 C</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground">Uptime</span>
            <span className="font-mono text-xs text-foreground">{formatUptime(uptime)}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
