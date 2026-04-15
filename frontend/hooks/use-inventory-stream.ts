// frontend/hooks/use-inventory-stream.ts
import { useState, useEffect, useRef } from 'react';
import { FrameData, TimeSeriesPoint } from '@/lib/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://192.168.1.4:8000';

export function useInventoryStream({ 
  useMock = false, 
  refreshInterval = 5000  // Poll every 5 seconds
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
  
  const timeSeriesRef = useRef<TimeSeriesPoint[]>([]);
  const mountedRef = useRef(true);

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

  const updateTimeSeries = (totalObjects: number, densityScore: number, fps: number) => {
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
  };

  // Poll inventory data
  useEffect(() => {
    if (useMock) {
      // Mock data mode
      const interval = setInterval(() => {
        const mockTotal = Math.floor(Math.random() * 5);
        setCurrentFrame(prev => ({
          ...prev,
          frame_id: prev.frame_id + 1,
          timestamp: Date.now() / 1000,
          inventory: {
            total_objects: mockTotal,
            class_counts: { item: mockTotal },
            density_score: mockTotal / 10,
            coverage_ratio: mockTotal / 100,
          },
          density_map: [[mockTotal, 0, 0], [0, 0, 0], [0, 0, 0]],
        }));
        setFramesProcessed(prev => prev + 1);
        setConnected(true);
        updateTimeSeries(mockTotal, mockTotal / 10, 1);
      }, refreshInterval);
      return () => clearInterval(interval);
    }

    mountedRef.current = true;
    
    const fetchInventory = async () => {
      if (!mountedRef.current) return;
      
      try {
        const response = await fetch(`${API_URL}/api/inventory/count`);
        if (response.ok) {
          const data = await response.json();
          if (data.success && data.data?.current) {
            const currentCount = data.data.current.current_count || 0;
            const densityScore = data.data.current.density_score || 0;
            
            setCurrentFrame(prev => ({
              ...prev,
              frame_id: prev.frame_id + 1,
              timestamp: Date.now() / 1000,
              inventory: {
                total_objects: currentCount,
                class_counts: {},
                density_score: densityScore,
                coverage_ratio: currentCount / 100,
              },
              density_map: generateDensityMap(currentCount),
              fps: 1,
            }));
            
            setFramesProcessed(prev => prev + 1);
            setConnected(true);
            updateTimeSeries(currentCount, densityScore, 1);
          }
        } else {
          setConnected(false);
        }
      } catch (error) {
        console.error('Fetch error:', error);
        setConnected(false);
      }
    };

    // Initial fetch
    fetchInventory();
    
    // Poll every refreshInterval
    const interval = setInterval(fetchInventory, refreshInterval);
    
    return () => {
      mountedRef.current = false;
      clearInterval(interval);
    };
  }, [useMock, refreshInterval]);

  return {
    currentFrame,
    timeSeries,
    connected,
    framesProcessed,
  };
}

function generateDensityMap(itemCount: number): number[][] {
  if (itemCount === 0) return [[0, 0, 0], [0, 0, 0], [0, 0, 0]];
  if (itemCount <= 2) return [[0, 1, 0], [0, 0, 0], [0, 0, 0]];
  if (itemCount <= 5) return [[1, 1, 0], [0, 1, 0], [0, 0, 0]];
  if (itemCount <= 10) return [[1, 2, 1], [0, 2, 1], [0, 1, 0]];
  return [[2, 2, 2], [1, 2, 2], [1, 1, 1]];
}