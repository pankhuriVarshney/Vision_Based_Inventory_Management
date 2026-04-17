// frontend/hooks/use-inventory-stream.ts
import { useState, useEffect, useRef, useCallback } from 'react';
import { FrameData, TimeSeriesPoint } from '@/lib/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://192.168.1.4:8000';
const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://192.168.1.4:8000/ws/inventory';

export function useInventoryStream({ 
  useMock = false, 
  refreshInterval = 3000  // Fallback polling interval
}: { 
  useMock?: boolean; 
  refreshInterval?: number;
}) {
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
    density_map: [[0, 0, 0], [0, 0, 0], [0, 0, 0]],
    fps: 0,
  });
  const [timeSeries, setTimeSeries] = useState<TimeSeriesPoint[]>([]);
  const [connected, setConnected] = useState(false);
  const [framesProcessed, setFramesProcessed] = useState(0);
  const [usingWebSocket, setUsingWebSocket] = useState(false);
  
  const timeSeriesRef = useRef<TimeSeriesPoint[]>([]);
  const mountedRef = useRef(true);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();

  // Initialize time series with 60 points
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

  const updateFrame = useCallback((totalObjects: number, densityScore: number, status: string) => {
    setCurrentFrame(prev => ({
      ...prev,
      frame_id: prev.frame_id + 1,
      timestamp: Date.now() / 1000,
      inventory: {
        total_objects: totalObjects,
        class_counts: {},
        density_score: densityScore,
        coverage_ratio: totalObjects / 100,
      },
      density_map: generateDensityMap(totalObjects),
      fps: usingWebSocket ? 10 : 1,
    }));
    
    setFramesProcessed(prev => prev + 1);
    updateTimeSeries(totalObjects, densityScore, usingWebSocket ? 10 : 1);
  }, [updateTimeSeries, usingWebSocket]);

  // WebSocket connection for real-time updates
  const connectWebSocket = useCallback(() => {
    if (!mountedRef.current) return;
    
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      return;
    }

    console.log('📡 Connecting to WebSocket...');
    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => {
      if (!mountedRef.current) return;
      console.log('✅ WebSocket connected');
      setConnected(true);
      setUsingWebSocket(true);
    };

    ws.onmessage = (event) => {
      if (!mountedRef.current) return;
      try {
        const data = JSON.parse(event.data);
        updateFrame(data.total_objects || 0, data.density_score || 0, data.status || 'unknown');
      } catch (error) {
        console.error('Error parsing WebSocket data:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('❌ WebSocket error:', error);
      setConnected(false);
      setUsingWebSocket(false);
    };

    ws.onclose = () => {
      if (!mountedRef.current) return;
      console.log('⚠️ WebSocket disconnected, falling back to HTTP polling...');
      setConnected(false);
      setUsingWebSocket(false);
      
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      
      // Attempt to reconnect WebSocket after 10 seconds
      reconnectTimeoutRef.current = setTimeout(() => {
        if (mountedRef.current) {
          connectWebSocket();
        }
      }, 10000);
    };
  }, [updateFrame]);

  // HTTP polling as fallback
  const fetchInventory = useCallback(async () => {
    if (!mountedRef.current) return;
    
    try {
      const response = await fetch(`${API_URL}/api/inventory/count`);
      if (response.ok) {
        const data = await response.json();
        if (data.success && data.data?.current) {
          const currentCount = data.data.current.current_count || 0;
          const densityScore = data.data.current.density_score || 0;
          const status = data.data.current.status || 'unknown';
          
          updateFrame(currentCount, densityScore, status);
          setConnected(true);
        }
      } else {
        setConnected(false);
      }
    } catch (error) {
      console.error('Fetch error:', error);
      setConnected(false);
    }
  }, [updateFrame]);

  // Initialize connection
  useEffect(() => {
    mountedRef.current = true;
    
    if (useMock) {
      // Mock mode
      const interval = setInterval(() => {
        const mockTotal = Math.floor(Math.random() * 8);
        updateFrame(mockTotal, mockTotal / 10, mockTotal > 0 ? 'in_stock' : 'out_of_stock');
      }, refreshInterval);
      return () => clearInterval(interval);
    }

    // Try WebSocket first
    connectWebSocket();
    
    // Also start HTTP polling as backup (less frequent)
    const pollInterval = setInterval(() => {
      if (!usingWebSocket) {
        fetchInventory();
      }
    }, refreshInterval);
    
    return () => {
      mountedRef.current = false;
      clearInterval(pollInterval);
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [useMock, refreshInterval, connectWebSocket, fetchInventory, usingWebSocket]);

  return {
    currentFrame,
    timeSeries,
    connected,
    framesProcessed,
    usingWebSocket,
  };
}

function generateDensityMap(itemCount: number): number[][] {
  if (itemCount === 0) return [[0, 0, 0], [0, 0, 0], [0, 0, 0]];
  if (itemCount <= 2) return [[0, 1, 0], [0, 0, 0], [0, 0, 0]];
  if (itemCount <= 5) return [[1, 1, 0], [0, 1, 0], [0, 0, 0]];
  if (itemCount <= 10) return [[1, 2, 1], [0, 2, 1], [0, 1, 0]];
  return [[2, 2, 2], [1, 2, 2], [1, 1, 1]];
}