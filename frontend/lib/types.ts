export interface Detection {
  bbox: [number, number, number, number]
  confidence: number
  class_id: number
  class_name: string
  center: [number, number]
  track_id?: number
}

export interface InventoryData {
  total_objects: number
  class_counts: Record<string, number>
  density_score: number
  coverage_ratio: number
}

export interface FrameData {
  frame_id: number
  timestamp: number
  detections: Detection[]
  inventory: InventoryData
  density_map: number[][]
  fps?: number
}

export interface TimeSeriesPoint {
  time: string
  timestamp: number
  total_objects: number
  density_score: number
  fps: number
}

export interface SystemStatus {
  connected: boolean
  model: string
  device: string
  uptime: number
  framesProcessed: number
}

export type GridSize = "2x2" | "3x3" | "4x4"
export type ModelType = "YOLOv8n" | "YOLOv8s" | "YOLOv8m"
