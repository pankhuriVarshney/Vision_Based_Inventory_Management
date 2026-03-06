'use client';

import React, { useRef, useEffect } from 'react';
import { Detection } from '@/lib/api-client';

interface DetectionOverlayProps {
  detections: Detection[];
  imageWidth?: number;
  imageHeight?: number;
  showLabels?: boolean;
  showConfidence?: boolean;
}

export function DetectionOverlay({
  detections,
  imageWidth = 640,
  imageHeight = 480,
  showLabels = true,
  showConfidence = true,
}: DetectionOverlayProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw detections
    detections.forEach((detection, index) => {
      const [x1, y1, x2, y2] = detection.bbox;
      const confidence = detection.confidence;
      const className = detection.class_name;

      // Generate color based on class ID
      const colors = [
        '#00FF00', // Green
        '#FF0000', // Red
        '#0000FF', // Blue
        '#FFFF00', // Yellow
        '#FF00FF', // Magenta
        '#00FFFF', // Cyan
      ];
      const color = colors[detection.class_id % colors.length];

      // Draw bounding box
      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);

      // Draw label background
      if (showLabels) {
        const label = showConfidence
          ? `${className}: ${(confidence * 100).toFixed(0)}%`
          : className;

        ctx.font = '12px Arial';
        const textWidth = ctx.measureText(label).width;
        const labelHeight = 20;

        // Draw background
        ctx.fillStyle = color;
        ctx.fillRect(x1, y1 - labelHeight, textWidth + 8, labelHeight);

        // Draw text
        ctx.fillStyle = '#000000';
        ctx.fillText(label, x1 + 4, y1 - 5);
      }

      // Draw center point
      const [cx, cy] = detection.center;
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.arc(cx, cy, 3, 0, Math.PI * 2);
      ctx.fill();
    });
  }, [detections, imageWidth, imageHeight, showLabels, showConfidence]);

  return (
    <canvas
      ref={canvasRef}
      width={imageWidth}
      height={imageHeight}
      className="absolute inset-0 pointer-events-none"
      style={{ position: 'absolute', top: 0, left: 0 }}
    />
  );
}

export default DetectionOverlay;
