"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Grid3X3 } from "lucide-react"
import type { GridSize } from "@/lib/types"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"

interface ShelfHeatmapProps {
  densityMap: number[][]
  gridSize: GridSize
}

function getCellColor(value: number, maxVal: number): string {
  if (maxVal === 0) return "rgba(30, 41, 59, 0.5)"
  const intensity = value / maxVal
  if (intensity === 0) return "rgba(30, 41, 59, 0.5)"
  if (intensity < 0.25) return "rgba(34, 211, 238, 0.2)"
  if (intensity < 0.5) return "rgba(34, 211, 238, 0.4)"
  if (intensity < 0.75) return "rgba(251, 191, 36, 0.5)"
  return "rgba(248, 113, 113, 0.6)"
}

function getCellBorder(value: number, maxVal: number): string {
  if (maxVal === 0) return "border-border/30"
  const intensity = value / maxVal
  if (intensity < 0.25) return "border-primary/20"
  if (intensity < 0.5) return "border-primary/40"
  if (intensity < 0.75) return "border-warning/40"
  return "border-destructive/40"
}

function getZoneLabel(row: number, col: number): string {
  const rowLabels = "ABCDEFGH"
  return `${rowLabels[row]}${col + 1}`
}

export function ShelfHeatmap({ densityMap, gridSize }: ShelfHeatmapProps) {
  const rows = densityMap.length
  const cols = densityMap[0]?.length || 0
  const maxVal = Math.max(...densityMap.flat(), 1)
  const totalItems = densityMap.flat().reduce((a, b) => a + b, 0)

  return (
    <Card className="border-border bg-card">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Grid3X3 className="h-4 w-4 text-primary" />
            <CardTitle className="text-sm font-medium text-card-foreground">
              Shelf Density Map
            </CardTitle>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs text-muted-foreground">Grid: {gridSize}</span>
            <span className="font-mono text-xs text-primary">{totalItems} items</span>
          </div>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <TooltipProvider delayDuration={0}>
          <div
            className="grid gap-1.5"
            style={{
              gridTemplateColumns: `repeat(${cols}, 1fr)`,
              gridTemplateRows: `repeat(${rows}, 1fr)`,
            }}
          >
            {densityMap.map((row, ri) =>
              row.map((val, ci) => (
                <Tooltip key={`${ri}-${ci}`}>
                  <TooltipTrigger asChild>
                    <div
                      className={`flex flex-col items-center justify-center rounded-md border p-3 transition-all duration-300 hover:scale-105 cursor-default ${getCellBorder(val, maxVal)}`}
                      style={{ backgroundColor: getCellColor(val, maxVal), minHeight: "64px" }}
                    >
                      <span className="font-mono text-lg font-bold text-foreground">{val}</span>
                      <span className="text-[10px] text-muted-foreground">{getZoneLabel(ri, ci)}</span>
                    </div>
                  </TooltipTrigger>
                  <TooltipContent side="top" className="border-border bg-popover text-popover-foreground">
                    <div className="flex flex-col gap-1">
                      <span className="font-medium">Zone {getZoneLabel(ri, ci)}</span>
                      <span className="text-xs text-muted-foreground">
                        {val} items detected
                      </span>
                      <span className="text-xs text-muted-foreground">
                        Density: {((val / maxVal) * 100).toFixed(0)}%
                      </span>
                    </div>
                  </TooltipContent>
                </Tooltip>
              ))
            )}
          </div>
        </TooltipProvider>

        {/* Legend */}
        <div className="mt-3 flex items-center justify-between">
          <span className="text-[10px] text-muted-foreground">Low</span>
          <div className="flex h-2 flex-1 mx-2 overflow-hidden rounded-full">
            <div className="flex-1 bg-primary/20" />
            <div className="flex-1 bg-primary/40" />
            <div className="flex-1 bg-warning/50" />
            <div className="flex-1 bg-destructive/60" />
          </div>
          <span className="text-[10px] text-muted-foreground">High</span>
        </div>
      </CardContent>
    </Card>
  )
}
