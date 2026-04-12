import { NextResponse } from "next/server"
import { generateInitialTimeSeries } from "@/lib/mock-data"

/**
 * GET /api/inventory/history
 * Returns historical inventory data for chart display.
 * In production, this would query a time-series database.
 */
export async function GET() {
  const history = generateInitialTimeSeries()

  return NextResponse.json({
    success: true,
    data: history,
    count: history.length,
    timestamp: new Date().toISOString(),
  })
}
