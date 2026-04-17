"use client";

import React, { useRef, useState, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Wifi, WifiOff, Activity, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ROSVideoStreamProps {
  piIp?: string;
  port?: number;
  className?: string;
  onStreamStatus?: (connected: boolean, fps: number) => void;
}

export function ROSVideoStream({
  piIp = process.env.NEXT_PUBLIC_PI_IP || "192.168.1.4",
  port = 8080,
  className = "",
  onStreamStatus,
}: ROSVideoStreamProps) {
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState(false);
  const [fps, setFps] = useState(0);
  const [reconnecting, setReconnecting] = useState(false);
  const imgRef = useRef<HTMLImageElement>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const frameCountRef = useRef(0);
  const lastFpsUpdateRef = useRef(Date.now());
  const reconnectAttemptsRef = useRef(0);

  const streamUrl = `http://${piIp}:${port}/stream.mjpg`;

  const connect = () => {
    if (imgRef.current) {
      // Add cache-busting timestamp to prevent caching
      imgRef.current.src = `${streamUrl}?t=${Date.now()}`;
    }
  };

  const reconnect = () => {
    if (reconnecting) return;

    setReconnecting(true);
    setError(true);

    // Exponential backoff: 2s, 4s, 8s, max 30s
    const delay = Math.min(
      30000,
      Math.pow(2, reconnectAttemptsRef.current) * 1000,
    );
    console.log(`Attempting reconnect in ${delay / 1000}s...`);

    if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
    reconnectTimeoutRef.current = setTimeout(() => {
      reconnectAttemptsRef.current++;
      setError(false);
      connect();
      setReconnecting(false);
    }, delay);
  };

  useEffect(() => {
    connect();

    // Calculate FPS based on image load events
    const handleImageLoad = () => {
      frameCountRef.current++;
      const now = Date.now();
      const elapsed = (now - lastFpsUpdateRef.current) / 1000;

      if (elapsed >= 1) {
        const currentFps = frameCountRef.current / elapsed;
        setFps(currentFps);
        frameCountRef.current = 0;
        lastFpsUpdateRef.current = now;

        // Notify parent component
        if (onStreamStatus) {
          onStreamStatus(true, currentFps);
        }
      }

      // Reset reconnect attempts on successful frame
      reconnectAttemptsRef.current = 0;
    };

    // Health check interval
    const checkHealth = async () => {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 3000);

        const response = await fetch(`http://${piIp}:${port}/health`, {
          signal: controller.signal,
        });
        clearTimeout(timeoutId);

        if (response.ok) {
          setConnected(true);
          setError(false);
          reconnectAttemptsRef.current = 0;
        } else {
          setConnected(false);
          if (!reconnecting) reconnect();
        }
      } catch (err) {
        console.error("ROS stream health check failed:", err);
        setConnected(false);
        if (!reconnecting) reconnect();
      }
    };

    const img = imgRef.current;
    if (img) {
      img.addEventListener("load", handleImageLoad);
      img.addEventListener("error", () => {
        setConnected(false);
        if (!reconnecting) reconnect();
      });
    }

    checkHealth();
    const healthInterval = setInterval(checkHealth, 10000); // Check every 10 seconds

    return () => {
      if (img) {
        img.removeEventListener("load", handleImageLoad);
      }
      clearInterval(healthInterval);
      if (reconnectTimeoutRef.current)
        clearTimeout(reconnectTimeoutRef.current);
    };
  }, [piIp, port, streamUrl]);

  const handleManualReconnect = () => {
    reconnectAttemptsRef.current = 0;
    reconnect();
  };

  return (
    <Card className={`border-border bg-card ${className}`}>
      <CardContent className="p-4">
        <div className="relative">
          <img
            ref={imgRef}
            alt="ROS Camera Stream"
            className="w-full rounded-lg bg-black"
            style={{
              maxHeight: "480px",
              objectFit: "contain",
              minHeight: "360px",
            }}
          />

          {/* Connection Status Overlay */}
          <div className="absolute top-2 left-2 flex gap-2">
            <Badge
              variant={connected ? "default" : "destructive"}
              className="gap-1"
            >
              {connected ? (
                <>
                  <Wifi className="w-3 h-3" />
                  LIVE
                </>
              ) : (
                <>
                  <WifiOff className="w-3 h-3" />
                  {reconnecting ? "RECONNECTING..." : "OFFLINE"}
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
                📹 {piIp}:{port}
              </Badge>
            </div>
          )}

          {/* Timestamp Overlay */}
          {connected && (
            <div className="absolute bottom-2 right-2">
              <Badge variant="secondary" className="text-xs font-mono">
                {new Date().toLocaleTimeString()}
              </Badge>
            </div>
          )}

          {/* Error Overlay */}
          {error && !connected && (
            <div className="absolute inset-0 flex items-center justify-center bg-black/80 rounded-lg">
              <div className="text-center text-white p-4">
                <WifiOff className="w-12 h-12 mx-auto mb-2 text-red-500" />
                <p className="font-bold">Cannot connect to ROS stream</p>
                <p className="text-sm text-gray-400 mt-1">
                  Make sure ROS nodes are running on Pi
                </p>
                <p className="text-xs font-mono mt-2 text-gray-500">
                  {streamUrl}
                </p>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleManualReconnect}
                  className="mt-3 gap-2"
                  disabled={reconnecting}
                >
                  <RefreshCw
                    className={`w-3 h-3 ${reconnecting ? "animate-spin" : ""}`}
                  />
                  {reconnecting ? "Reconnecting..." : "Retry Connection"}
                </Button>
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
