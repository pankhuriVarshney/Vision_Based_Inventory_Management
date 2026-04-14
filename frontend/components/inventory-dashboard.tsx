'use client';

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { apiClient, InventoryStats, Detection } from '@/lib/api-client';
import { Package, TrendingUp, AlertTriangle, CheckCircle, Download } from 'lucide-react';

interface InventoryDashboardProps {
  inventory?: {
    total_objects: number;
    class_counts: Record<string, number>;
    density_score: number;
  };
  detections?: Detection[];
}

export function InventoryDashboard({ inventory, detections }: InventoryDashboardProps) {
  const [stats, setStats] = useState<InventoryStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  // Fetch initial inventory stats
  useEffect(() => {
   const fetchStats = async () => {
  try {
    const data = await apiClient.getInventoryCount();
    setStats(data);
    setLastUpdated(new Date());
  } catch (error) {
    console.error('Failed to fetch inventory stats:', error);
    // Don't show error, just keep existing stats
    setStats(prev => prev || {
      avg_count: 0,
      min_count: 0,
      max_count: 0,
      current_count: 0,
      data_points: 0,
    });
  } finally {
    setLoading(false);
  }
};

    fetchStats();

    // Poll for updates every 5 seconds
    const interval = setInterval(fetchStats, 5000);
    return () => clearInterval(interval);
  }, []);

  // Update stats from real-time data
  useEffect(() => {
    if (inventory) {
      setStats({
        avg_count: inventory.total_objects,
        min_count: 0,
        max_count: 100,
        current_count: inventory.total_objects,
        data_points: 1,
      });
      setLastUpdated(new Date());
    }
  }, [inventory]);

  const getStatusBadge = (count: number) => {
    if (count === 0) {
      return (
        <Badge variant="destructive">
          <AlertTriangle className="w-3 h-3 mr-1" />
          Out of Stock
        </Badge>
      );
    } else if (count < 5) {
      return (
        <Badge variant="secondary">
          <AlertTriangle className="w-3 h-3 mr-1" />
          Low Stock
        </Badge>
      );
    } else {
      return (
        <Badge className="bg-green-600">
          <CheckCircle className="w-3 h-3 mr-1" />
          In Stock
        </Badge>
      );
    }
  };

  const handleExport = async (format: 'json' | 'csv') => {
    try {
      const blob = await apiClient.exportInventory(format);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `inventory_export_${Date.now()}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Export failed:', error);
    }
  };

  const currentCount = stats?.current_count || inventory?.total_objects || 0;
  const capacityPercent = Math.min((currentCount / 100) * 100, 100);

  return (
    <div className="space-y-4">
      {/* Total Count Card */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">
            Total Items Detected
          </CardTitle>
          <Package className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="text-2xl font-bold">{loading ? '...' : currentCount}</div>
            {getStatusBadge(currentCount)}
          </div>
          <p className="text-xs text-muted-foreground mt-2">
            {lastUpdated ? `Updated ${lastUpdated.toLocaleTimeString()}` : 'Loading...'}
          </p>
        </CardContent>
      </Card>

      {/* Shelf Capacity */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">
            Shelf Capacity
          </CardTitle>
          <TrendingUp className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>{currentCount} / 100</span>
              <span>{capacityPercent.toFixed(0)}%</span>
            </div>
            <Progress value={capacityPercent} className="h-2" />
          </div>
        </CardContent>
      </Card>

      {/* Class Breakdown */}
      {inventory?.class_counts && Object.keys(inventory.class_counts).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">
              Items by Class
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(inventory.class_counts).map(([className, count]) => (
                <div key={className} className="flex items-center justify-between">
                  <span className="text-sm capitalize">{className}</span>
                  <Badge variant="secondary">{count}</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Statistics */}
      {stats && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">
              Statistics
            </CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-3 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold">{stats.avg_count.toFixed(1)}</div>
              <div className="text-xs text-muted-foreground">Average</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold">{stats.min_count}</div>
              <div className="text-xs text-muted-foreground">Minimum</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold">{stats.max_count}</div>
              <div className="text-xs text-muted-foreground">Maximum</div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Density Score */}
      {inventory?.density_score !== undefined && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">
              Shelf Density
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{inventory.density_score.toFixed(2)}</div>
            <p className="text-xs text-muted-foreground mt-1">
              Objects per grid cell
            </p>
          </CardContent>
        </Card>
      )}

      {/* Export Actions */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">
            Export Data
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleExport('json')}
              className="flex-1"
            >
              <Download className="w-4 h-4 mr-2" />
              JSON
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleExport('csv')}
              className="flex-1"
            >
              <Download className="w-4 h-4 mr-2" />
              CSV
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default InventoryDashboard;
