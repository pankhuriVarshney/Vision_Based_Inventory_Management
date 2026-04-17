"use client";

import { Badge } from "@/components/ui/badge";
import { Bell } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Children } from "react";

interface DashboardHeaderProps {
  title: string;
  subtitle?: string;
  children?: React.ReactNode;
}

export function DashboardHeader({ title, subtitle }: DashboardHeaderProps) {
  return (
    <header className="flex items-center justify-between border-b border-border bg-card px-6 py-3">
      <div className="flex flex-col">
        <h1 className="text-lg font-semibold text-foreground">{title}</h1>
        {subtitle && (
          <p className="text-xs text-muted-foreground">{subtitle}</p>
        )}
      </div>
      <div className="flex items-center gap-3">
        {children}
        <Badge
          variant="outline"
          className="border-primary/30 bg-primary/10 text-primary font-mono text-xs"
        >
          v1.2.0
        </Badge>
        <Button variant="ghost" size="icon" className="h-8 w-8 relative">
          <Bell className="h-4 w-4" />
          <span className="absolute -right-0.5 -top-0.5 h-2 w-2 rounded-full bg-destructive" />
        </Button>
      </div>
    </header>
  );
}
