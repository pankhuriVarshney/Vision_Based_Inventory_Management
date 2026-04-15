// frontend/hooks/use-inventory-stream.ts
import { useState, useEffect, useRef, useCallback } from 'react';
import { FrameData, TimeSeriesPoint, Detection } from '@/lib/types';
import { apiClient } from '@/lib/api-client';

interface UseInventoryStreamProps {
  useMock?: boolean;
  wsUrl?: string;
  refreshInterval?: number;
}

export function useInventoryStream({ 
  useMock = false, 
  wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://192.168.1.4:8000/ws/inventory',
  refreshInterval = 2000
}: UseInventoryStreamProps) {
  const [currentFrame, setCurrentFrame] = useState<FrameData>(() => ({
    frame_id: 0,
    timestamp: Date.now() / 1000,
    detections: [],
    inventory: {
      total_objects: 0,
      class_counts: {},
      density_score: 0,
      coverage_ratio: 0,
    },
    density_map: [[0]],
    fps: 0,
  }));
  const [timeSeries, setTimeSeries] = useState<TimeSeriesPoint[]>([]);
  const [connected, setConnected] = useState(false);
  const [framesProcessed, setFramesProcessed] = useState(0);
  
  const intervalRef = useRef<NodeJS.Timeout>();
  const wsRef = useRef<WebSocket | null>(null);
  const timeSeriesRef = useRef<TimeSeriesPoint[]>([]);

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

  // Real data via WebSocket
  useEffect(() => {
    if (useMock) {
      console.log('Using mock data mode');
      return;
    }

    console.log(`Connecting to WebSocket: ${wsUrl}`);
    
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('✅ Inventory WebSocket connected');
      setConnected(true);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        // Convert WebSocket data to FrameData format
        const frameData: FrameData = {
          frame_id: framesProcessed + 1,
          timestamp: Date.now() / 1000,
          detections: data.detections || [],
          inventory: {
            total_objects: data.total_objects || data.inventory?.total_objects || 0,
            class_counts: data.class_counts || data.inventory?.class_counts || {},
            density_score: data.density_score || data.inventory?.density_score || 0,
            coverage_ratio: data.coverage_ratio || 0.5,
          },
          density_map: data.density_map || generateDefaultDensityMap(),
          fps: data.fps || 0,
        };
        
        setCurrentFrame(frameData);
        setFramesProcessed(prev => prev + 1);
        
        // Update time series
        updateTimeSeries(
          frameData.inventory.total_objects,
          frameData.inventory.density_score,
          frameData.fps || 0
        );
      } catch (error) {
        console.error('Error parsing WebSocket data:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('❌ Inventory WebSocket error:', error);
      setConnected(false);
    };

    ws.onclose = () => {
      console.log('Inventory WebSocket closed, attempting reconnect in 3s...');
      setConnected(false);
      // Attempt reconnect
      setTimeout(() => {
        if (wsRef.current?.readyState !== WebSocket.OPEN) {
          console.log('Reconnecting...');
          const newWs = new WebSocket(wsUrl);
          wsRef.current = newWs;
        }
      }, 3000);
    };

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [useMock, wsUrl, framesProcessed, updateTimeSeries]);

  // Also poll REST API as fallback
  useEffect(() => {
    if (useMock) return;

    const fetchInventory = async () => {
      try {
        const stats = await apiClient.getInventoryCount();
        if (stats && stats.current_count !== undefined) {
          setCurrentFrame(prev => ({
            ...prev,
            inventory: {
              ...prev.inventory,
              total_objects: stats.current_count,
            },
          }));
        }
      } catch (error) {
        console.error('REST API fetch error:', error);
      }
    };

    intervalRef.current = setInterval(fetchInventory, refreshInterval);
    
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [useMock, refreshInterval]);

  return {
    currentFrame,
    timeSeries,
    connected,
    framesProcessed,
  };
}

function generateDefaultDensityMap(): number[][] {
  return [
    [0, 0, 0],
    [0, 0, 0],
    [0, 0, 0],
  ];
}