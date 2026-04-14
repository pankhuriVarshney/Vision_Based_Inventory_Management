/**
 * API Client for Vision-Based Inventory Management System
 * Connects to FastAPI backend for real-time inventory monitoring
 */

// In Next.js client-side, NEXT_PUBLIC_* vars are replaced at build time
// We need to ensure they have fallbacks
const getApiUrl = () => {
  // For client-side in Next.js, we need to use a different approach
  if (typeof window !== 'undefined') {
    // Try to get from window.__NEXT_DATA__ or use hardcoded Pi IP
    const piIp = '192.168.1.4'; // Your Pi's IP - HARDCODED for now
    return `http://${piIp}:8000`;
  }
  // Server-side fallback
  return process.env.NEXT_PUBLIC_API_URL || 'http://192.168.1.4:8000';
};

const API_BASE_URL = getApiUrl();
const WS_BASE_URL = API_BASE_URL.replace('http', 'ws').replace('https', 'wss');

console.log(`🔌 API Client connecting to: ${API_BASE_URL}`);
console.log(`🔌 WebSocket connecting to: ${WS_BASE_URL}`);

// Rest of your types remain the same...
export interface Detection {
  bbox: number[];
  confidence: number;
  class_id: number;
  class_name: string;
  center: number[];
}

export interface Inventory {
  total_objects: number;
  class_counts: Record<string, number>;
  density_score: number;
  timestamp: number;
}

export interface DetectionResult {
  success: boolean;
  detections: Detection[];
  inventory: Inventory;
  metadata: {
    image_shape: number[];
    inference_time_ms: number;
    fps: number;
    model_info: Record<string, any>;
  };
  annotated_image_base64?: string;
  error?: string;
}

export interface InventoryStats {
  avg_count: number;
  min_count: number;
  max_count: number;
  current_count: number;
  data_points: number;
}

export interface InventoryHistory {
  timestamp: number;
  total_objects: number;
  class_counts: Record<string, number>;
}

export interface ModelInfo {
  path: string;
  device: string;
  conf_threshold: number;
  iou_threshold: number;
  frame_count: number;
}

export interface VideoFrame {
  success: boolean;
  frame: string; // base64
  detections: Detection[];
  inventory: Inventory;
  stats: {
    fps: number;
    latency_ms: number;
    frame_count: number;
  };
}

// API Client Class
export class InventoryAPIClient {
  private baseUrl: string;
  private wsUrl: string;
  private videoWebSocket: WebSocket | null = null;
  private inventoryWebSocket: WebSocket | null = null;

  constructor(baseUrl?: string) {
    this.baseUrl = baseUrl || API_BASE_URL;
    this.wsUrl = WS_BASE_URL;
    console.log(`✅ API Client initialized with base URL: ${this.baseUrl}`);
    console.log(`✅ WebSocket URL: ${this.wsUrl}`);
  }

  // ========================================================================
  // REST API Methods
  // ========================================================================

  /**
   * Health check
   */
  async healthCheck(): Promise<{ status: string; detector_loaded: boolean }> {
    try {
      const response = await fetch(`${this.baseUrl}/api/health`);
      const data = await response.json();
      return data.data;
    } catch (error) {
      console.error('Health check failed:', error);
      return { status: 'unreachable', detector_loaded: false };
    }
  }

