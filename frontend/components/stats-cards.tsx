"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Package, Gauge, LayoutGrid, TrendingUp, Cpu, Clock } from "lucide-react"
import { useEffect, useState } from "react"
import type { InventoryData } from "@/lib/types"

interface StatsCardsProps {
  inventory: InventoryData
  fps: number
  framesProcessed: number
}

function AnimatedNumber({ value, decimals = 0 }: { value: number; decimals?: number }) {
  const [display, setDisplay] = useState(value)

  useEffect(() => {
    const start = display
    const diff = value - start
    const duration = 500
    const startTime = performance.now()

    const animate = (time: number) => {
      const elapsed = time - startTime
      const progress = Math.min(elapsed / duration, 1)
      const eased = 1 - Math.pow(1 - progress, 3)
      setDisplay(start + diff * eased)
      if (progress < 1) requestAnimationFrame(animate)
    }

    requestAnimationFrame(animate)
  }, [value])

  return <span>{decimals > 0 ? display.toFixed(decimals) : Math.round(display)}</span>
}

function DensityGauge({ score }: { score: number }) {
  const percentage = (score / 10) * 100
  const getColor = () => {
    if (score < 3) return "text-success"
    if (score < 6) return "text-warning"
    return "text-destructive"
  }
  const getBarColor = () => {
    if (score < 3) return "bg-success"
    if (score < 6) return "bg-warning"
    return "bg-destructive"
  }

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-baseline justify-between">
        <span className={`font-mono text-2xl font-bold ${getColor()}`}>
          <AnimatedNumber value={score} decimals={1} />
        </span>
        <span className="text-xs text-muted-foreground">/ 10</span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-secondary">
        <div
          className={`h-full rounded-full ${getBarColor()} transition-all duration-500`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  )
}

export function StatsCards({ inventory, fps, framesProcessed }: StatsCardsProps) {
  const stats = [
    {
      label: "Total Items",
      value: inventory.total_objects,
      icon: Package,
      decimals: 0,
      accent: "text-primary",
      bgAccent: "bg-primary/10",
    },
    {
      label: "Coverage",
      value: inventory.coverage_ratio * 100,
      suffix: "%",
      icon: LayoutGrid,
      decimals: 1,
      accent: "text-chart-2",
      bgAccent: "bg-chart-2/10",
    },
    {
      label: "Inference FPS",
      value: fps,
      icon: Cpu,
      decimals: 1,
      accent: "text-chart-3",
      bgAccent: "bg-chart-3/10",
    },
    {
      label: "Frames",
      value: framesProcessed,
      icon: Clock,
      decimals: 0,
      accent: "text-chart-4",
      bgAccent: "bg-chart-4/10",
    },
  ]

  return (
    <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
      {stats.map((stat) => {
        const Icon = stat.icon
        return (
          <Card key={stat.label} className="border-border bg-card">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-muted-foreground">{stat.label}</span>
                <div className={`rounded-md p-1.5 ${stat.bgAccent}`}>
                  <Icon className={`h-3.5 w-3.5 ${stat.accent}`} />
                </div>
              </div>
              <div className="mt-2 flex items-baseline gap-1">
                <span className={`font-mono text-2xl font-bold ${stat.accent}`}>
                  <AnimatedNumber value={stat.value} decimals={stat.decimals} />
                </span>
                {stat.suffix && (
                  <span className="text-sm text-muted-foreground">{stat.suffix}</span>
                )}
              </div>
            </CardContent>
          </Card>
        )
      })}

      {/* Density Score Card - special */}
      <Card className="border-border bg-card lg:col-span-2">
        <CardHeader className="pb-2">
          <div className="flex items-center gap-2">
            <Gauge className="h-4 w-4 text-primary" />
            <CardTitle className="text-sm font-medium text-card-foreground">Density Score</CardTitle>
          </div>
        </CardHeader>
        <CardContent className="pt-0">
          <DensityGauge score={inventory.density_score} />
        </CardContent>
      </Card>

      {/* Class Breakdown Card */}
      <Card className="border-border bg-card lg:col-span-2">
        <CardHeader className="pb-2">
          <div className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-primary" />
            <CardTitle className="text-sm font-medium text-card-foreground">Class Breakdown</CardTitle>
          </div>
        </CardHeader>
        <CardContent className="pt-0">
          <div className="flex flex-col gap-2">
            {Object.entries(inventory.class_counts)
              .sort(([, a], [, b]) => b - a)
              .map(([name, count]) => {
                const max = Math.max(...Object.values(inventory.class_counts))
                const pct = (count / max) * 100
                return (
                  <div key={name} className="flex items-center gap-3">
                    <span className="w-16 text-xs text-muted-foreground capitalize">{name}</span>
                    <div className="flex-1">
                      <div className="h-2 w-full overflow-hidden rounded-full bg-secondary">
                        <div
                          className="h-full rounded-full bg-primary transition-all duration-500"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                    <span className="w-8 text-right font-mono text-xs text-foreground">{count}</span>
                  </div>
                )
              })}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
