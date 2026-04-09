import { format } from "date-fns"

export function formatLongDate(value: Date): string {
  return format(value, "EEEE, MMMM d, yyyy")
}

export function formatShortTime(value: string | Date | null | undefined): string {
  if (!value) {
    return "Pending"
  }

  const parsed = value instanceof Date ? value : new Date(value)
  if (Number.isNaN(parsed.getTime())) {
    return "Pending"
  }

  return format(parsed, "h:mm a")
}

export function formatTimeWindow(estimatedArrival: string | null, sequence: number): string {
  if (!estimatedArrival) {
    return `Stop ${sequence}`
  }

  return `ETA ${formatShortTime(estimatedArrival)}`
}

export function formatRouteLabel(routeGroupId: string | null | undefined): string {
  if (!routeGroupId) {
    return "Pending route"
  }

  return `Route ${routeGroupId.slice(0, 8).toUpperCase()}`
}