  /**
   * Detect objects from image file
   */
  async detectImage(file: File): Promise<DetectionResult> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${this.baseUrl}/api/detect/image`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Detection failed');
    }

    return response.json();
  }

  /**
   * Detect objects from base64 image
   */
  async detectBase64(imageBase64: string): Promise<DetectionResult> {
    const response = await fetch(`${this.baseUrl}/api/detect/base64`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ image_base64: imageBase64 }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Detection failed');
    }

    return response.json();
  }

  /**
   * Detect objects from image URL
   */
  async detectUrl(url: string): Promise<DetectionResult> {
    const response = await fetch(`${this.baseUrl}/api/detect/url`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ url }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Detection failed');
    }

    return response.json();
  }

  /**
   * Get current inventory count
   */
  async getInventoryCount(): Promise<InventoryStats> {
    try {
      const response = await fetch(`${this.baseUrl}/api/inventory/count`);
      if (!response.ok) {
        console.warn(`Inventory API returned ${response.status}, using fallback`);
        return {
          avg_count: 0,
          min_count: 0,
          max_count: 0,
          current_count: 0,
          data_points: 0,
        };
      }
      const data = await response.json();
      return data.data?.current || {
        avg_count: 0,
        min_count: 0,
        max_count: 0,
        current_count: 0,
        data_points: 0,
      };
    } catch (error) {
      console.error('Failed to fetch inventory count:', error);
      return {
        avg_count: 0,
        min_count: 0,
        max_count: 0,
        current_count: 0,
        data_points: 0,
      };
    }
  }

  /**
   * Get inventory history
   */
  async getInventoryHistory(limit: number = 100): Promise<InventoryHistory[]> {
    try {
      const response = await fetch(`${this.baseUrl}/api/inventory/history?limit=${limit}`);
      const data = await response.json();
      return data.data?.history || [];
    } catch (error) {
      console.error('Failed to fetch inventory history:', error);
      return [];
    }
  }

  /**
   * Export inventory data
   */
  async exportInventory(format: 'json' | 'csv' = 'json'): Promise<Blob> {
    const response = await fetch(`${this.baseUrl}/api/inventory/export?format=${format}`, {
      method: 'POST',
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Export failed');
    }

    return response.blob();
  }

  /**
   * Get model information
   */
  async getModelInfo(): Promise<ModelInfo> {
    try {
      const response = await fetch(`${this.baseUrl}/api/model/info`);
      const data = await response.json();
      return data.data;
    } catch (error) {
      console.error('Failed to fetch model info:', error);
      return {
        path: 'unknown',
        device: 'unknown',
        conf_threshold: 0.25,
        iou_threshold: 0.45,
        frame_count: 0,
      };
    }
  }

  /**
   * List available models
   */
  async listModels(): Promise<Array<{ name: string; path: string; size_mb: number }>> {
    try {
      const response = await fetch(`${this.baseUrl}/api/model/list`);
      const data = await response.json();
      return data.data?.models || [];
    } catch (error) {
      console.error('Failed to list models:', error);
      return [];
    }
  }

  /**
   * Switch to different model
   */
  async switchModel(modelPath: string, confThreshold: number = 0.25): Promise<ModelInfo> {
    const response = await fetch(`${this.baseUrl}/api/model/switch`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ model_path: modelPath, conf_threshold: confThreshold }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Model switch failed');
    }

    return response.json();
  }

  /**
   * Clear inventory history
   */
  async clearInventory(): Promise<void> {
    const response = await fetch(`${this.baseUrl}/api/inventory/clear`, {
      method: 'POST',
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Clear failed');
    }
  }

  /**
   * Start video processing
   */
  async startVideo(source: string = '0'): Promise<{ active: boolean; source: string }> {
    const response = await fetch(`${this.baseUrl}/api/video/start?source=${source}`, {
      method: 'POST',
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Start video failed');
    }

    return response.json();
  }

  /**
   * Stop video processing
   */
  async stopVideo(): Promise<{ active: boolean }> {
    const response = await fetch(`${this.baseUrl}/api/video/stop`, {
      method: 'POST',
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Stop video failed');
    }

    return response.json();
  }

  /**
   * Get video status
   */
  async getVideoStatus(): Promise<{
    active: boolean;
    clients: number;
    stats: { avg_fps: number; avg_latency_ms: number };
  }> {
    const response = await fetch(`${this.baseUrl}/api/video/status`);
    const data = await response.json();
    return data.data;
  }

  // ========================================================================
  // WebSocket Methods
  // ========================================================================

  /**
   * Connect to video WebSocket stream
   */
  connectVideoStream(
    source: string,
    onFrame: (frame: VideoFrame) => void,
    onError?: (error: string) => void,
    onClose?: () => void
  ): () => void {
    const ws = new WebSocket(`${this.wsUrl}/ws/video`);

    this.videoWebSocket = ws;

    ws.onopen = () => {
      console.log('✅ Video WebSocket connected');
      ws.send(JSON.stringify({ source }));
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onFrame(data);
      } catch (error) {
        console.error('Error parsing video frame:', error);
        if (onError) onError('Failed to parse video frame');
      }
    };

    ws.onerror = () => {
      console.error('❌ Video WebSocket error');
      if (onError) onError('WebSocket connection error');
    };

    ws.onclose = () => {
      console.log('Video WebSocket closed');
      if (onClose) onClose();
    };

    return () => {
      ws.close();
      this.videoWebSocket = null;
    };
  }

  /**
   * Connect to inventory WebSocket stream
   */
  connectInventoryStream(
    onInventory: (stats: InventoryStats) => void,
    onError?: (error: string) => void,
    onClose?: () => void
  ): () => void {
    const ws = new WebSocket(`${this.wsUrl}/ws/inventory`);

    this.inventoryWebSocket = ws;

    ws.onopen = () => {
      console.log('✅ Inventory WebSocket connected');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.success && data.inventory) {
          onInventory(data.inventory);
        }
      } catch (error) {
        console.error('Error parsing inventory data:', error);
        if (onError) onError('Failed to parse inventory data');
      }
    };

    ws.onerror = () => {
      console.error('❌ Inventory WebSocket error');
      if (onError) onError('WebSocket connection error');
    };

    ws.onclose = () => {
      console.log('Inventory WebSocket closed');
      if (onClose) onClose();
    };

    return () => {
      ws.close();
      this.inventoryWebSocket = null;
    };
  }

  /**
   * Disconnect all WebSocket connections
   */
  disconnectAll(): void {
    if (this.videoWebSocket) {
      this.videoWebSocket.close();
      this.videoWebSocket = null;
    }
    if (this.inventoryWebSocket) {
      this.inventoryWebSocket.close();
      this.inventoryWebSocket = null;
    }
  }
}

// Export singleton instance with Pi IP hardcoded
export const apiClient = new InventoryAPIClient('http://192.168.1.4:8000');

// Export default
export default apiClient;