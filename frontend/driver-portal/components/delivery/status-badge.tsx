"use client"

import { cn } from "@/lib/utils"

type DeliveryStatus = 
  | "pending" 
  | "in-progress" 
  | "completed" 
  | "delayed" 
  | "exception" 
  | "not-started"

interface StatusBadgeProps {
  status: DeliveryStatus
  className?: string
}

const statusConfig: Record<DeliveryStatus, { label: string; className: string }> = {
  "pending": {
    label: "Pending",
    className: "bg-[var(--thistle)] text-[var(--twilight-indigo)]"
  },
  "in-progress": {
    label: "In Progress",
    className: "bg-[var(--muted-teal)]/20 text-[var(--evergreen)] border border-[var(--muted-teal)]"
  },
  "completed": {
    label: "Completed",
    className: "bg-[var(--muted-teal)] text-[var(--evergreen)]"
  },
  "delayed": {
    label: "Delayed",
    className: "bg-amber-100 text-amber-800 border border-amber-300"
  },
  "exception": {
    label: "Exception",
    className: "bg-red-100 text-red-800 border border-red-300"
  },
  "not-started": {
    label: "Not Started",
    className: "bg-[var(--twilight-indigo)]/10 text-[var(--twilight-indigo)] border border-[var(--twilight-indigo)]/20"
  }
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const config = statusConfig[status]
  
  return (
    <span
      className={cn(
        "inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold tracking-wide",
        config.className,
        className
      )}
    >
      {config.label}
    </span>
  )
}
