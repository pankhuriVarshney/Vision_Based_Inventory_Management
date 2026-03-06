"use client"

import { cn } from "@/lib/utils"
import {
  LayoutDashboard,
  BarChart3,
  Settings,
  Camera,
  Box,
  Wifi,
  WifiOff,
  ChevronLeft,
  ChevronRight,
  Video,
} from "lucide-react"
import { useState } from "react"

interface SidebarProps {
  activeView: string
  onViewChange: (view: string) => void
  connected: boolean
}

const navItems = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { id: "analytics", label: "Analytics", icon: BarChart3 },
  { id: "live", label: "Live Stream", icon: Video },
  { id: "cameras", label: "Cameras", icon: Camera },
  { id: "settings", label: "Settings", icon: Settings },
]

export function AppSidebar({ activeView, onViewChange, connected }: SidebarProps) {
  const [collapsed, setCollapsed] = useState(false)

  return (
    <aside
      className={cn(
        "flex flex-col border-r border-border bg-sidebar transition-all duration-300",
        collapsed ? "w-16" : "w-56"
      )}
    >
      {/* Logo */}
      <div className="flex items-center gap-3 border-b border-border px-4 py-4">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary">
          <Box className="h-4 w-4 text-primary-foreground" />
        </div>
        {!collapsed && (
          <div className="flex flex-col">
            <span className="text-sm font-semibold text-foreground">ShelfVision</span>
            <span className="text-xs text-muted-foreground">Inventory AI</span>
          </div>
        )}
      </div>

      {/* Nav */}
      <nav className="flex flex-1 flex-col gap-1 p-2">
        {navItems.map((item) => {
          const Icon = item.icon
          const isActive = activeView === item.id
          return (
            <button
              key={item.id}
              onClick={() => onViewChange(item.id)}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:bg-secondary hover:text-foreground"
              )}
            >
              <Icon className="h-4 w-4 shrink-0" />
              {!collapsed && <span>{item.label}</span>}
            </button>
          )
        })}
      </nav>

      {/* Status & Collapse */}
      <div className="border-t border-border p-3">
        <div className="flex items-center gap-2">
          {connected ? (
            <Wifi className="h-4 w-4 shrink-0 text-success" />
          ) : (
            <WifiOff className="h-4 w-4 shrink-0 text-destructive" />
          )}
          {!collapsed && (
            <span className={cn("text-xs", connected ? "text-success" : "text-destructive")}>
              {connected ? "Stream Active" : "Disconnected"}
            </span>
          )}
        </div>
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="mt-3 flex w-full items-center justify-center rounded-md py-1.5 text-muted-foreground hover:bg-secondary hover:text-foreground transition-colors"
        >
          {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </button>
      </div>
    </aside>
  )
}
