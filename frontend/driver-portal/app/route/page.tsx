"use client"

import { useRouter } from "next/navigation"
import { AppShell } from "@/components/delivery/app-shell"
import { PageHeader } from "@/components/delivery/page-header"
import { RouteMap } from "@/components/delivery/route-map"
import { DeliveryCard } from "@/components/delivery/delivery-card"
import { Button } from "@/components/ui/button"
import { 
  MapPin, 
  Clock, 
  Truck, 
  User,
  Route,
  Navigation,
  ChevronRight
} from "lucide-react"

const routeStops = [
  { id: "1", name: "Green Valley Farms", status: "completed" as const },
  { id: "2", name: "Sunrise Organic Co-op", status: "in-progress" as const },
  { id: "3", name: "The Corner Bistro", status: "pending" as const },
  { id: "4", name: "Healthy Harvest Market", status: "pending" as const },
  { id: "5", name: "Farm Fresh Deli", status: "pending" as const },
]

const deliveryDetails = [
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

export default function RouteOverviewPage() {
  const router = useRouter()

  return (
    <AppShell>
      <PageHeader 
        title="Route Overview"
        subtitle="Route NE-47"
        backHref="/dashboard"
      />

      <main className="px-4 py-6 max-w-4xl mx-auto space-y-6">
        {/* Route Map */}
        <RouteMap stops={routeStops} className="h-[220px]" />

        {/* Route Info Cards */}
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-card rounded-xl p-4 border border-border">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-[var(--muted-teal)]/10">
                <Route className="w-5 h-5 text-[var(--muted-teal)]" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Route ID</p>
                <p className="font-semibold text-foreground">NE-47</p>
              </div>
            </div>
          </div>
          
          <div className="bg-card rounded-xl p-4 border border-border">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-[var(--twilight-indigo)]/10">
                <MapPin className="w-5 h-5 text-[var(--twilight-indigo)]" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Region</p>
                <p className="font-semibold text-foreground">North Valley</p>
              </div>
            </div>
          </div>
          
          <div className="bg-card rounded-xl p-4 border border-border">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-[var(--midnight-violet)]/10">
                <User className="w-5 h-5 text-[var(--midnight-violet)]" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Driver</p>
                <p className="font-semibold text-foreground">Marcus Chen</p>
              </div>
            </div>
          </div>
          
          <div className="bg-card rounded-xl p-4 border border-border">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-[var(--thistle)]">
                <Truck className="w-5 h-5 text-[var(--twilight-indigo)]" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Vehicle</p>
                <p className="font-semibold text-foreground">Van #12</p>
              </div>
            </div>
          </div>
        </div>

        {/* Route Summary Stats */}
        <div className="bg-[var(--evergreen)] rounded-2xl p-5 text-white">
          <h3 className="text-sm font-medium text-white/70 mb-4">Route Summary</h3>
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center">
              <p className="text-3xl font-bold">5</p>
              <p className="text-xs text-white/60 mt-1">Total Stops</p>
            </div>
            <div className="text-center border-x border-white/20">
              <p className="text-3xl font-bold">42</p>
              <p className="text-xs text-white/60 mt-1">Miles</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-bold">4.5</p>
              <p className="text-xs text-white/60 mt-1">Hours Est.</p>
            </div>
          </div>
        </div>

        {/* Navigate to Active Button */}
        <Button
          onClick={() => router.push("/deliveries/2")}
          className="w-full h-14 bg-[var(--muted-teal)] hover:bg-[var(--muted-teal)]/90 text-[var(--evergreen)] font-semibold text-base rounded-xl"
        >
          <Navigation className="w-5 h-5 mr-2" />
          Navigate to Current Stop
          <ChevronRight className="w-5 h-5 ml-auto" />
        </Button>

        {/* Ordered Stop List */}
        <section>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-foreground flex items-center gap-2">
              <Clock className="w-5 h-5 text-muted-foreground" />
              Stop Sequence
            </h2>
            <span className="text-sm text-muted-foreground">
              1 of 5 completed
            </span>
          </div>

          <div className="space-y-3">
            {deliveryDetails.map((delivery) => (
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
