"use client"

import { cn } from "@/lib/utils"
import { Check, Circle, Clock } from "lucide-react"

interface TimelineStep {
  label: string
  time?: string
  status: "completed" | "current" | "pending"
}

interface ProgressTimelineProps {
  steps: TimelineStep[]
  className?: string
}

export function ProgressTimeline({ steps, className }: ProgressTimelineProps) {
  return (
    <div className={cn("space-y-0", className)}>
      {steps.map((step, index) => {
        const isLast = index === steps.length - 1
        
        return (
          <div key={index} className="relative flex gap-3">
            {/* Line connector */}
            {!isLast && (
              <div 
                className={cn(
                  "absolute left-[11px] top-6 w-0.5 h-[calc(100%-8px)]",
                  step.status === "completed" 
                    ? "bg-[var(--muted-teal)]" 
                    : "bg-border"
                )}
              />
            )}
            
            {/* Icon */}
            <div className="flex-shrink-0 relative z-10">
              {step.status === "completed" ? (
                <div className="w-6 h-6 rounded-full bg-[var(--muted-teal)] flex items-center justify-center">
                  <Check className="w-3.5 h-3.5 text-[var(--evergreen)]" />
                </div>
              ) : step.status === "current" ? (
                <div className="w-6 h-6 rounded-full bg-[var(--midnight-violet)] flex items-center justify-center animate-pulse">
                  <Clock className="w-3.5 h-3.5 text-white" />
                </div>
              ) : (
                <div className="w-6 h-6 rounded-full bg-muted flex items-center justify-center">
                  <Circle className="w-3 h-3 text-muted-foreground" />
                </div>
              )}
            </div>

            {/* Content */}
            <div className={cn(
              "flex-1 pb-4",
              isLast && "pb-0"
            )}>
              <p className={cn(
                "text-sm font-medium",
                step.status === "pending" 
                  ? "text-muted-foreground" 
                  : "text-foreground"
              )}>
                {step.label}
              </p>
              {step.time && (
                <p className="text-xs text-muted-foreground mt-0.5">
                  {step.time}
                </p>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}
