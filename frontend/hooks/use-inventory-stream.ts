// frontend/hooks/use-inventory-stream.ts
import { useState, useEffect, useRef, useCallback } from 'react';
import { FrameData, TimeSeriesPoint } from '@/lib/types';

interface UseInventoryStreamProps {
  useMock?: boolean;
  wsUrl?: string;
  refreshInterval?: number;
}

export function useInventoryStream({ 
  useMock = false, 
  wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://192.168.1.4:8000/ws/inventory',
  refreshInterval = 5000
}: UseInventoryStreamProps) {
  const [currentFrame, setCurrentFrame] = useState<FrameData>({
    frame_id: 0,
    timestamp: Date.now() / 1000,
    detections: [],
    inventory: {
      total_objects: 0,
      class_counts: {},
      density_score: 0,
      coverage_ratio: 0,
    },
    density_map: [[0,0,0], [0,0,0], [0,0,0]],
    fps: 0,
  });
  const [timeSeries, setTimeSeries] = useState<TimeSeriesPoint[]>([]);
  const [connected, setConnected] = useState(false);
  const [framesProcessed, setFramesProcessed] = useState(0);
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const timeSeriesRef = useRef<TimeSeriesPoint[]>([]);
  const mountedRef = useRef(true);

  // Initialize time series
  useEffect(() => {
    const initialPoints: TimeSeriesPoint[] = [];
    const now = Date.now();
    for (let i = 59; i >= 0; i--) {
      const timestamp = now - i * 1000;
      const date = new Date(timestamp);
      initialPoints.push({
        time: `${date.getMinutes().toString().padStart(2, "0")}:${date.getSeconds().toString().padStart(2, "0")}`,
        timestamp,
        total_objects: 0,
        density_score: 0,
        fps: 0,
      });
    }
    setTimeSeries(initialPoints);
    timeSeriesRef.current = initialPoints;
  }, []);

  const updateTimeSeries = useCallback((totalObjects: number, densityScore: number, fps: number) => {
    const now = Date.now();
    const date = new Date(now);
    const newPoint: TimeSeriesPoint = {
      time: `${date.getMinutes().toString().padStart(2, "0")}:${date.getSeconds().toString().padStart(2, "0")}`,
      timestamp: now,
      total_objects: totalObjects,
      density_score: densityScore,
      fps: fps,
    };
    
    const updatedSeries = [...timeSeriesRef.current.slice(1), newPoint];
    timeSeriesRef.current = updatedSeries;
    setTimeSeries(updatedSeries);
  }, []);

  const connectWebSocket = useCallback(() => {
    if (!mountedRef.current) return;
    
    // Close existing connection if any
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      return; // Already connected
    }

    console.log('📡 Connecting to WebSocket...');
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      if (!mountedRef.current) return;
      console.log('✅ WebSocket connected');
      setConnected(true);
    };

    ws.onmessage = (event) => {
      if (!mountedRef.current) return;
      try {
        const data = JSON.parse(event.data);
        
        const frameData: FrameData = {
          frame_id: framesProcessed + 1,
          timestamp: Date.now() / 1000,
          detections: data.detections || [],
          inventory: {
            total_objects: data.total_objects || 0,
            class_counts: data.class_counts || {},
            density_score: data.density_score || 0,
            coverage_ratio: (data.total_objects || 0) / 100,
          },
          density_map: generateDensityMap(data.total_objects || 0),
          fps: 1,
        };
        
        setCurrentFrame(frameData);
        setFramesProcessed(prev => prev + 1);
        
        updateTimeSeries(
          frameData.inventory.total_objects,
          frameData.inventory.density_score,
          1
        );
      } catch (error) {
        console.error('Error parsing WebSocket data:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('❌ WebSocket error:', error);
      setConnected(false);
    };

    ws.onclose = () => {
      if (!mountedRef.current) return;
      console.log('⚠️ WebSocket disconnected, reconnecting in 10s...');
      setConnected(false);
      
      // Clear any existing reconnect timeout
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      
      // Reconnect after delay
      reconnectTimeoutRef.current = setTimeout(() => {
        if (mountedRef.current) {
          connectWebSocket();
        }
      }, 10000); // 10 second reconnect delay
    };
  }, [wsUrl, framesProcessed, updateTimeSeries]);

  useEffect(() => {
    mountedRef.current = true;
    
    if (!useMock) {
      connectWebSocket();
    }
    
    return () => {
      mountedRef.current = false;
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [useMock, connectWebSocket]);

  // Poll REST API as fallback (but less frequently)
  useEffect(() => {
    if (useMock) return;

    const fetchInventory = async () => {
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://192.168.1.4:8000'}/api/inventory/count`);
        const data = await response.json();
        if (data.success && data.data?.current?.current_count !== undefined) {
          setCurrentFrame(prev => ({
            ...prev,
            inventory: {
              ...prev.inventory,
              total_objects: data.data.current.current_count,
            },
          }));
        }
      } catch (error) {
        console.error('REST API error:', error);
      }
    };

    // Poll every 10 seconds instead of 2
    const interval = setInterval(fetchInventory, 10000);
    return () => clearInterval(interval);
  }, [useMock]);

  return {
    currentFrame,
    timeSeries,
    connected,
    framesProcessed,
  };
}

function generateDensityMap(itemCount: number): number[][] {
  if (itemCount === 0) return [[0,0,0], [0,0,0], [0,0,0]];
  if (itemCount <= 2) return [[0,1,0], [0,0,0], [0,0,0]];
  if (itemCount <= 5) return [[1,1,0], [0,1,0], [0,0,0]];
  return [[2,2,1], [1,2,1], [0,1,1]];
}