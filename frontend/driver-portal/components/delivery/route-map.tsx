"use client"

import { cn } from "@/lib/utils"
import { MapPin, Navigation } from "lucide-react"

interface RouteMapProps {
  stops: Array<{
    id: string
    name: string
    status: "pending" | "in-progress" | "completed"
  }>
  className?: string
}

export function RouteMap({ stops, className }: RouteMapProps) {
  return (
    <div className={cn(
      "relative bg-gradient-to-br from-[var(--thistle)]/30 via-[var(--muted-teal)]/10 to-[var(--twilight-indigo)]/10 rounded-2xl overflow-hidden border border-border",
      className
    )}>
      {/* Map Background Pattern */}
      <div className="absolute inset-0 opacity-30">
        <svg className="w-full h-full" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="var(--twilight-indigo)" strokeWidth="0.5" opacity="0.3"/>
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" />
        </svg>
      </div>

      {/* Route Line SVG */}
      <svg className="absolute inset-0 w-full h-full" viewBox="0 0 400 200" preserveAspectRatio="xMidYMid meet">
        {/* Main Route Path */}
        <path
          d="M 50 150 Q 100 100 150 120 T 250 80 T 350 100"
          fill="none"
          stroke="var(--muted-teal)"
          strokeWidth="4"
          strokeLinecap="round"
          strokeDasharray="8 4"
          className="animate-pulse"
        />
        
        {/* Completed portion */}
        <path
          d="M 50 150 Q 100 100 150 120"
          fill="none"
          stroke="var(--muted-teal)"
          strokeWidth="4"
          strokeLinecap="round"
        />
      </svg>

      {/* Stop Markers */}
      <div className="relative w-full h-full min-h-[200px] p-4">
        {/* Start Point */}
        <div className="absolute left-[10%] bottom-[20%] transform -translate-x-1/2">
          <div className="flex flex-col items-center">
            <div className="w-10 h-10 rounded-full bg-[var(--muted-teal)] flex items-center justify-center shadow-lg border-2 border-white">
              <Navigation className="w-5 h-5 text-[var(--evergreen)]" />
            </div>
            <span className="mt-1 text-[10px] font-semibold text-[var(--evergreen)] bg-white/80 px-1.5 py-0.5 rounded">
              START
            </span>
          </div>
        </div>

        {/* Stop Points */}
        {stops.slice(0, 4).map((stop, index) => {
          const positions = [
            { left: '35%', bottom: '40%' },
            { left: '55%', bottom: '55%' },
            { left: '75%', bottom: '45%' },
            { left: '90%', bottom: '50%' },
          ]
          const pos = positions[index]
          
          return (
            <div
              key={stop.id}
              className="absolute transform -translate-x-1/2"
              style={{ left: pos.left, bottom: pos.bottom }}
            >
              <div className="flex flex-col items-center">
                <div className={cn(
                  "w-8 h-8 rounded-full flex items-center justify-center shadow-md border-2 border-white font-bold text-xs",
                  stop.status === "completed" 
                    ? "bg-[var(--muted-teal)] text-[var(--evergreen)]"
                    : stop.status === "in-progress"
                      ? "bg-[var(--midnight-violet)] text-white animate-pulse"
                      : "bg-[var(--twilight-indigo)] text-white"
                )}>
                  {index + 1}
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Legend */}
      <div className="absolute bottom-3 left-3 flex items-center gap-3 text-[10px] font-medium">
        <div className="flex items-center gap-1.5 bg-white/80 backdrop-blur-sm px-2 py-1 rounded-full">
          <div className="w-2 h-2 rounded-full bg-[var(--muted-teal)]" />
          <span className="text-[var(--evergreen)]">Completed</span>
        </div>
        <div className="flex items-center gap-1.5 bg-white/80 backdrop-blur-sm px-2 py-1 rounded-full">
          <div className="w-2 h-2 rounded-full bg-[var(--twilight-indigo)]" />
          <span className="text-[var(--twilight-indigo)]">Pending</span>
        </div>
      </div>

      {/* Map Attribution Style */}
      <div className="absolute bottom-3 right-3 text-[9px] text-muted-foreground/60 bg-white/60 px-1.5 py-0.5 rounded">
        Route Preview
      </div>
    </div>
  )
}
