// frontend/hooks/use-inventory-stream.ts
import { useState, useEffect, useRef, useCallback } from 'react';
import { FrameData, TimeSeriesPoint } from '@/lib/types';
import { generateMockFrame, generateInitialTimeSeries } from '@/lib/mock-data';

interface UseInventoryStreamProps {
  useMock?: boolean;
  wsUrl?: string;
  refreshInterval?: number; // Add this
}

export function useInventoryStream({ 
  useMock = false, 
  wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws/inventory',
  refreshInterval = 2000  // Default 2 seconds instead of 30 FPS
}: UseInventoryStreamProps) {
  const [currentFrame, setCurrentFrame] = useState<FrameData>(() => generateMockFrame(0));
  const [timeSeries, setTimeSeries] = useState<TimeSeriesPoint[]>(() => generateInitialTimeSeries());
  const [connected, setConnected] = useState(false);
  const [framesProcessed, setFramesProcessed] = useState(0);
  
  const intervalRef = useRef<NodeJS.Timeout>();

  useEffect(() => {
    if (useMock) {
      // Mock mode - update every 2 seconds
      const interval = setInterval(() => {
        setCurrentFrame(generateMockFrame(Date.now()));
        setFramesProcessed(prev => prev + 1);
        setConnected(true);
      }, refreshInterval);
      return () => clearInterval(interval);
    }

    // Real data - use HTTP polling instead of WebSocket (lighter)
    let isMounted = true;
    
    const fetchFrame = async () => {
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/stream/frame`);
        if (response.ok) {
          const data = await response.json();
          if (isMounted && data.frame) {
            setCurrentFrame(data.frame);
            setFramesProcessed(prev => prev + 1);
            setConnected(true);
          }
        } else {
          setConnected(false);
        }
      } catch (error) {
        console.error('Fetch error:', error);
        setConnected(false);
      }
    };
    
    // Poll every refreshInterval milliseconds
    fetchFrame(); // Initial fetch
    intervalRef.current = setInterval(fetchFrame, refreshInterval);
    
    return () => {
      isMounted = false;
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