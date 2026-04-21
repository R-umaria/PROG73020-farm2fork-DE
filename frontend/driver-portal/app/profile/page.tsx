"use client"

import { Bell, ChevronRight, CreditCard, HelpCircle, LogOut, Shield, Truck, User } from "lucide-react"

import { AppShell } from "@/components/delivery/app-shell"
import { PageHeader } from "@/components/delivery/page-header"
import { Button } from "@/components/ui/button"
import { useDriverSession } from "@/hooks/use-driver-session"

const menuItems = [
  { label: "Notifications", icon: Bell },
  { label: "Vehicle & Equipment", icon: Truck },
  { label: "Help & Support", icon: HelpCircle },
  { label: "Privacy", icon: Shield },
  { label: "Payment Details", icon: CreditCard },
]

export default function ProfilePage() {
  const { session, isReady, signOut } = useDriverSession({ required: true, requireShift: true })

  if (!isReady || !session) {
    return null
  }

  return (
    <AppShell>
      <PageHeader title="Profile" subtitle="Backend-linked driver session" />

      <main className="px-4 py-6 max-w-lg mx-auto space-y-5">
        <div className="bg-card rounded-2xl p-6 border border-border text-center">
          <div className="mx-auto mb-4 flex h-20 w-20 items-center justify-center rounded-full bg-[var(--muted-teal)]/15">
            <User className="h-10 w-10 text-[var(--muted-teal)]" />
          </div>
          <h2 className="text-xl font-bold text-foreground">{session.driverName}</h2>
          <p className="mt-1 text-sm text-muted-foreground">Driver #{session.driverId}</p>
          <div className="mt-4 grid grid-cols-2 gap-3 text-left">
            <div className="rounded-xl border border-border p-3">
              <p className="text-xs text-muted-foreground">Vehicle</p>
              <p className="mt-1 font-medium text-foreground">{session.vehicleType}</p>
            </div>
            <div className="rounded-xl border border-border p-3">
              <p className="text-xs text-muted-foreground">Roster status</p>
              <p className="mt-1 font-medium text-foreground capitalize">{session.driverStatus}</p>
            </div>
          </div>
        </div>

        <div className="bg-card rounded-xl border border-border divide-y divide-border">
          {menuItems.map((item) => (
            <button key={item.label} className="w-full flex items-center gap-4 p-4 hover:bg-muted/50 transition-colors">
              <div className="p-2 rounded-lg bg-muted">
                <item.icon className="w-5 h-5 text-muted-foreground" />
              </div>
              <span className="flex-1 text-left font-medium text-foreground">{item.label}</span>
              <ChevronRight className="w-5 h-5 text-muted-foreground" />
            </button>
          ))}
        </div>

        <Button onClick={signOut} variant="outline" className="w-full h-12 border-red-200 text-red-600 hover:bg-red-50 font-medium rounded-xl">
          <LogOut className="w-5 h-5 mr-2" />
          Sign Out
        </Button>

        <div className="rounded-xl border border-border p-3 text-left"><p className="text-xs text-muted-foreground">Active shift</p><p className="mt-1 font-medium text-foreground">{session.selectedShiftName ?? "No shift selected"}</p><p className="mt-1 text-xs text-muted-foreground">{session.selectedZoneCode ? `Region ${session.selectedZoneCode}` : "Shift selection controls dashboard scope"}</p></div><p className="text-center text-xs text-muted-foreground pt-2">Signed in at {new Date(session.signedInAt).toLocaleString()}</p>
      </main>
    </AppShell>
  )
}
