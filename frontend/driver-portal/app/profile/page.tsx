"use client"

import { useRouter } from "next/navigation"
import { AppShell } from "@/components/delivery/app-shell"
import { PageHeader } from "@/components/delivery/page-header"
import { Button } from "@/components/ui/button"
import { 
  User, 
  Mail, 
  Phone, 
  Truck, 
  MapPin,
  Calendar,
  Award,
  Settings,
  HelpCircle,
  LogOut,
  ChevronRight,
  Bell,
  Shield
} from "lucide-react"
import { cn } from "@/lib/utils"

const menuItems = [
  {
    label: "Notifications",
    icon: Bell,
    href: "#",
  },
  {
    label: "Privacy & Security",
    icon: Shield,
    href: "#",
  },
  {
    label: "App Settings",
    icon: Settings,
    href: "#",
  },
  {
    label: "Help & Support",
    icon: HelpCircle,
    href: "#",
  },
]

export default function ProfilePage() {
  const router = useRouter()

  return (
    <AppShell>
      <PageHeader 
        title="Profile"
        subtitle="Driver Account"
      />

      <main className="px-4 py-6 max-w-lg mx-auto space-y-6">
        {/* Profile Card */}
        <div className="bg-card rounded-2xl p-6 border border-border text-center">
          <div className="w-24 h-24 rounded-full bg-[var(--evergreen)] mx-auto mb-4 flex items-center justify-center text-white text-3xl font-bold">
            MC
          </div>
          <h2 className="text-xl font-bold text-foreground">Marcus Chen</h2>
          <p className="text-sm text-muted-foreground mt-1">Driver ID: DRV-2847</p>
          
          <div className="flex items-center justify-center gap-2 mt-3">
            <Award className="w-4 h-4 text-[var(--muted-teal)]" />
            <span className="text-sm font-medium text-[var(--muted-teal)]">
              Top Performer - Q1 2026
            </span>
          </div>
        </div>

        {/* Contact Info */}
        <div className="bg-card rounded-xl border border-border divide-y divide-border">
          <div className="flex items-center gap-4 p-4">
            <div className="p-2 rounded-lg bg-[var(--muted-teal)]/10">
              <Mail className="w-5 h-5 text-[var(--muted-teal)]" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs text-muted-foreground">Email</p>
              <p className="font-medium text-foreground truncate">marcus.chen@farm2fork.com</p>
            </div>
          </div>
          
          <div className="flex items-center gap-4 p-4">
            <div className="p-2 rounded-lg bg-[var(--twilight-indigo)]/10">
              <Phone className="w-5 h-5 text-[var(--twilight-indigo)]" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs text-muted-foreground">Phone</p>
              <p className="font-medium text-foreground">(555) 867-5309</p>
            </div>
          </div>
          
          <div className="flex items-center gap-4 p-4">
            <div className="p-2 rounded-lg bg-[var(--midnight-violet)]/10">
              <MapPin className="w-5 h-5 text-[var(--midnight-violet)]" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs text-muted-foreground">Home Base</p>
              <p className="font-medium text-foreground">North Valley Distribution Center</p>
            </div>
          </div>
        </div>

        {/* Driver Stats */}
        <div className="bg-[var(--evergreen)] rounded-xl p-5 text-white">
          <h3 className="text-sm font-medium text-white/70 mb-4">This Month</h3>
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center">
              <p className="text-2xl font-bold">127</p>
              <p className="text-xs text-white/60 mt-1">Deliveries</p>
            </div>
            <div className="text-center border-x border-white/20">
              <p className="text-2xl font-bold">98.4%</p>
              <p className="text-xs text-white/60 mt-1">On-Time</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold">4.9</p>
              <p className="text-xs text-white/60 mt-1">Rating</p>
            </div>
          </div>
        </div>

        {/* Vehicle Assignment */}
        <div className="bg-card rounded-xl p-4 border border-border">
          <div className="flex items-center gap-4">
            <div className="p-2.5 rounded-lg bg-[var(--thistle)]">
              <Truck className="w-5 h-5 text-[var(--twilight-indigo)]" />
            </div>
            <div className="flex-1">
              <p className="text-xs text-muted-foreground">Assigned Vehicle</p>
              <p className="font-medium text-foreground">Van #12 - Ford Transit</p>
            </div>
            <span className="text-xs bg-[var(--muted-teal)]/10 text-[var(--evergreen)] px-2 py-1 rounded-full">
              Active
            </span>
          </div>
        </div>

        {/* Menu Items */}
        <div className="bg-card rounded-xl border border-border divide-y divide-border">
          {menuItems.map((item) => (
            <button
              key={item.label}
              className="w-full flex items-center gap-4 p-4 hover:bg-muted/50 transition-colors"
            >
              <div className="p-2 rounded-lg bg-muted">
                <item.icon className="w-5 h-5 text-muted-foreground" />
              </div>
              <span className="flex-1 text-left font-medium text-foreground">
                {item.label}
              </span>
              <ChevronRight className="w-5 h-5 text-muted-foreground" />
            </button>
          ))}
        </div>

        {/* Sign Out Button */}
        <Button
          onClick={() => router.push("/")}
          variant="outline"
          className="w-full h-12 border-red-200 text-red-600 hover:bg-red-50 font-medium rounded-xl"
        >
          <LogOut className="w-5 h-5 mr-2" />
          Sign Out
        </Button>

        {/* Version Footer */}
        <p className="text-center text-xs text-muted-foreground pt-2">
          Farm2Fork Driver v2.4.1
        </p>
      </main>
    </AppShell>
  )
}
