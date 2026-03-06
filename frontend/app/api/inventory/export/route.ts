import { NextResponse } from "next/server"

/**
 * GET /api/inventory/export
 * Exports inventory data as CSV.
 * In production, this would read from the actual database.
 */
export async function GET() {
  const { generateInitialTimeSeries } = await import("@/lib/mock-data")
  const data = generateInitialTimeSeries()

  const headers = "timestamp,time,total_objects,density_score,fps\n"
  const rows = data
    .map(
      (p) =>
        `${new Date(p.timestamp).toISOString()},${p.time},${p.total_objects},${p.density_score.toFixed(2)},${p.fps.toFixed(1)}`
    )
    .join("\n")

  const csv = headers + rows

  return new NextResponse(csv, {
    headers: {
      "Content-Type": "text/csv",
      "Content-Disposition": `attachment; filename="inventory-export-${new Date().toISOString().slice(0, 10)}.csv"`,
    },
  })
}
