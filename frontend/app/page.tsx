"use client"

import { useState, useMemo } from "react"
import { AppSidebar } from "@/components/app-sidebar"
import { DashboardHeader } from "@/components/dashboard-header"
import { VideoFeed } from "@/components/video-feed"
import { StatsCards } from "@/components/stats-cards"
import { ShelfHeatmap } from "@/components/shelf-heatmap"
import { RealtimeChart, FpsChart } from "@/components/realtime-chart"
import { ControlPanel } from "@/components/control-panel"
import { ActivityLog } from "@/components/activity-log"
import { SystemInfo } from "@/components/system-info"
import { useInventoryStream } from "@/hooks/use-inventory-stream"
import { generateDensityMap, generateMockLogs } from "@/lib/mock-data"
import type { GridSize, ModelType } from "@/lib/types"

// ROS Stream Component (import this - you need to create this file)
import { ROSVideoStream } from "@/components/ROSVideoStream"
import { InventoryDashboard } from "@/components/inventory-dashboard"
import { DetectionsTable } from "@/components/detections-table"
import { Detection } from "@/lib/api-client"

export default function DashboardPage() {
  // Controls state
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.25)
  const [model, setModel] = useState<ModelType>("YOLOv8n")
  const [gridSize, setGridSize] = useState<GridSize>("3x3")
  const [activeView, setActiveView] = useState("dashboard")

  // Real-time data from API
  const [liveInventory, setLiveInventory] = useState<any>(null)
  const [liveDetections, setLiveDetections] = useState<Detection[]>([])
  const [liveStats, setLiveStats] = useState<any>(null)

  // Real-time data stream from backend API (inventory only)
  const { currentFrame, timeSeries, connected, framesProcessed } = useInventoryStream({
    useMock: false,
    wsUrl: process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws/inventory',
  })

  // Get Pi IP from environment or use default
  const piIp = process.env.NEXT_PUBLIC_PI_IP || '192.168.1.4'
  const rosStreamPort = parseInt(process.env.NEXT_PUBLIC_ROS_STREAM_PORT || '8080')

  // Generate density map matching grid size selection
  const densityMap = useMemo(() => {
    const [rows, cols] = gridSize.split("x").map(Number)
    if (
      currentFrame.density_map.length === rows &&
      currentFrame.density_map[0]?.length === cols
    ) {
      return currentFrame.density_map
    }
    return generateDensityMap(rows, cols)
  }, [gridSize, currentFrame.density_map])

  const logs = useMemo(() => generateMockLogs(), [])

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Sidebar */}
      <AppSidebar
        activeView={activeView}
        onViewChange={setActiveView}
        connected={connected}
      />

      {/* Main Content */}
      <div className="flex flex-1 flex-col overflow-hidden">
        <DashboardHeader
          title="Inventory Dashboard"
          subtitle="Real-time vision-based inventory monitoring"
        />

        <main className="flex-1 overflow-y-auto p-4 lg:p-6">
          {activeView === "dashboard" && (
            <div className="flex flex-col gap-4 lg:gap-6">
              {/* Stats Row */}
              <StatsCards
                inventory={currentFrame.inventory}
                fps={currentFrame.fps || 0}
                framesProcessed={framesProcessed}
              />

              {/* Main Content: Video + Side Panel */}
              <div className="grid gap-4 lg:grid-cols-5 lg:gap-6">
                {/* Video Feed - Using ROS Stream */}
                <div className="lg:col-span-3">
                  <ROSVideoStream
                    piIp={piIp}
                    port={rosStreamPort}
                  />
                </div>

                {/* Right panel - takes 2/5 */}
                <div className="flex flex-col gap-4 lg:col-span-2 lg:gap-6">
                  <ShelfHeatmap densityMap={densityMap} gridSize={gridSize} />
                  <ControlPanel
                    confidenceThreshold={confidenceThreshold}
                    onConfidenceChange={setConfidenceThreshold}
                    model={model}
                    onModelChange={setModel}
                    gridSize={gridSize}
                    onGridSizeChange={setGridSize}
                    timeSeries={timeSeries}
                  />
                </div>
              </div>

              {/* Charts Row */}
              <div className="grid gap-4 lg:grid-cols-5 lg:gap-6">
                <div className="lg:col-span-3">
                  <RealtimeChart data={timeSeries} />
                </div>
                <div className="lg:col-span-2">
                  <FpsChart data={timeSeries} />
                </div>
              </div>

              {/* Bottom Row: Activity + System */}
              <div className="grid gap-4 lg:grid-cols-5 lg:gap-6">
                <div className="lg:col-span-3">
                  <ActivityLog logs={logs} />
                </div>
                <div className="lg:col-span-2">
                  <SystemInfo
                    connected={connected}
                    model={model}
                    framesProcessed={framesProcessed}
                  />
                </div>
              </div>
            </div>
          )}

          {activeView === "analytics" && (
            <div className="flex flex-col gap-4 lg:gap-6">
              <StatsCards
                inventory={currentFrame.inventory}
                fps={currentFrame.fps || 0}
                framesProcessed={framesProcessed}
              />
              <div className="grid gap-4 lg:grid-cols-2 lg:gap-6">
                <RealtimeChart data={timeSeries} />
                <FpsChart data={timeSeries} />
              </div>
              <div className="grid gap-4 lg:grid-cols-2 lg:gap-6">
                <ShelfHeatmap densityMap={densityMap} gridSize={gridSize} />
                <ActivityLog logs={logs} />
              </div>
            </div>
          )}

          {activeView === "live" && (
            <div className="flex flex-col gap-4 lg:gap-6">
              {/* Live ROS Stream View */}
              <div className="grid gap-4 lg:grid-cols-2 lg:gap-6">
                {/* Live Video Stream from ROS */}
                <ROSVideoStream
                  piIp={piIp}
                  port={rosStreamPort}
                />

                {/* Live Inventory from API */}
                <InventoryDashboard
                  inventory={currentFrame.inventory}
                  detections={currentFrame.detections}
                />
              </div>

              {/* Detections Table */}
              <div className="grid gap-4 lg:grid-cols-2 lg:gap-6">
                <DetectionsTable 
                  detections={currentFrame.detections.map(d => ({
                    bbox: d.bbox,
                    confidence: d.confidence,
                    class_id: d.class_id,
                    class_name: d.class_name,
                    center: d.center
                  }))} 
                  maxDisplay={20} 
                />
                
                {/* System Stats */}
                <SystemInfo
                  connected={connected}
                  model={model}
                  framesProcessed={framesProcessed}
                />
              </div>
            </div>
          )}

          {activeView === "cameras" && (
            <div className="flex flex-col gap-4 lg:gap-6">
              <div className="grid gap-4 lg:grid-cols-2">
                <ROSVideoStream piIp={piIp} port={rosStreamPort} />
                <ROSVideoStream piIp={piIp} port={rosStreamPort} />
              </div>
              <div className="grid gap-4 lg:grid-cols-2">
                <ROSVideoStream piIp={piIp} port={rosStreamPort} />
                <ROSVideoStream piIp={piIp} port={rosStreamPort} />
              </div>
            </div>
          )}

          {activeView === "settings" && (
            <div className="mx-auto max-w-xl">
              <div className="flex flex-col gap-4 lg:gap-6">
                <ControlPanel
                  confidenceThreshold={confidenceThreshold}
                  onConfidenceChange={setConfidenceThreshold}
                  model={model}
                  onModelChange={setModel}
                  gridSize={gridSize}
                  onGridSizeChange={setGridSize}
                  timeSeries={timeSeries}
                />
                <SystemInfo
                  connected={connected}
                  model={model}
                  framesProcessed={framesProcessed}
                />
                
                {/* ROS Stream Info Card */}
                <div className="rounded-lg border border-border bg-card p-4">
                  <h3 className="text-sm font-medium mb-2">📹 ROS Stream Configuration</h3>
                  <div className="space-y-1 text-xs text-muted-foreground">
                    <p>Stream URL: <code className="text-primary">http://{piIp}:{rosStreamPort}/stream.mjpg</code></p>
                    <p>Status: {connected ? '🟢 Connected' : '🔴 Disconnected'}</p>
                    <p>Frames: {framesProcessed}</p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  )
}