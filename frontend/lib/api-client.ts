/**
 * API Client for Vision-Based Inventory Management System
 * Connects to FastAPI backend for real-time inventory monitoring
 */

// In Next.js client-side, NEXT_PUBLIC_* vars are replaced at build time
// We need to ensure they have fallbacks

// const WS_BASE_URL = API_BASE_URL.replace('http', 'ws').replace('https', 'wss');
// frontend/lib/api-client.ts
// API Client for Vision-Based Inventory Management System

const PI_IP = process.env.NEXT_PUBLIC_PI_IP || '192.168.1.4';
const API_BASE_URL = `http://${PI_IP}:8000`;

console.log(`🔌 API Client connecting to: ${API_BASE_URL}`);

export interface Detection {
  bbox: number[];
  confidence: number;
  class_id: number;
  class_name: string;
  center: number[];
}

export interface InventoryStats {
  avg_count: number;
  min_count: number;
  max_count: number;
  current_count: number;
  data_points: number;
}
export interface LearningStats {
  status: string;
  buffer_size: number;
  buffer_max: number;
  avg_confidence: number;
  fill_percent: number;
  total_learning_events: number;
  auto_learn_enabled: boolean;
}


export class InventoryAPIClient {
  private baseUrl: string;

  constructor(baseUrl?: string) {
    this.baseUrl = baseUrl || API_BASE_URL;
    console.log(`✅ API Client initialized with base URL: ${this.baseUrl}`);
  }

  async getInventoryCount(): Promise<InventoryStats> {
    try {
      const response = await fetch(`${this.baseUrl}/api/inventory/count`, {
        cache: 'no-store',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        console.warn(`Inventory API returned ${response.status}`);
        return {
          avg_count: 0,
          min_count: 0,
          max_count: 0,
          current_count: 0,
          data_points: 0,
        };
      }
      
      const data = await response.json();
      console.log('Inventory API response:', data);
      
      // Handle different response formats
      if (data.data?.current) {
        return data.data.current;
      }
      if (data.current_count !== undefined) {
        return data;
      }
      
      return {
        avg_count: data.avg_count || 0,
        min_count: data.min_count || 0,
        max_count: data.max_count || 0,
        current_count: data.current_count || data.total_objects || 0,
        data_points: data.data_points || 0,
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

  async getInventoryHistory(limit: number = 100): Promise<any[]> {
    try {
      const response = await fetch(`${this.baseUrl}/api/inventory/history?limit=${limit}`);
      const data = await response.json();
      return data.data?.history || [];
    } catch (error) {
      console.error('Failed to fetch inventory history:', error);
      return [];
    }
  }

  async exportInventory(format: 'json' | 'csv' = 'json'): Promise<Blob> {
    const response = await fetch(`${this.baseUrl}/api/inventory/export?format=${format}`, {
      method: 'POST',
    });
    return response.blob();
  }
  async getLearningStatus(): Promise<LearningStats> {
    try {
      const response = await fetch(`${this.baseUrl}/api/learning/status`);
      const data = await response.json();
      if (data.success) {
        return data.data;
      }
      return {
        status: 'initializing',
        buffer_size: 0,
        buffer_max: 500,
        avg_confidence: 0,
        fill_percent: 0,
        total_learning_events: 0,
        auto_learn_enabled: true
      };
    } catch (error) {
      console.error('Failed to fetch learning status:', error);
      return {
        status: 'error',
        buffer_size: 0,
        buffer_max: 500,
        avg_confidence: 0,
        fill_percent: 0,
        total_learning_events: 0,
        auto_learn_enabled: true
      };
    }
  }

  async triggerLearning(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/api/learning/trigger`, {
        method: 'POST',
      });
      const data = await response.json();
      return data.success;
    } catch (error) {
      console.error('Failed to trigger learning:', error);
      return false;
    }
  }

}

export const apiClient = new InventoryAPIClient();
export default apiClient;