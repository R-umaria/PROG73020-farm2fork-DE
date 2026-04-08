"use client"

import { useRouter } from "next/navigation"
import { AppShell } from "@/components/delivery/app-shell"
import { PageHeader } from "@/components/delivery/page-header"
import { MetricCard } from "@/components/delivery/metric-card"
import { DeliveryCard } from "@/components/delivery/delivery-card"
import { StatusBadge } from "@/components/delivery/status-badge"
import { Button } from "@/components/ui/button"
import { 
  Package, 
  CheckCircle2, 
  Clock, 
  MapPin, 
  Timer,
  Play,
  ChevronRight
} from "lucide-react"

// Sample delivery data
const todayDeliveries = [
  {
    id: "1",
    stopNumber: 1,
    customerName: "Green Valley Farms",
    address: "1234 Rural Route 7, Riverside",
    timeWindow: "8:00 - 9:00 AM",
    deliveryType: "Produce Box",
    status: "completed" as const,
  },
  {
    id: "2",
    stopNumber: 2,
    customerName: "Sunrise Organic Co-op",
    address: "567 Market Street, Downtown",
    timeWindow: "9:30 - 10:30 AM",
    deliveryType: "Mixed Crate",
    status: "in-progress" as const,
  },
  {
    id: "3",
    stopNumber: 3,
    customerName: "The Corner Bistro",
    address: "890 Main Avenue, Midtown",
    timeWindow: "11:00 AM - 12:00 PM",
    deliveryType: "Restaurant Order",
    status: "pending" as const,
  },
  {
    id: "4",
    stopNumber: 4,
    customerName: "Healthy Harvest Market",
    address: "234 Oak Boulevard, Westside",
    timeWindow: "12:30 - 1:30 PM",
    deliveryType: "Bulk Produce",
    status: "pending" as const,
  },
  {
    id: "5",
    stopNumber: 5,
    customerName: "Farm Fresh Deli",
    address: "456 Pine Street, Eastside",
    timeWindow: "2:00 - 3:00 PM",
    deliveryType: "Produce Box",
    status: "pending" as const,
  },
]

export default function DashboardPage() {
  const router = useRouter()
  
  const completedCount = todayDeliveries.filter(d => d.status === "completed").length
  const pendingCount = todayDeliveries.filter(d => d.status === "pending" || d.status === "in-progress").length

  return (
    <AppShell>
      <PageHeader 
        title="Good morning, Marcus"
        subtitle="Thursday, March 27, 2026"
        showNotifications
      />

      <main className="px-4 py-6 max-w-4xl mx-auto space-y-6">
        {/* Shift Status Banner */}
        <div className="bg-[var(--midnight-violet)] rounded-2xl p-4 text-white">
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <StatusBadge status="in-progress" />
              </div>
              <p className="text-sm text-white/70 mt-2">
                Route NE-47 | North Valley Region
              </p>
            </div>
            <div className="text-right">
              <p className="text-2xl font-bold">1 of 5</p>
              <p className="text-xs text-white/60">stops completed</p>
            </div>
          </div>
          
          {/* Progress Bar */}
          <div className="mt-4">
            <div className="h-2 bg-white/20 rounded-full overflow-hidden">
              <div 
                className="h-full bg-[var(--muted-teal)] rounded-full transition-all duration-500"
                style={{ width: `${(completedCount / todayDeliveries.length) * 100}%` }}
              />
            </div>
            <p className="text-xs text-white/60 mt-2">
              Estimated completion: 3:15 PM
            </p>
          </div>
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-2 gap-3">
          <MetricCard
            title="Total Deliveries"
            value={todayDeliveries.length}
            subtitle="assigned today"
            icon={Package}
            variant="default"
          />
          <MetricCard
            title="Completed"
            value={completedCount}
            subtitle={`${Math.round((completedCount / todayDeliveries.length) * 100)}% done`}
            icon={CheckCircle2}
            variant="primary"
          />
          <MetricCard
            title="Pending"
            value={pendingCount}
            subtitle="remaining"
            icon={Clock}
            variant="muted"
          />
          <MetricCard
            title="Est. Duration"
            value="4.5 hrs"
            subtitle="~42 miles"
            icon={Timer}
            variant="accent"
          />
        </div>

        {/* Start/Continue Delivering CTA */}
        <Button
          onClick={() => router.push("/deliveries/2")}
          className="w-full h-14 bg-[var(--muted-teal)] hover:bg-[var(--muted-teal)]/90 text-[var(--evergreen)] font-semibold text-base rounded-xl shadow-lg shadow-[var(--muted-teal)]/20"
        >
          <Play className="w-5 h-5 mr-2" />
          Continue Delivering
          <ChevronRight className="w-5 h-5 ml-auto" />
        </Button>

        {/* Today's Deliveries List */}
        <section>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-foreground">
              {"Today's Schedule"}
            </h2>
            <button 
              onClick={() => router.push("/route")}
              className="text-sm font-medium text-[var(--twilight-indigo)] flex items-center gap-1 hover:text-[var(--midnight-violet)] transition-colors"
            >
              View Route
              <MapPin className="w-4 h-4" />
            </button>
          </div>

          <div className="space-y-3">
            {todayDeliveries.map((delivery) => (
              <DeliveryCard
                key={delivery.id}
                {...delivery}
                isActive={delivery.status === "in-progress"}
                onClick={() => router.push(`/deliveries/${delivery.id}`)}
              />
            ))}
          </div>
        </section>
      </main>
    </AppShell>
  )
}
