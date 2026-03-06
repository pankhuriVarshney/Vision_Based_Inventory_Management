"use client"

import { useEffect, useRef, useState } from "react"
import type { Detection } from "@/lib/types"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Pause, Play, Maximize2, Video } from "lucide-react"

interface VideoFeedProps {
  detections: Detection[]
  fps: number
  connected: boolean
  /** Set to your MJPEG endpoint, e.g. "http://localhost:8000/video_feed" */
  videoUrl?: string
  confidenceThreshold: number
}

export function VideoFeed({
  detections,
  fps,
  connected,
  videoUrl,
  confidenceThreshold,
}: VideoFeedProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const imageRef = useRef<HTMLImageElement | null>(null)
  const [paused, setPaused] = useState(false)
  const [imageLoaded, setImageLoaded] = useState(false)
  const animationRef = useRef<number>(0)

  // Load the shelf detection image once
  useEffect(() => {
    if (videoUrl) return // skip if using real video
    const img = new Image()
    img.crossOrigin = "anonymous"
    img.onload = () => {
      imageRef.current = img
      setImageLoaded(true)
    }
    img.src = "/images/shelf-detection.png"
  }, [videoUrl])

  // Draw the shelf image + bounding boxes
  useEffect(() => {
    if (paused || videoUrl) return
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext("2d")
    if (!ctx) return

    const draw = () => {
      const w = canvas.width
      const h = canvas.height

      // Clear
      ctx.fillStyle = "#0f1419"
      ctx.fillRect(0, 0, w, h)

      // Draw the actual shelf image as the background
      if (imageRef.current && imageLoaded) {
        ctx.drawImage(imageRef.current, 0, 0, w, h)
      }

      // Draw bounding boxes for detections above threshold
      const filtered = detections.filter((d) => d.confidence >= confidenceThreshold)
      filtered.forEach((det) => {
        const [x1, y1, x2, y2] = det.bbox
        const bw = x2 - x1
        const bh = y2 - y1

        const color = "#22ff44"

        // Box outline
        ctx.strokeStyle = color
        ctx.lineWidth = 2
        ctx.strokeRect(x1, y1, bw, bh)

        // Label text
        const label = `${det.class_name}: ${det.confidence.toFixed(2)}`
        ctx.font = "bold 13px monospace"
        const metrics = ctx.measureText(label)

        // Label (drawn above box, no background - matches the original image style)
        ctx.fillStyle = color
        ctx.fillText(label, x1 + 4, y1 - 6)

        // Corner accents
        const cornerLen = 10
        ctx.lineWidth = 3
        ctx.strokeStyle = color
        // top-left
        ctx.beginPath()
        ctx.moveTo(x1, y1 + cornerLen)
        ctx.lineTo(x1, y1)
        ctx.lineTo(x1 + cornerLen, y1)
        ctx.stroke()
        // top-right
        ctx.beginPath()
        ctx.moveTo(x2 - cornerLen, y1)
        ctx.lineTo(x2, y1)
        ctx.lineTo(x2, y1 + cornerLen)
        ctx.stroke()
        // bottom-left
        ctx.beginPath()
        ctx.moveTo(x1, y2 - cornerLen)
        ctx.lineTo(x1, y2)
        ctx.lineTo(x1 + cornerLen, y2)
        ctx.stroke()
        // bottom-right
        ctx.beginPath()
        ctx.moveTo(x2 - cornerLen, y2)
        ctx.lineTo(x2, y2)
        ctx.lineTo(x2, y2 - cornerLen)
        ctx.stroke()
        ctx.lineWidth = 2
      })

      // Subtle scanline effect
      const time = Date.now() * 0.001
      const scanY = ((time * 40) % h)
      const gradient = ctx.createLinearGradient(0, scanY - 20, 0, scanY + 20)
      gradient.addColorStop(0, "rgba(34, 255, 68, 0)")
      gradient.addColorStop(0.5, "rgba(34, 255, 68, 0.04)")
      gradient.addColorStop(1, "rgba(34, 255, 68, 0)")
      ctx.fillStyle = gradient
      ctx.fillRect(0, scanY - 20, w, 40)

      animationRef.current = requestAnimationFrame(draw)
    }

    draw()
    return () => cancelAnimationFrame(animationRef.current)
  }, [detections, paused, confidenceThreshold, imageLoaded, videoUrl])

  return (
    <Card className="flex flex-col border-border bg-card">
      <CardHeader className="flex flex-row items-center justify-between pb-3">
        <div className="flex items-center gap-3">
          <Video className="h-4 w-4 text-primary" />
          <CardTitle className="text-sm font-medium text-card-foreground">Live Feed</CardTitle>
          <Badge
            variant="outline"
            className={connected ? "border-success/30 bg-success/10 text-success" : "border-destructive/30 bg-destructive/10 text-destructive"}
          >
            <span className={`mr-1.5 inline-block h-1.5 w-1.5 rounded-full ${connected ? "bg-success animate-pulse" : "bg-destructive"}`} />
            {connected ? "LIVE" : "OFFLINE"}
          </Badge>
        </div>
        <div className="flex items-center gap-2">
          <span className="font-mono text-xs text-muted-foreground">{fps.toFixed(1)} FPS</span>
          <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => setPaused(!paused)}>
            {paused ? <Play className="h-3.5 w-3.5" /> : <Pause className="h-3.5 w-3.5" />}
          </Button>
          <Button variant="ghost" size="icon" className="h-7 w-7">
            <Maximize2 className="h-3.5 w-3.5" />
          </Button>
        </div>
      </CardHeader>
      <CardContent className="flex-1 p-2 pt-0">
        <div className="relative overflow-hidden rounded-md bg-secondary">
          {videoUrl ? (
            /* Replace with real MJPEG stream */
            // eslint-disable-next-line @next/next/no-img-element
            <img src={videoUrl} alt="Live camera feed" className="h-full w-full object-cover" />
          ) : (
            <canvas
              ref={canvasRef}
              width={640}
              height={480}
              className="h-full w-full"
              style={{ imageRendering: "auto" }}
            />
          )}
          {/* Detection count overlay */}
          <div className="absolute bottom-3 left-3 flex items-center gap-2 rounded-md bg-background/80 px-2.5 py-1 backdrop-blur-sm">
            <span className="text-xs font-medium text-primary">
              {detections.filter((d) => d.confidence >= confidenceThreshold).length} detections
            </span>
          </div>
          {/* Timestamp overlay */}
          <div className="absolute bottom-3 right-3 rounded-md bg-background/80 px-2.5 py-1 backdrop-blur-sm">
            <span className="font-mono text-xs text-muted-foreground">
              {new Date().toLocaleTimeString()}
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
