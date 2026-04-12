"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Slider } from "@/components/ui/slider"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Button } from "@/components/ui/button"
import { Download, SlidersHorizontal } from "lucide-react"
import type { GridSize, ModelType, TimeSeriesPoint } from "@/lib/types"

interface ControlPanelProps {
  confidenceThreshold: number
  onConfidenceChange: (value: number) => void
  model: ModelType
  onModelChange: (model: ModelType) => void
  gridSize: GridSize
  onGridSizeChange: (size: GridSize) => void
  timeSeries: TimeSeriesPoint[]
}

export function ControlPanel({
  confidenceThreshold,
  onConfidenceChange,
  model,
  onModelChange,
  gridSize,
  onGridSizeChange,
  timeSeries,
}: ControlPanelProps) {
  const exportCSV = () => {
    const headers = "time,total_objects,density_score,fps\n"
    const rows = timeSeries
      .map((p) => `${p.time},${p.total_objects},${p.density_score.toFixed(2)},${p.fps.toFixed(1)}`)
      .join("\n")
    const csv = headers + rows
    const blob = new Blob([csv], { type: "text/csv" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `inventory-data-${new Date().toISOString().slice(0, 10)}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <Card className="border-border bg-card">
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          <SlidersHorizontal className="h-4 w-4 text-primary" />
          <CardTitle className="text-sm font-medium text-card-foreground">Controls</CardTitle>
        </div>
      </CardHeader>
      <CardContent className="flex flex-col gap-5 pt-0">
        {/* Confidence Threshold */}
        <div className="flex flex-col gap-2">
          <div className="flex items-center justify-between">
            <label className="text-xs text-muted-foreground">Confidence Threshold</label>
            <span className="font-mono text-xs text-primary">{confidenceThreshold.toFixed(2)}</span>
          </div>
          <Slider
            value={[confidenceThreshold]}
            onValueChange={([val]) => onConfidenceChange(val)}
            min={0.1}
            max={1.0}
            step={0.05}
            className="w-full"
          />
        </div>

        {/* Model Selector */}
        <div className="flex flex-col gap-2">
          <label className="text-xs text-muted-foreground">Detection Model</label>
          <Select value={model} onValueChange={(v) => onModelChange(v as ModelType)}>
            <SelectTrigger className="h-8 bg-secondary text-sm">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="YOLOv8n">YOLOv8n (Nano)</SelectItem>
              <SelectItem value="YOLOv8s">YOLOv8s (Small)</SelectItem>
              <SelectItem value="YOLOv8m">YOLOv8m (Medium)</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Grid Size */}
        <div className="flex flex-col gap-2">
          <label className="text-xs text-muted-foreground">Density Grid</label>
          <Select value={gridSize} onValueChange={(v) => onGridSizeChange(v as GridSize)}>
            <SelectTrigger className="h-8 bg-secondary text-sm">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="2x2">2 x 2</SelectItem>
              <SelectItem value="3x3">3 x 3</SelectItem>
              <SelectItem value="4x4">4 x 4</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Export */}
        <Button variant="outline" size="sm" onClick={exportCSV} className="w-full gap-2">
          <Download className="h-3.5 w-3.5" />
          Export Data (CSV)
        </Button>
      </CardContent>
    </Card>
  )
}
