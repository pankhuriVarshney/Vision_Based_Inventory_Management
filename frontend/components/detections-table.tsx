'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Detection } from '@/lib/api-client';

interface DetectionsTableProps {
  detections: Detection[];
  maxDisplay?: number;
}

export function DetectionsTable({
  detections,
  maxDisplay = 10,
}: DetectionsTableProps) {
  const displayDetections = detections.slice(0, maxDisplay);
  const remaining = detections.length - maxDisplay;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">
          Detected Items {detections.length > 0 && (
            <Badge variant="secondary" className="ml-2">
              {detections.length}
            </Badge>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {detections.length === 0 ? (
          <div className="text-center text-muted-foreground py-8">
            No items detected
          </div>
        ) : (
          <div className="space-y-2">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[50px]">#</TableHead>
                  <TableHead>Class</TableHead>
                  <TableHead>Confidence</TableHead>
                  <TableHead>Position</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {displayDetections.map((detection, index) => (
                  <TableRow key={index}>
                    <TableCell className="font-mono text-xs">
                      {index + 1}
                    </TableCell>
                    <TableCell className="font-medium">
                      <Badge variant="outline">
                        {detection.class_name}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <div className="flex-1 h-2 w-24 bg-secondary rounded-full overflow-hidden">
                          <div
                            className="h-full bg-primary transition-all"
                            style={{ width: `${detection.confidence * 100}%` }}
                          />
                        </div>
                        <span className="text-xs text-muted-foreground w-12">
                          {(detection.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                    </TableCell>
                    <TableCell className="font-mono text-xs">
                      ({detection.center[0].toFixed(0)}, {detection.center[1].toFixed(0)})
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            
            {remaining > 0 && (
              <div className="text-center text-sm text-muted-foreground">
                +{remaining} more items
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default DetectionsTable;
