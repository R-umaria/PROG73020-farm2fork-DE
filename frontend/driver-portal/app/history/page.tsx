"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { AppShell } from "@/components/delivery/app-shell"
import { PageHeader } from "@/components/delivery/page-header"
import { StatusBadge } from "@/components/delivery/status-badge"
import { cn } from "@/lib/utils"
import { 
  MapPin, 
  Clock, 
  CheckCircle2,
  AlertTriangle,
  Filter
} from "lucide-react"

type FilterTab = "all" | "scheduled" | "delivered" | "exceptions"

const deliveryHistory = [
  {
    id: "1",
    stopNumber: 1,
    customerName: "Green Valley Farms",
    address: "1234 Rural Route 7, Riverside",
    timeWindow: "8:00 - 9:00 AM",
    completedTime: "8:45 AM",
    status: "delivered" as const,
  },
  {
    id: "2",
    stopNumber: 2,
    customerName: "Sunrise Organic Co-op",
    address: "567 Market Street, Downtown",
    timeWindow: "9:30 - 10:30 AM",
    completedTime: null,
    status: "out_for_delivery" as const,
  },
  {
    id: "3",
    stopNumber: 3,
    customerName: "The Corner Bistro",
    address: "890 Main Avenue, Midtown",
    timeWindow: "11:00 AM - 12:00 PM",
    completedTime: null,
    status: "scheduled" as const,
  },
  {
    id: "4",
    stopNumber: 4,
    customerName: "Healthy Harvest Market",
    address: "234 Oak Boulevard, Westside",
    timeWindow: "12:30 - 1:30 PM",
    completedTime: null,
    status: "scheduled" as const,
  },
  {
    id: "5",
    stopNumber: 5,
    customerName: "Farm Fresh Deli",
    address: "456 Pine Street, Eastside",
    timeWindow: "2:00 - 3:00 PM",
    completedTime: null,
    status: "scheduled" as const,
  },
]

const tabs: { id: FilterTab; label: string; count: number }[] = [
  { id: "all", label: "All", count: 5 },
  { id: "scheduled", label: "Scheduled", count: 3 },
  { id: "delivered", label: "Delivered", count: 1 },
  { id: "exceptions", label: "Exceptions", count: 0 },
]

export default function HistoryPage() {
  const router = useRouter()
  const [activeTab, setActiveTab] = useState<FilterTab>("all")

  const filteredDeliveries = deliveryHistory.filter(delivery => {
    if (activeTab === "all") return true
    if (activeTab === "scheduled") return delivery.status === "scheduled" || delivery.status === "out_for_delivery"
    if (activeTab === "delivered") return delivery.status === "delivered"
    if (activeTab === "exceptions") return delivery.status === "failed"
    return true
  })

  const completedCount = deliveryHistory.filter(d => d.status === "delivered").length
  const pendingCount = deliveryHistory.filter(d => d.status === "scheduled" || d.status === "out_for_delivery").length

  return (
    <AppShell>
      <PageHeader 
        title="Delivery History"
        subtitle="March 27, 2026"
        actions={
          <button className="p-2 rounded-lg hover:bg-white/10 transition-colors">
            <Filter className="w-5 h-5 text-white" />
          </button>
        }
      />

      <main className="px-4 py-6 max-w-4xl mx-auto space-y-6">
        {/* Summary Stats */}
        <div className="flex items-center gap-4 bg-card rounded-xl p-4 border border-border">
          <div className="flex-1 text-center">
            <div className="flex items-center justify-center gap-2 text-[var(--muted-teal)]">
              <CheckCircle2 className="w-5 h-5" />
              <span className="text-2xl font-bold">{completedCount}</span>
            </div>
            <p className="text-xs text-muted-foreground mt-1">Delivered</p>
          </div>
          <div className="w-px h-12 bg-border" />
          <div className="flex-1 text-center">
            <div className="flex items-center justify-center gap-2 text-[var(--twilight-indigo)]">
              <Clock className="w-5 h-5" />
              <span className="text-2xl font-bold">{pendingCount}</span>
            </div>
            <p className="text-xs text-muted-foreground mt-1">Remaining</p>
          </div>
          <div className="w-px h-12 bg-border" />
          <div className="flex-1 text-center">
            <div className="flex items-center justify-center gap-2 text-amber-500">
              <AlertTriangle className="w-5 h-5" />
              <span className="text-2xl font-bold">0</span>
            </div>
            <p className="text-xs text-muted-foreground mt-1">Exceptions</p>
          </div>
        </div>

        {/* Filter Tabs */}
        <div className="flex gap-2 overflow-x-auto pb-1 -mx-4 px-4 scrollbar-hide">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                "flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-all whitespace-nowrap",
                activeTab === tab.id
                  ? "bg-[var(--evergreen)] text-white"
                  : "bg-muted text-muted-foreground hover:bg-muted/80"
              )}
            >
              {tab.label}
              <span className={cn(
                "px-1.5 py-0.5 rounded-full text-xs",
                activeTab === tab.id
                  ? "bg-white/20"
                  : "bg-background"
              )}>
                {tab.count}
              </span>
            </button>
          ))}
        </div>

        {/* Delivery List */}
        <div className="space-y-3">
          {filteredDeliveries.length === 0 ? (
            <div className="text-center py-12">
              <div className="w-16 h-16 rounded-full bg-muted mx-auto mb-4 flex items-center justify-center">
                <Clock className="w-8 h-8 text-muted-foreground" />
              </div>
              <p className="text-muted-foreground">No deliveries in this category</p>
            </div>
          ) : (
            filteredDeliveries.map((delivery) => (
              <button
                key={delivery.id}
                onClick={() => router.push(`/deliveries/${delivery.id}`)}
                className={cn(
                  "w-full bg-card rounded-xl p-4 border transition-all text-left",
                  delivery.status === "out_for_delivery"
                    ? "border-[var(--muted-teal)] shadow-md"
                    : "border-border hover:border-[var(--muted-teal)]/50"
                )}
              >
                <div className="flex items-start gap-3">
                  {/* Stop Number */}
                  <div className={cn(
                    "flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center font-bold text-sm",
                    delivery.status === "delivered"
                      ? "bg-[var(--muted-teal)] text-[var(--evergreen)]"
                      : delivery.status === "out_for_delivery"
                        ? "bg-[var(--midnight-violet)] text-white"
                        : "bg-muted text-muted-foreground"
                  )}>
                    {delivery.status === "delivered" ? (
                      <CheckCircle2 className="w-5 h-5" />
                    ) : (
                      `#${delivery.stopNumber}`
                    )}
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0">
                        <h3 className="font-semibold text-foreground truncate">
                          {delivery.customerName}
                        </h3>
                        <div className="flex items-center gap-1.5 mt-1 text-sm text-muted-foreground">
                          <MapPin className="w-3.5 h-3.5 flex-shrink-0" />
                          <span className="truncate">{delivery.address}</span>
                        </div>
                      </div>
                      <StatusBadge status={delivery.status} />
                    </div>

                    <div className="flex items-center justify-between mt-3">
                      <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                        <Clock className="w-3.5 h-3.5" />
                        <span>{delivery.timeWindow}</span>
                      </div>
                      {delivery.completedTime && (
                        <span className="text-xs text-[var(--muted-teal)] font-medium">
                          Delivered {delivery.completedTime}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </button>
            ))
          )}
        </div>
      </main>
    </AppShell>
  )
}
