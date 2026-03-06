import { NextResponse } from "next/server"
import { generateMockFrame } from "@/lib/mock-data"

/**
 * GET /api/inventory/current
 * Returns the current inventory snapshot.
 * In production, this would read from the actual detection backend or database.
 */
export async function GET() {
  const frame = generateMockFrame(Math.floor(Math.random() * 10000))

  return NextResponse.json({
    success: true,
    data: frame,
    timestamp: new Date().toISOString(),
  })
}
