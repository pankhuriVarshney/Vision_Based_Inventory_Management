/**
 * API Client for Vision-Based Inventory Management System
 * Connects to FastAPI backend for real-time inventory monitoring
 */

// API Configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const WS_BASE_URL = API_BASE_URL.replace('http', 'ws');

// Types
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
  }

  // ========================================================================
  // REST API Methods
  // ========================================================================

  /**
   * Health check
   */
  async healthCheck(): Promise<{ status: string; detector_loaded: boolean }> {
    const response = await fetch(`${this.baseUrl}/api/health`);
    const data = await response.json();
    return data.data;
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
    const response = await fetch(`${this.baseUrl}/api/inventory/count`);
    const data = await response.json();
    return data.data.current;
  }

  /**
   * Get inventory history
   */
  async getInventoryHistory(limit: number = 100): Promise<InventoryHistory[]> {
    const response = await fetch(`${this.baseUrl}/api/inventory/history?limit=${limit}`);
    const data = await response.json();
    return data.data.history;
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
    const response = await fetch(`${this.baseUrl}/api/model/info`);
    const data = await response.json();
    return data.data;
  }

  /**
   * List available models
   */
  async listModels(): Promise<Array<{ name: string; path: string; size_mb: number }>> {
    const response = await fetch(`${this.baseUrl}/api/model/list`);
    const data = await response.json();
    return data.data.models;
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
      // Send source configuration
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
      if (onError) onError('WebSocket connection error');
    };

    ws.onclose = () => {
      if (onClose) onClose();
    };

    // Return disconnect function
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

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.success) {
          onInventory(data.inventory);
        }
      } catch (error) {
        console.error('Error parsing inventory data:', error);
        if (onError) onError('Failed to parse inventory data');
      }
    };

    ws.onerror = () => {
      if (onError) onError('WebSocket connection error');
    };

    ws.onclose = () => {
      if (onClose) onClose();
    };

    // Return disconnect function
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

// Export singleton instance
export const apiClient = new InventoryAPIClient();

// Export default
export default apiClient;
