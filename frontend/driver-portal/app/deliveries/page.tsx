"use client"

import { useRouter } from "next/navigation"
import { AppShell } from "@/components/delivery/app-shell"
import { PageHeader } from "@/components/delivery/page-header"
import { DeliveryCard } from "@/components/delivery/delivery-card"
import { Button } from "@/components/ui/button"
import { 
  Package, 
  Search,
  SlidersHorizontal
} from "lucide-react"
import { Input } from "@/components/ui/input"

const allDeliveries = [
  {
    id: "1",
    stopNumber: 1,
    customerName: "Green Valley Farms",
    address: "1234 Rural Route 7, Riverside",
    timeWindow: "8:00 - 9:00 AM",
    deliveryType: "Produce Box",
    status: "delivered" as const,
  },
  {
    id: "2",
    stopNumber: 2,
    customerName: "Sunrise Organic Co-op",
    address: "567 Market Street, Downtown",
    timeWindow: "9:30 - 10:30 AM",
    deliveryType: "Mixed Crate",
    status: "out_for_delivery" as const,
  },
  {
    id: "3",
    stopNumber: 3,
    customerName: "The Corner Bistro",
    address: "890 Main Avenue, Midtown",
    timeWindow: "11:00 AM - 12:00 PM",
    deliveryType: "Restaurant Order",
    status: "scheduled" as const,
  },
  {
    id: "4",
    stopNumber: 4,
    customerName: "Healthy Harvest Market",
    address: "234 Oak Boulevard, Westside",
    timeWindow: "12:30 - 1:30 PM",
    deliveryType: "Bulk Produce",
    status: "scheduled" as const,
  },
  {
    id: "5",
    stopNumber: 5,
    customerName: "Farm Fresh Deli",
    address: "456 Pine Street, Eastside",
    timeWindow: "2:00 - 3:00 PM",
    deliveryType: "Produce Box",
    status: "scheduled" as const,
  },
]

export default function DeliveriesPage() {
  const router = useRouter()

  return (
    <AppShell>
      <PageHeader 
        title="Deliveries"
        subtitle="5 stops assigned"
        actions={
          <Button 
            variant="ghost" 
            size="icon"
            className="text-white hover:bg-white/10"
          >
            <SlidersHorizontal className="w-5 h-5" />
          </Button>
        }
      />

      <main className="px-4 py-6 max-w-4xl mx-auto space-y-5">
        {/* Search Bar */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
          <Input 
            placeholder="Search deliveries..."
            className="pl-10 h-12 bg-card border-border rounded-xl"
          />
        </div>

        {/* Quick Stats */}
        <div className="flex items-center gap-3">
          <div className="flex-1 bg-[var(--muted-teal)]/10 rounded-xl p-3 border border-[var(--muted-teal)]/20">
            <div className="flex items-center gap-2">
              <Package className="w-4 h-4 text-[var(--muted-teal)]" />
              <span className="text-sm font-medium text-foreground">1 Delivered</span>
            </div>
          </div>
          <div className="flex-1 bg-[var(--midnight-violet)]/10 rounded-xl p-3 border border-[var(--midnight-violet)]/20">
            <div className="flex items-center gap-2">
              <Package className="w-4 h-4 text-[var(--midnight-violet)]" />
              <span className="text-sm font-medium text-foreground">1 In Transit</span>
            </div>
          </div>
          <div className="flex-1 bg-muted rounded-xl p-3 border border-border">
            <div className="flex items-center gap-2">
              <Package className="w-4 h-4 text-muted-foreground" />
              <span className="text-sm font-medium text-foreground">3 Scheduled</span>
            </div>
          </div>
        </div>

        {/* Deliveries List */}
        <section>
          <h2 className="text-sm font-medium text-muted-foreground mb-3">
            All Deliveries
          </h2>
          <div className="space-y-3">
            {allDeliveries.map((delivery) => (
              <DeliveryCard
                key={delivery.id}
                {...delivery}
                isActive={delivery.status === "out_for_delivery"}
                onClick={() => router.push(`/deliveries/${delivery.id}`)}
              />
            ))}
          </div>
        </section>
      </main>
    </AppShell>
  )
}
