"use client"

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { Brain, TrendingUp, Clock, Database, Zap, RefreshCw } from 'lucide-react'

interface LearningStats {
  status: string
  buffer_size: number
  buffer_max: number
  avg_confidence: number
  fill_percent: number
  total_learning_events: number
  last_learning_time: number | null
  auto_learn_enabled: boolean
  trigger_threshold: number
}

interface LearningEvent {
  timestamp: number
  buffer_size: number
  avg_confidence: number
  loss_before: number
  loss_after: number
  success: boolean
}

export function ContinualLearningPanel() {
  const [stats, setStats] = useState<LearningStats | null>(null)
  const [history, setHistory] = useState<LearningEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [triggering, setTriggering] = useState(false)

  const fetchStats = async () => {
    try {
      const response = await fetch('http://192.168.1.4:8000/api/learning/status')
      const data = await response.json()
      if (data.success) {
        setStats(data.data)
      }
    } catch (error) {
      console.error('Failed to fetch learning stats:', error)
    }
  }

  const fetchHistory = async () => {
    try {
      const response = await fetch('http://192.168.1.4:8000/api/learning/history')
      const data = await response.json()
      if (data.success) {
        setHistory(data.data.learning_events)
      }
    } catch (error) {
      console.error('Failed to fetch learning history:', error)
    }
  }

  const triggerLearning = async () => {
    setTriggering(true)
    try {
      const response = await fetch('http://192.168.1.4:8000/api/learning/trigger')
      const data = await response.json()
      if (data.success) {
        alert('Learning triggered successfully! Check the dashboard for updates.')
        setTimeout(() => {
          fetchStats()
          fetchHistory()
        }, 3000)
      } else {
        alert('Failed to trigger learning: ' + (data.error || 'Unknown error'))
      }
    } catch (error) {
      alert('Error triggering learning: ' + error)
    } finally {
      setTriggering(false)
    }
  }

  useEffect(() => {
    fetchStats()
    fetchHistory()
    const interval = setInterval(() => {
      fetchStats()
    }, 10000) // Update every 10 seconds
    return () => clearInterval(interval)
  }, [])

  if (!stats) {
    return (
      <Card className="border-border bg-card">
        <CardContent className="p-6">
          <div className="text-center text-muted-foreground">
            <Brain className="h-12 w-12 mx-auto mb-3 opacity-50" />
            <p>Continual Learning initializing...</p>
            <p className="text-sm">System is collecting experiences</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-4">
      {/* Main Stats Card */}
      <Card className="border-border bg-card">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Brain className="h-5 w-5 text-primary" />
              <CardTitle className="text-sm font-medium">Continual Learning</CardTitle>
            </div>
            <Badge variant={stats.status === 'active' ? 'default' : 'secondary'}>
              {stats.status}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            {/* Experience Buffer */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <span className="flex items-center gap-1">
                  <Database className="h-3 w-3" />
                  Experience Buffer
                </span>
                <span>{stats.buffer_size} / {stats.buffer_max}</span>
              </div>
              <Progress value={stats.fill_percent} className="h-2" />
              <p className="text-xs text-muted-foreground">
                {stats.fill_percent.toFixed(0)}% full
              </p>
            </div>

            {/* Avg Confidence */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <span className="flex items-center gap-1">
                  <TrendingUp className="h-3 w-3" />
                  Avg Confidence
                </span>
                <span>{(stats.avg_confidence * 100).toFixed(0)}%</span>
              </div>
              <Progress 
                value={stats.avg_confidence * 100} 
                className="h-2"
                indicatorClassName={stats.avg_confidence < stats.trigger_threshold ? 'bg-destructive' : 'bg-primary'}
              />
              <p className="text-xs text-muted-foreground">
                Threshold: {(stats.trigger_threshold * 100).toFixed(0)}%
              </p>
            </div>

            {/* Learning Events */}
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-1 text-xs text-muted-foreground">
                <Zap className="h-3 w-3" />
                Learning Events
              </span>
              <span className="font-mono text-lg font-bold text-primary">
                {stats.total_learning_events}
              </span>
            </div>

            {/* Auto-learn Status */}
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-1 text-xs text-muted-foreground">
                <Clock className="h-3 w-3" />
                Auto-Learn
              </span>
              <Badge variant={stats.auto_learn_enabled ? 'default' : 'secondary'} className="text-xs">
                {stats.auto_learn_enabled ? 'ON' : 'OFF'}
              </Badge>
            </div>
          </div>

          {/* Manual Trigger Button */}
          <Button 
            onClick={triggerLearning} 
            disabled={triggering}
            className="w-full mt-4 gap-2"
            variant="outline"
          >
            <RefreshCw className={`h-4 w-4 ${triggering ? 'animate-spin' : ''}`} />
            {triggering ? 'Triggering...' : 'Manually Trigger Learning'}
          </Button>
        </CardContent>
      </Card>

      {/* Learning History */}
      {history.length > 0 && (
        <Card className="border-border bg-card">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Learning History</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {history.map((event, idx) => (
                <div key={idx} className="flex items-center justify-between p-2 rounded-md bg-secondary/30">
                  <div className="flex flex-col">
                    <span className="text-xs font-mono">
                      {new Date(event.timestamp * 1000).toLocaleTimeString()}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      Buffer: {event.buffer_size} samples
                    </span>
                  </div>
                  <div className="flex flex-col items-end">
                    <Badge variant={event.success ? 'default' : 'destructive'} className="text-xs">
                      {event.success ? 'Success' : 'Failed'}
                    </Badge>
                    {event.loss_before > 0 && (
                      <span className="text-xs text-muted-foreground mt-1">
                        Loss: {event.loss_before.toFixed(3)} → {event.loss_after.toFixed(3)}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}