"use client"

import { useState } from "react"
import { useRouter, useParams } from "next/navigation"
import { AppShell } from "@/components/delivery/app-shell"
import { PageHeader } from "@/components/delivery/page-header"
import { StatusBadge } from "@/components/delivery/status-badge"
import { ProgressTimeline } from "@/components/delivery/progress-timeline"
import { Button } from "@/components/ui/button"
import { 
  MapPin, 
  Phone, 
  FileText, 
  Clock, 
  Navigation,
  CheckCircle2,
  AlertTriangle,
  Package,
  User,
  Camera,
  ChevronRight
} from "lucide-react"

// Sample delivery data
const deliveriesData: Record<string, {
  id: string
  stopNumber: number
  customerName: string
  address: string
  phone: string
  orderId: string
  deliveryNotes: string
  timeWindow: string
  deliveryType: string
  status: "scheduled" | "out_for_delivery" | "delivered" | "failed"
  items: string[]
}> = {
  "1": {
    id: "1",
    stopNumber: 1,
    customerName: "Green Valley Farms",
    address: "1234 Rural Route 7, Riverside, CA 92501",
    phone: "(555) 123-4567",
    orderId: "ORD-2026-0847",
    deliveryNotes: "Leave at loading dock. Ring bell twice for attendant.",
    timeWindow: "8:00 - 9:00 AM",
    deliveryType: "Produce Box",
    status: "delivered",
    items: ["Organic Tomatoes (5 lbs)", "Mixed Greens (2 cases)", "Fresh Herbs Bundle"],
  },
  "2": {
    id: "2",
    stopNumber: 2,
    customerName: "Sunrise Organic Co-op",
    address: "567 Market Street, Downtown, CA 92502",
    phone: "(555) 234-5678",
    orderId: "ORD-2026-0848",
    deliveryNotes: "Deliver to back entrance. Ask for Sarah at receiving.",
    timeWindow: "9:30 - 10:30 AM",
    deliveryType: "Mixed Crate",
    status: "out_for_delivery",
    items: ["Seasonal Fruit Mix (3 crates)", "Root Vegetables (2 boxes)", "Eggs (10 dozen)"],
  },
  "3": {
    id: "3",
    stopNumber: 3,
    customerName: "The Corner Bistro",
    address: "890 Main Avenue, Midtown, CA 92503",
    phone: "(555) 345-6789",
    orderId: "ORD-2026-0849",
    deliveryNotes: "Kitchen entrance on side street. Temperature sensitive items.",
    timeWindow: "11:00 AM - 12:00 PM",
    deliveryType: "Restaurant Order",
    status: "scheduled",
    items: ["Premium Salad Mix (4 cases)", "Cherry Tomatoes (20 lbs)", "Microgreens (5 containers)"],
  },
  "4": {
    id: "4",
    stopNumber: 4,
    customerName: "Healthy Harvest Market",
    address: "234 Oak Boulevard, Westside, CA 92504",
    phone: "(555) 456-7890",
    orderId: "ORD-2026-0850",
    deliveryNotes: "Use freight elevator. Stock room on second floor.",
    timeWindow: "12:30 - 1:30 PM",
    deliveryType: "Bulk Produce",
    status: "scheduled",
    items: ["Assorted Apples (50 lbs)", "Citrus Mix (30 lbs)", "Leafy Greens (6 cases)"],
  },
  "5": {
    id: "5",
    stopNumber: 5,
    customerName: "Farm Fresh Deli",
    address: "456 Pine Street, Eastside, CA 92505",
    phone: "(555) 567-8901",
    orderId: "ORD-2026-0851",
    deliveryNotes: "Front door delivery. Call upon arrival.",
    timeWindow: "2:00 - 3:00 PM",
    deliveryType: "Produce Box",
    status: "scheduled",
    items: ["Sandwich Vegetables (2 cases)", "Fresh Herbs (1 box)", "Specialty Lettuce (3 cases)"],
  },
}

