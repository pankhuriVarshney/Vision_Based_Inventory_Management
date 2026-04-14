// frontend/hooks/use-inventory-stream.ts
import { useState, useEffect, useRef, useCallback } from 'react';
import { FrameData, TimeSeriesPoint } from '@/lib/types';
import { generateMockFrame, generateInitialTimeSeries } from '@/lib/mock-data';

interface UseInventoryStreamProps {
  useMock?: boolean;
  wsUrl?: string;
}

export function useInventoryStream({ 
  useMock = false, 
  wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws/inventory'
}: UseInventoryStreamProps) {
  const [currentFrame, setCurrentFrame] = useState<FrameData>(() => generateMockFrame(0));
  const [timeSeries, setTimeSeries] = useState<TimeSeriesPoint[]>(() => generateInitialTimeSeries());
  const [connected, setConnected] = useState(false);
  const [framesProcessed, setFramesProcessed] = useState(0);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();

  const connectWebSocket = useCallback(() => {
    if (useMock) {
      // Mock mode - simulate data
      const interval = setInterval(() => {
        setCurrentFrame(generateMockFrame(Date.now()));
        setFramesProcessed(prev => prev + 1);
        setConnected(true);
      }, 100);
      return () => clearInterval(interval);
    }

    // Real WebSocket connection
    console.log(`Connecting to WebSocket: ${wsUrl}`);
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('✅ WebSocket connected to backend');
      setConnected(true);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.success && data.frame) {
          // Convert backend frame format to frontend FrameData
          const frame: FrameData = {
            frame_id: data.frame.frame_id || framesProcessed,
            timestamp: data.frame.timestamp || Date.now() / 1000,
            detections: data.frame.detections?.map((d: any) => ({
              bbox: d.bbox,
              confidence: d.confidence,
              class_id: d.class_id,
              class_name: d.class_name,
              center: d.center || [(d.bbox[0] + d.bbox[2]) / 2, (d.bbox[1] + d.bbox[3]) / 2],
            })) || [],
            inventory: data.frame.inventory || {
              total_objects: 0,
              class_counts: {},
              density_score: 0,
              coverage_ratio: 0,
            },
            density_map: data.frame.density_map || [[0]],
            fps: data.frame.fps || 0,
          };
          
          setCurrentFrame(frame);
          setFramesProcessed(prev => prev + 1);
          
          // Update time series
          setTimeSeries(prev => {
            const newPoint: TimeSeriesPoint = {
              time: new Date().toLocaleTimeString().slice(0, 5),
              timestamp: Date.now(),
              total_objects: frame.inventory.total_objects,
              density_score: frame.inventory.density_score,
              fps: frame.fps || 0,
            };
            const updated = [...prev.slice(-59), newPoint];
            return updated;
          });
        } else if (data.inventory) {
          // Handle inventory-only updates
          setCurrentFrame(prev => ({
            ...prev,
            inventory: data.inventory,
            timestamp: Date.now() / 1000,
          }));
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setConnected(false);
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected, attempting reconnect...');
      setConnected(false);
      
      // Attempt reconnect after 3 seconds
      reconnectTimeoutRef.current = setTimeout(() => {
        connectWebSocket();
      }, 3000);
    };

    return () => {
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [useMock, wsUrl, framesProcessed]);

  useEffect(() => {
    const cleanup = connectWebSocket();
    return () => {
      if (cleanup) cleanup();
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (wsRef.current) wsRef.current.close();
    };
  }, [connectWebSocket]);

  return {
    currentFrame,
    timeSeries,
    connected,
    framesProcessed,
  };
}