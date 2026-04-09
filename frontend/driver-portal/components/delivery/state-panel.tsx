import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import type { LucideIcon } from "lucide-react"

interface StatePanelProps {
  icon: LucideIcon
  title: string
  message: string
  actionLabel?: string
  onAction?: () => void
  className?: string
}

export function StatePanel({
  icon: Icon,
  title,
  message,
  actionLabel,
  onAction,
  className,
}: StatePanelProps) {
  return (
    <div className={cn("bg-card rounded-2xl border border-border p-6 text-center", className)}>
      <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-[var(--muted-teal)]/10">
        <Icon className="h-6 w-6 text-[var(--muted-teal)]" />
      </div>
      <h2 className="text-lg font-semibold text-foreground">{title}</h2>
      <p className="mt-2 text-sm text-muted-foreground">{message}</p>
      {actionLabel && onAction ? (
        <Button onClick={onAction} className="mt-5 bg-[var(--evergreen)] hover:bg-[var(--evergreen)]/90 text-white">
          {actionLabel}
        </Button>
      ) : null}
    </div>
  )
}