export default function DeliveryDetailPage() {
  const router = useRouter()
  const params = useParams()
  const deliveryId = params.id as string
  const delivery = deliveriesData[deliveryId] || deliveriesData["2"]
  
  const [currentStatus, setCurrentStatus] = useState<"scheduled" | "out_for_delivery" | "delivered">(
    delivery.status === "delivered" ? "delivered" : delivery.status === "out_for_delivery" ? "out_for_delivery" : "scheduled"
  )

  const timelineSteps = [
    {
      label: "Order Assigned",
      time: "7:30 AM",
      status: "completed" as const,
    },
    {
      label: "En Route",
      time: currentStatus !== "scheduled" ? "9:15 AM" : undefined,
      status: currentStatus !== "scheduled" ? "completed" as const : "pending" as const,
    },
    {
      label: "Arrived at Location",
      time: currentStatus === "delivered" ? "9:28 AM" : undefined,
      status: currentStatus === "delivered" ? "completed" as const : currentStatus === "out_for_delivery" ? "current" as const : "pending" as const,
    },
    {
      label: "Delivery Completed",
      time: currentStatus === "delivered" ? "9:35 AM" : undefined,
      status: currentStatus === "delivered" ? "completed" as const : "pending" as const,
    },
  ]

  const handleMarkArrived = () => {
    setCurrentStatus("out_for_delivery")
  }

  const handleMarkComplete = () => {
    setCurrentStatus("delivered")
  }

  return (
    <AppShell>
      <PageHeader 
        title={`Stop #${delivery.stopNumber}`}
        subtitle={delivery.customerName}
        backHref="/dashboard"
      />

      <main className="px-4 py-6 max-w-4xl mx-auto space-y-5">
        {/* Status Banner */}
        <div className="flex items-center justify-between bg-card rounded-xl p-4 border border-border">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-[var(--muted-teal)]/10">
              <Package className="w-6 h-6 text-[var(--muted-teal)]" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Order ID</p>
              <p className="font-semibold text-foreground">{delivery.orderId}</p>
            </div>
          </div>
          <StatusBadge status={currentStatus} />
        </div>

        {/* Customer Info Card */}
        <div className="bg-card rounded-xl p-5 border border-border space-y-4">
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-lg bg-[var(--twilight-indigo)]/10">
              <User className="w-5 h-5 text-[var(--twilight-indigo)]" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm text-muted-foreground">Customer</p>
              <p className="font-semibold text-foreground text-lg">{delivery.customerName}</p>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <div className="p-2 rounded-lg bg-[var(--muted-teal)]/10">
              <MapPin className="w-5 h-5 text-[var(--muted-teal)]" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm text-muted-foreground">Delivery Address</p>
              <p className="font-medium text-foreground">{delivery.address}</p>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <div className="p-2 rounded-lg bg-[var(--midnight-violet)]/10">
              <Phone className="w-5 h-5 text-[var(--midnight-violet)]" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm text-muted-foreground">Contact</p>
              <a href={`tel:${delivery.phone}`} className="font-medium text-[var(--twilight-indigo)] hover:underline">
                {delivery.phone}
              </a>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <div className="p-2 rounded-lg bg-[var(--thistle)]">
              <Clock className="w-5 h-5 text-[var(--twilight-indigo)]" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm text-muted-foreground">Delivery Window</p>
              <p className="font-medium text-foreground">{delivery.timeWindow}</p>
            </div>
          </div>
        </div>

        {/* Delivery Notes */}
        <div className="bg-[var(--thistle)]/30 rounded-xl p-4 border border-[var(--thistle)]">
          <div className="flex items-start gap-3">
            <FileText className="w-5 h-5 text-[var(--twilight-indigo)] flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-[var(--twilight-indigo)]">Delivery Instructions</p>
              <p className="text-sm text-foreground mt-1">{delivery.deliveryNotes}</p>
            </div>
          </div>
        </div>

        {/* Items List */}
        <div className="bg-card rounded-xl p-5 border border-border">
          <h3 className="font-semibold text-foreground mb-3 flex items-center gap-2">
            <Package className="w-5 h-5 text-muted-foreground" />
            Items ({delivery.items.length})
          </h3>
          <ul className="space-y-2">
            {delivery.items.map((item, index) => (
              <li key={index} className="flex items-center gap-3 text-sm">
                <div className="w-1.5 h-1.5 rounded-full bg-[var(--muted-teal)]" />
                <span className="text-foreground">{item}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Status Timeline */}
        <div className="bg-card rounded-xl p-5 border border-border">
          <h3 className="font-semibold text-foreground mb-4">Delivery Progress</h3>
          <ProgressTimeline steps={timelineSteps} />
        </div>

        {/* Proof of Delivery Placeholder */}
        {currentStatus === "delivered" && (
          <div className="bg-[var(--muted-teal)]/10 rounded-xl p-4 border border-[var(--muted-teal)]/30">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-[var(--muted-teal)]/20">
                <Camera className="w-5 h-5 text-[var(--muted-teal)]" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-[var(--evergreen)]">Proof of Delivery</p>
                <p className="text-xs text-muted-foreground">Photo captured at 9:35 AM</p>
              </div>
              <CheckCircle2 className="w-5 h-5 text-[var(--muted-teal)]" />
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="space-y-3 pt-2">
          {currentStatus === "scheduled" && (
            <>
              <Button
                onClick={() => window.open(`https://maps.google.com/?q=${encodeURIComponent(delivery.address)}`, '_blank')}
                className="w-full h-14 bg-[var(--twilight-indigo)] hover:bg-[var(--twilight-indigo)]/90 text-white font-semibold rounded-xl"
              >
                <Navigation className="w-5 h-5 mr-2" />
                Navigate to Location
              </Button>
              <Button
                onClick={handleMarkArrived}
                className="w-full h-14 bg-[var(--muted-teal)] hover:bg-[var(--muted-teal)]/90 text-[var(--evergreen)] font-semibold rounded-xl"
              >
                <MapPin className="w-5 h-5 mr-2" />
                Mark Arrived
              </Button>
            </>
          )}

          {currentStatus === "out_for_delivery" && (
            <>
              <Button
                onClick={handleMarkComplete}
                className="w-full h-14 bg-[var(--muted-teal)] hover:bg-[var(--muted-teal)]/90 text-[var(--evergreen)] font-semibold rounded-xl"
              >
                <CheckCircle2 className="w-5 h-5 mr-2" />
                Delivery Complete
              </Button>
              <Button
                onClick={() => router.push(`/deliveries/${deliveryId}/issue`)}
                variant="outline"
                className="w-full h-14 border-red-300 text-red-600 hover:bg-red-50 font-semibold rounded-xl"
              >
                <AlertTriangle className="w-5 h-5 mr-2" />
                Report Issue
              </Button>
            </>
          )}

          {currentStatus === "delivered" && (
            <Button
              onClick={() => {
                const nextId = String(Number(deliveryId) + 1)
                if (deliveriesData[nextId]) {
                  router.push(`/deliveries/${nextId}`)
                } else {
                  router.push("/summary")
                }
              }}
              className="w-full h-14 bg-[var(--muted-teal)] hover:bg-[var(--muted-teal)]/90 text-[var(--evergreen)] font-semibold rounded-xl"
            >
              Next Delivery
              <ChevronRight className="w-5 h-5 ml-2" />
            </Button>
          )}
        </div>
      </main>
    </AppShell>
  )
}
