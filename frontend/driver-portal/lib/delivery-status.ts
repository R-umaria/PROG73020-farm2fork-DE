export type DeliveryStatus =
  | "scheduled"
  | "out_for_delivery"
  | "delivered"
  | "failed"

export const deliveryStatusConfig: Record<
  DeliveryStatus,
  { label: string; className: string }
> = {
  scheduled: {
    label: "Scheduled",
    className: "bg-[var(--thistle)] text-[var(--twilight-indigo)]",
  },
  out_for_delivery: {
    label: "Out for Delivery",
    className:
      "bg-[var(--muted-teal)]/20 text-[var(--evergreen)] border border-[var(--muted-teal)]",
  },
  delivered: {
    label: "Delivered",
    className: "bg-[var(--muted-teal)] text-[var(--evergreen)]",
  },
  failed: {
    label: "Failed",
    className: "bg-red-100 text-red-800 border border-red-300",
  },
}
