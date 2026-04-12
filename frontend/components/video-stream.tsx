'use client';

import React, { useRef, useEffect, useState, useCallback } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { apiClient, VideoFrame, Detection } from '@/lib/api-client';
import { Play, Square, Wifi, WifiOff } from 'lucide-react';

interface VideoStreamProps {
  source?: string;
  onDetectionUpdate?: (detections: Detection[]) => void;
  onInventoryUpdate?: (inventory: any) => void;
  onStatsUpdate?: (stats: any) => void;
}

export function VideoStream({
  source = '0',
  onDetectionUpdate,
  onInventoryUpdate,
  onStatsUpdate,
}: VideoStreamProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fps, setFps] = useState(0);
  const [latency, setLatency] = useState(0);
  const [frameCount, setFrameCount] = useState(0);
  const disconnectRef = useRef<(() => void) | null>(null);

  const connect = useCallback(() => {
    setError(null);
    
    try {
      disconnectRef.current = apiClient.connectVideoStream(
        source,
        (frame: VideoFrame) => {
          // Update connection status
          setIsConnected(true);
          setIsStreaming(true);
          
          // Draw frame to canvas
          if (canvasRef.current && frame.frame) {
            const canvas = canvasRef.current;
            const ctx = canvas.getContext('2d');
            
            if (ctx) {
              const img = new Image();
              img.onload = () => {
                canvas.width = img.width;
                canvas.height = img.height;
                ctx.drawImage(img, 0, 0);
              };
              img.src = `data:image/jpeg;base64,${frame.frame}`;
            }
          }
          
          // Update stats
          setFps(frame.stats.fps);
          setLatency(frame.stats.latency_ms);
          setFrameCount(frame.stats.frame_count);
          
          // Callbacks
          if (onDetectionUpdate) {
            onDetectionUpdate(frame.detections);
          }
          
          if (onInventoryUpdate) {
            onInventoryUpdate(frame.inventory);
          }
          
          if (onStatsUpdate) {
            onStatsUpdate({
              fps: frame.stats.fps,
              latency: frame.stats.latency_ms,
              frameCount: frame.stats.frame_count,
            });
          }
        },
        (errorMsg: string) => {
          setError(errorMsg);
          setIsConnected(false);
        },
        () => {
          setIsConnected(false);
          setIsStreaming(false);
        }
      );
    } catch (err: any) {
      setError(err.message || 'Failed to connect');
      setIsConnected(false);
    }
  }, [source, onDetectionUpdate, onInventoryUpdate, onStatsUpdate]);

  const disconnect = useCallback(() => {
    if (disconnectRef.current) {
      disconnectRef.current();
      disconnectRef.current = null;
    }
    setIsStreaming(false);
    setIsConnected(false);
  }, []);

  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  const handleToggle = () => {
    if (isStreaming) {
      disconnect();
    } else {
      connect();
    }
  };

  return (
    <Card className="w-full">
      <CardContent className="p-4">
        <div className="relative">
          {/* Video Canvas */}
          <canvas
            ref={canvasRef}
            className="w-full h-auto bg-black rounded-lg"
            style={{ maxHeight: '480px' }}
          />
          
          {/* Connection Status */}
          <div className="absolute top-2 left-2">
            <Badge variant={isConnected ? 'default' : 'destructive'}>
              {isConnected ? (
                <>
                  <Wifi className="w-3 h-3 mr-1" />
                  Live
                </>
              ) : (
                <>
                  <WifiOff className="w-3 h-3 mr-1" />
                  Disconnected
                </>
              )}
            </Badge>
          </div>
          
          {/* Stats Overlay */}
          {isConnected && (
            <div className="absolute top-2 right-2 flex gap-2">
              <Badge variant="secondary">
                FPS: {fps.toFixed(1)}
              </Badge>
              <Badge variant="secondary">
                Latency: {latency.toFixed(0)}ms
              </Badge>
            </div>
          )}
          
          {/* Error Display */}
          {error && (
            <div className="absolute inset-0 flex items-center justify-center bg-black/50 rounded-lg">
              <div className="text-red-500 text-center p-4">
                <p className="font-bold">Connection Error</p>
                <p className="text-sm">{error}</p>
              </div>
            </div>
          )}
          
          {/* Not Streaming Placeholder */}
          {!isStreaming && !error && (
            <div className="absolute inset-0 flex items-center justify-center bg-black/50 rounded-lg">
              <div className="text-white text-center">
                <Play className="w-12 h-12 mx-auto mb-2 opacity-50" />
                <p>Click Start to begin streaming</p>
              </div>
            </div>
          )}
        </div>
        
        {/* Controls */}
        <div className="mt-4 flex justify-center">
          <Button
            onClick={handleToggle}
            variant={isStreaming ? 'destructive' : 'default'}
            size="lg"
          >
            {isStreaming ? (
              <>
                <Square className="w-4 h-4 mr-2" />
                Stop Stream
              </>
            ) : (
              <>
                <Play className="w-4 h-4 mr-2" />
                Start Stream
              </>
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

export default VideoStream;
