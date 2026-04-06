"use client"

import { cn } from "@/lib/utils"
import type { LucideIcon } from "lucide-react"

interface MetricCardProps {
  title: string
  value: string | number
  subtitle?: string
  icon: LucideIcon
  variant?: "default" | "primary" | "accent" | "muted"
  className?: string
}

const variantStyles = {
  default: "bg-card border border-border",
  primary: "bg-[var(--muted-teal)]/10 border border-[var(--muted-teal)]/30",
  accent: "bg-[var(--midnight-violet)]/10 border border-[var(--midnight-violet)]/20",
  muted: "bg-[var(--thistle)]/30 border border-[var(--thistle)]"
}

const iconVariantStyles = {
  default: "bg-[var(--twilight-indigo)]/10 text-[var(--twilight-indigo)]",
  primary: "bg-[var(--muted-teal)]/20 text-[var(--evergreen)]",
  accent: "bg-[var(--midnight-violet)]/20 text-[var(--midnight-violet)]",
  muted: "bg-[var(--thistle)] text-[var(--twilight-indigo)]"
}

export function MetricCard({ 
  title, 
  value, 
  subtitle, 
  icon: Icon, 
  variant = "default",
  className 
}: MetricCardProps) {
  return (
    <div
      className={cn(
        "rounded-xl p-4 transition-all",
        variantStyles[variant],
        className
      )}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-muted-foreground truncate">
            {title}
          </p>
          <p className="mt-1 text-2xl font-bold tracking-tight text-foreground">
            {value}
          </p>
          {subtitle && (
            <p className="mt-0.5 text-xs text-muted-foreground">
              {subtitle}
            </p>
          )}
        </div>
        <div className={cn(
          "flex-shrink-0 p-2.5 rounded-lg",
          iconVariantStyles[variant]
        )}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
    </div>
  )
}
