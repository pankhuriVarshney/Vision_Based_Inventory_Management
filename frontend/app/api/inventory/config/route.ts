import { NextRequest, NextResponse } from "next/server"

/**
 * POST /api/inventory/config
 * Updates the detection configuration.
 * In production, this would forward configuration to the Raspberry Pi backend.
 */
export async function POST(request: NextRequest) {
  const body = await request.json()

  const { confidence_threshold, model, grid_size } = body

  // Validate inputs
  if (confidence_threshold !== undefined && (confidence_threshold < 0.1 || confidence_threshold > 1.0)) {
    return NextResponse.json(
      { success: false, error: "confidence_threshold must be between 0.1 and 1.0" },
      { status: 400 }
    )
  }

  const validModels = ["YOLOv8n", "YOLOv8s", "YOLOv8m"]
  if (model && !validModels.includes(model)) {
    return NextResponse.json(
      { success: false, error: `model must be one of: ${validModels.join(", ")}` },
      { status: 400 }
    )
  }

  const validGrids = ["2x2", "3x3", "4x4"]
  if (grid_size && !validGrids.includes(grid_size)) {
    return NextResponse.json(
      { success: false, error: `grid_size must be one of: ${validGrids.join(", ")}` },
      { status: 400 }
    )
  }

  // In production: forward to the RPi backend via fetch or WebSocket
  // await fetch('http://<rpi-ip>:8000/config', { method: 'POST', body: JSON.stringify(body) })

  return NextResponse.json({
    success: true,
    message: "Configuration updated",
    config: {
      confidence_threshold: confidence_threshold ?? 0.25,
      model: model ?? "YOLOv8n",
      grid_size: grid_size ?? "3x3",
    },
    timestamp: new Date().toISOString(),
  })
}

/**
 * GET /api/inventory/config
 * Returns current configuration.
 */
export async function GET() {
  return NextResponse.json({
    success: true,
    config: {
      confidence_threshold: 0.25,
      model: "YOLOv8n",
      grid_size: "3x3",
      device: "Raspberry Pi 5",
      backend_url: "ws://localhost:8000/ws",
      video_url: "http://localhost:8000/video_feed",
    },
    timestamp: new Date().toISOString(),
  })
}
