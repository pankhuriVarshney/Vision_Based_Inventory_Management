"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { FileText, AlertTriangle, Cpu, Eye } from "lucide-react"
import type { DetectionLogEntry } from "@/lib/mock-data"
import { cn } from "@/lib/utils"

interface ActivityLogProps {
  logs: DetectionLogEntry[]
}

const iconMap = {
  detection: Eye,
  alert: AlertTriangle,
  system: Cpu,
}

const severityStyles = {
  info: "text-primary",
  warning: "text-warning",
  critical: "text-destructive",
}

const severityDotStyles = {
  info: "bg-primary",
  warning: "bg-warning",
  critical: "bg-destructive",
}

export function ActivityLog({ logs }: ActivityLogProps) {
  return (
    <Card className="border-border bg-card">
      <CardHeader className="pb-2">
        <div className="flex items-center gap-2">
          <FileText className="h-4 w-4 text-primary" />
          <CardTitle className="text-sm font-medium text-card-foreground">
            Activity Log
          </CardTitle>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <ScrollArea className="h-52">
          <div className="flex flex-col gap-1">
            {logs.map((log) => {
              const Icon = iconMap[log.type]
              const timeDiff = Math.round((Date.now() - log.timestamp) / 1000)
              const timeLabel =
                timeDiff < 60
                  ? `${timeDiff}s ago`
                  : `${Math.round(timeDiff / 60)}m ago`

              return (
                <div
                  key={log.id}
                  className="flex items-start gap-2.5 rounded-md px-2 py-1.5 transition-colors hover:bg-secondary/50"
                >
                  <div className={cn("mt-0.5 rounded p-1", severityStyles[log.severity])}>
                    <Icon className="h-3 w-3" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs text-foreground leading-relaxed">{log.message}</p>
                    <div className="mt-0.5 flex items-center gap-2">
                      <span
                        className={cn(
                          "inline-block h-1.5 w-1.5 rounded-full",
                          severityDotStyles[log.severity]
                        )}
                      />
                      <span className="text-[10px] text-muted-foreground capitalize">
                        {log.severity}
                      </span>
                      <span className="text-[10px] text-muted-foreground">{timeLabel}</span>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  )
}
