'use client';

import React, { useRef, useState, useEffect } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Wifi, WifiOff, Activity } from 'lucide-react';

interface ROSVideoStreamProps {
  piIp?: string;
  port?: number;
  className?: string;
}

export function ROSVideoStream({ 
  piIp = process.env.NEXT_PUBLIC_PI_IP || '192.168.1.4',
  port = 8080,
  className = ''
}: ROSVideoStreamProps) {
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState(false);
  const [fps, setFps] = useState(0);
  const imgRef = useRef<HTMLImageElement>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const frameCountRef = useRef(0);
  const lastFpsUpdateRef = useRef(Date.now());

  useEffect(() => {
    const streamUrl = `http://${piIp}:${port}/stream.mjpg`;
    
    const connect = () => {
      if (imgRef.current) {
        imgRef.current.src = streamUrl;
      }
    };

    connect();

    // Calculate FPS based on image load events
    const handleImageLoad = () => {
      frameCountRef.current++;
      const now = Date.now();
      const elapsed = (now - lastFpsUpdateRef.current) / 1000;
      
      if (elapsed >= 1) {
        setFps(frameCountRef.current / elapsed);
        frameCountRef.current = 0;
        lastFpsUpdateRef.current = now;
      }
    };

    // Health check interval
    const checkHealth = async () => {
      try {
        const response = await fetch(`http://${piIp}:${port}/health`);
        if (response.ok) {
          setConnected(true);
          setError(false);
        } else {
          setConnected(false);
        }
      } catch (err) {
        console.error('ROS stream health check failed:', err);
        setConnected(false);
        setError(true);
        
        // Attempt reconnect after 5 seconds
        if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = setTimeout(connect, 5000);
      }
    };

    const img = imgRef.current;
    if (img) {
      img.addEventListener('load', handleImageLoad);
    }

    checkHealth();
    const interval = setInterval(checkHealth, 5000);

    return () => {
      if (img) {
        img.removeEventListener('load', handleImageLoad);
      }
      clearInterval(interval);
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
    };
  }, [piIp, port]);

  return (
    <Card className={`border-border bg-card ${className}`}>
      <CardContent className="p-4">
        <div className="relative">
          <img
            ref={imgRef}
            alt="ROS Camera Stream"
            className="w-full rounded-lg bg-black"
            style={{ 
              maxHeight: '480px', 
              objectFit: 'contain',
              minHeight: '360px'
            }}
            onError={() => {
              setError(true);
              setConnected(false);
            }}
            onLoad={() => {
              setError(false);
              setConnected(true);
            }}
          />
          
          {/* Connection Status Overlay */}
          <div className="absolute top-2 left-2 flex gap-2">
            <Badge variant={connected ? 'default' : 'destructive'} className="gap-1">
              {connected ? (
                <>
                  <Wifi className="w-3 h-3" />
                  LIVE
                </>
              ) : (
                <>
                  <WifiOff className="w-3 h-3" />
                  OFFLINE
                </>
              )}
            </Badge>
            
            {connected && (
              <Badge variant="secondary" className="gap-1">
                <Activity className="w-3 h-3" />
                {fps.toFixed(1)} FPS
              </Badge>
            )}
          </div>
          
          {/* Stream Info Overlay */}
          {connected && (
            <div className="absolute bottom-2 left-2">
              <Badge variant="secondary" className="text-xs font-mono">
                ROS Stream @ {piIp}:{port}
              </Badge>
            </div>
          )}
          
          {/* Error Overlay */}
          {error && (
            <div className="absolute inset-0 flex items-center justify-center bg-black/80 rounded-lg">
              <div className="text-center text-white p-4">
                <WifiOff className="w-12 h-12 mx-auto mb-2 text-red-500" />
                <p className="font-bold">Cannot connect to ROS stream</p>
                <p className="text-sm text-gray-400 mt-1">
                  Make sure ROS nodes are running on Pi
                </p>
                <p className="text-xs font-mono mt-2 text-gray-500">
                  http://{piIp}:{port}/stream.mjpg
                </p>
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}