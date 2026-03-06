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

// New API-connected components
import { VideoStream } from "@/components/video-stream"
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

  // Real-time data stream (uses mock by default)
  // To connect to real backend, set useMock=false and provide wsUrl:
  // { useMock: false, wsUrl: "ws://localhost:8000/ws" }
  const { currentFrame, timeSeries, connected, framesProcessed } = useInventoryStream({
    useMock: true,
  })

  // Generate density map matching grid size selection
  const densityMap = useMemo(() => {
    const [rows, cols] = gridSize.split("x").map(Number)
    // Use frame density map if it matches, otherwise generate
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
                {/* Video Feed - takes 3/5 */}
                <div className="lg:col-span-3">
                  <VideoFeed
                    detections={currentFrame.detections}
                    fps={currentFrame.fps || 0}
                    connected={connected}
                    confidenceThreshold={confidenceThreshold}
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
              {/* Live API Stream View - Real-time from backend */}
              <div className="grid gap-4 lg:grid-cols-2 lg:gap-6">
                {/* Live Video Stream */}
                <VideoStream
                  source="0"
                  onDetectionUpdate={setLiveDetections}
                  onInventoryUpdate={setLiveInventory}
                  onStatsUpdate={setLiveStats}
                />

                {/* Live Inventory */}
                <InventoryDashboard
                  inventory={liveInventory}
                  detections={liveDetections}
                />
              </div>

              {/* Detections Table */}
              <div className="grid gap-4 lg:grid-cols-2 lg:gap-6">
                <DetectionsTable detections={liveDetections} maxDisplay={20} />
                
                {/* System Stats */}
                {liveStats && (
                  <SystemInfo
                    connected={true}
                    model={model}
                    framesProcessed={liveStats.frameCount || 0}
                  />
                )}
              </div>
            </div>
          )}

          {activeView === "cameras" && (
            <div className="flex flex-col gap-4 lg:gap-6">
              <div className="grid gap-4 lg:grid-cols-2">
                <VideoFeed
                  detections={currentFrame.detections}
                  fps={currentFrame.fps || 0}
                  connected={connected}
                  confidenceThreshold={confidenceThreshold}
                />
                <VideoFeed
                  detections={[]}
                  fps={0}
                  connected={false}
                  confidenceThreshold={confidenceThreshold}
                />
              </div>
              <div className="grid gap-4 lg:grid-cols-2">
                <VideoFeed
                  detections={[]}
                  fps={0}
                  connected={false}
                  confidenceThreshold={confidenceThreshold}
                />
                <VideoFeed
                  detections={[]}
                  fps={0}
                  connected={false}
                  confidenceThreshold={confidenceThreshold}
                />
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
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
