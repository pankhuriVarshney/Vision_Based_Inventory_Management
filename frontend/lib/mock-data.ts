import type { FrameData, TimeSeriesPoint, Detection } from "./types"

// Static detections matching the shelf-detection.png image (4 items).
// Coordinates are in a 640x480 reference frame.
// These map to the 4 visible products with green bounding boxes in the image.
export const STATIC_DETECTIONS: Detection[] = [
  {
    // Top-right item (small package)
    bbox: [370, 30, 530, 175],
    confidence: 0.89,
    class_id: 0,
    class_name: "item",
    center: [450, 102],
    track_id: 1,
  },
  {
    // Center item (wrapped product)
    bbox: [185, 115, 380, 290],
    confidence: 0.93,
    class_id: 0,
    class_name: "item",
    center: [282, 202],
    track_id: 2,
  },
  {
    // Bottom-left item (can / cylindrical)
    bbox: [55, 240, 225, 435],
    confidence: 0.93,
    class_id: 0,
    class_name: "item",
    center: [140, 337],
    track_id: 3,
  },
  {
    // Bottom-right item (flat package)
    bbox: [310, 270, 540, 420],
    confidence: 0.92,
    class_id: 0,
    class_name: "item",
    center: [425, 345],
    track_id: 4,
  },
]

// Generate density map for given grid size (low values since we only have 4 items)
export function generateDensityMap(rows: number, cols: number): number[][] {
  const map: number[][] = []
  for (let r = 0; r < rows; r++) {
    const row: number[] = []
    for (let c = 0; c < cols; c++) {
      row.push(Math.floor(Math.random() * 3))
    }
    map.push(row)
  }
  return map
}

// Generate a single frame of data (keeps the same 4 detections, just varies FPS slightly)
export function generateMockFrame(frameId: number): FrameData {
  return {
    frame_id: frameId,
    timestamp: Date.now() / 1000,
    detections: STATIC_DETECTIONS,
    inventory: {
      total_objects: 4,
      class_counts: { item: 4 },
      density_score: 2.1,
      coverage_ratio: 0.42,
    },
    density_map: generateDensityMap(3, 3),
    fps: Math.random() * 2 + 23,
  }
}

// Generate initial time series data (last 60 seconds)
export function generateInitialTimeSeries(): TimeSeriesPoint[] {
  const points: TimeSeriesPoint[] = []
  const now = Date.now()

  for (let i = 59; i >= 0; i--) {
    const timestamp = now - i * 1000
    const date = new Date(timestamp)
    points.push({
      time: `${date.getMinutes().toString().padStart(2, "0")}:${date.getSeconds().toString().padStart(2, "0")}`,
      timestamp,
      total_objects: 4 + Math.round(Math.random() * 2 - 1), // 3-5 range to stay realistic
      density_score: 2.0 + Math.random() * 0.4,
      fps: Math.random() * 2 + 23,
    })
  }

  return points
}

// Initial mock frame
export const INITIAL_FRAME: FrameData = {
  frame_id: 0,
  timestamp: Date.now() / 1000,
  detections: STATIC_DETECTIONS,
  inventory: {
    total_objects: 4,
    class_counts: { item: 4 },
    density_score: 2.1,
    coverage_ratio: 0.42,
  },
  density_map: [
    [1, 2, 1],
    [0, 1, 2],
    [1, 0, 1],
  ],
  fps: 24.5,
}

// Detection log entries for the activity feed
export interface DetectionLogEntry {
  id: string
  timestamp: number
  type: "detection" | "alert" | "system"
  message: string
  severity: "info" | "warning" | "critical"
}

export function generateMockLogs(): DetectionLogEntry[] {
  const now = Date.now()
  return [
    {
      id: "1",
      timestamp: now - 2000,
      type: "detection",
      message: "4 items detected on shelf (conf: 0.89-0.93)",
      severity: "info",
    },
    {
      id: "2",
      timestamp: now - 5000,
      type: "system",
      message: "YOLOv8n model loaded successfully on CPU",
      severity: "info",
    },
    {
      id: "3",
      timestamp: now - 8000,
      type: "system",
      message: "Model inference latency: 42ms avg",
      severity: "info",
    },
    {
      id: "4",
      timestamp: now - 12000,
      type: "detection",
      message: "Item tracked: ID 3 position stable (Zone B1)",
      severity: "info",
    },
    {
      id: "5",
      timestamp: now - 20000,
      type: "alert",
      message: "Low item count in Zone A1 - restocking recommended",
      severity: "warning",
    },
    {
      id: "6",
      timestamp: now - 30000,
      type: "system",
      message: "WebSocket connection established",
      severity: "info",
    },
    {
      id: "7",
      timestamp: now - 45000,
      type: "detection",
      message: "New item placed on shelf (tracking ID: 4, conf: 0.92)",
      severity: "info",
    },
    {
      id: "8",
      timestamp: now - 60000,
      type: "system",
      message: "Camera feed initialized at 640x480 resolution",
      severity: "info",
    },
  ]
}
