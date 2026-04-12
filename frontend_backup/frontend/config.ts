/**
 * Frontend Configuration
 * Update these values to match your backend setup
 */

// WebSocket Connection Configuration
export const WS_CONFIG = {
  // Backend WebSocket URL - Change this to your Raspberry Pi IP
  // Examples:
  // - Local: 'ws://localhost:8000/ws/detections'
  // - Remote Raspberry Pi: 'ws://192.168.1.100:8000/ws/detections'
  // Set NEXT_PUBLIC_WS_URL in .env.local to configure
  URL: process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws/detections',
  
  // Reconnection settings
  RECONNECT_ATTEMPTS: 5,
  RECONNECT_DELAY: 2000, // milliseconds
  HEARTBEAT_INTERVAL: 30000, // milliseconds
  MESSAGE_TIMEOUT: 5000, // milliseconds
}

// Display Configuration
export const DISPLAY_CONFIG = {
  // Frame dimensions (must match backend)
  FRAME_WIDTH: 640,
  FRAME_HEIGHT: 480,
  
  // Target FPS for display
  TARGET_FPS: 30,
  
  // Data history to maintain
  HISTORY_LENGTH: 60, // seconds of data
  
  // Chart update frequency
  CHART_UPDATE_INTERVAL: 1000, // milliseconds
}

// Detection Configuration
export const DETECTION_CONFIG = {
  // Default confidence threshold
  DEFAULT_CONFIDENCE: 0.5,
  MIN_CONFIDENCE: 0.1,
  MAX_CONFIDENCE: 1.0,
  
  // Object class colors
  CLASS_COLORS: {
    'Product': '#3b82f6',      // Blue
    'Box': '#10b981',          // Green
    'Shelf': '#f59e0b',        // Amber
    'Other': '#8b5cf6',        // Purple
  } as Record<string, string>,
  
  // Default model (frontend-side, backend uses actual model)
  DEFAULT_MODEL: 'YOLOv8n',
}

// Heatmap Configuration
export const HEATMAP_CONFIG = {
  // Default grid size
  DEFAULT_GRID_SIZE: 3,
  MIN_GRID_SIZE: 2,
  MAX_GRID_SIZE: 4,
  
  // Color scheme for intensity levels
  // [empty, low, medium, high]
  COLOR_STOPS: [
    '#1a1a2e', // Dark (empty)
    '#2ecc71', // Green (low)
    '#f39c12', // Orange (medium)
    '#e74c3c', // Red (high)
  ] as const,
}

// System Health Configuration
export const HEALTH_CONFIG = {
  // Alert thresholds
  CPU_WARNING: 75,
  CPU_CRITICAL: 90,
  MEMORY_WARNING: 80,
  MEMORY_CRITICAL: 95,
  LATENCY_WARNING: 100, // milliseconds
  LATENCY_CRITICAL: 300, // milliseconds
}

// Mock Data Configuration (for development/testing)
export const MOCK_CONFIG = {
  // Enable mock data when WebSocket is unavailable
  ENABLE_FALLBACK: true,
  
  // Number of mock detections per frame
  MOCK_DETECTION_COUNT_MIN: 20,
  MOCK_DETECTION_COUNT_MAX: 50,
}

/**
 * Utility function to update WebSocket URL at runtime
 * Usage: setWebSocketURL('ws://192.168.1.100:8000/ws/detections')
 */
export function setWebSocketURL(url: string) {
  WS_CONFIG.URL = url
  // Store in localStorage for persistence
  if (typeof window !== 'undefined') {
    localStorage.setItem('ws_url', url)
  }
}

/**
 * Utility function to load saved WebSocket URL
 */
export function loadWebSocketURL() {
  if (typeof window !== 'undefined') {
    const saved = localStorage.getItem('ws_url')
    if (saved) {
      WS_CONFIG.URL = saved
      return saved
    }
  }
  return WS_CONFIG.URL
}

/**
 * Utility function to validate WebSocket URL format
 */
export function validateWebSocketURL(url: string): boolean {
  try {
    const pattern = /^wss?:\/\/([a-zA-Z0-9.-]+|\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d+)(\/.*)?$/
    return pattern.test(url)
  } catch {
    return false
  }
}
