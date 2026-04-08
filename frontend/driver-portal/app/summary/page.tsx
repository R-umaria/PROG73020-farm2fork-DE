"use client"

import { useRouter } from "next/navigation"
import { AppShell } from "@/components/delivery/app-shell"
import { Button } from "@/components/ui/button"
import { 
  CheckCircle2, 
  Clock, 
  MapPin, 
  AlertTriangle,
  Truck,
  ArrowRight,
  Home,
  Award
} from "lucide-react"

export default function ShiftSummaryPage() {
  const router = useRouter()

  return (
    <AppShell showNav={false}>
      {/* Success Header */}
      <div className="bg-gradient-to-b from-[var(--evergreen)] to-[#1a3a20] px-6 pt-16 pb-12 text-center">
        <div className="w-20 h-20 rounded-full bg-[var(--muted-teal)]/20 border-2 border-[var(--muted-teal)] mx-auto mb-6 flex items-center justify-center">
          <Award className="w-10 h-10 text-[var(--muted-teal)]" />
        </div>
        <h1 className="text-2xl font-bold text-white">
          Route Completed!
        </h1>
        <p className="text-white/70 mt-2">
          Great work today, Marcus
        </p>
      </div>

      <main className="px-4 py-6 max-w-lg mx-auto -mt-6 space-y-5">
        {/* Completion Stats Card */}
        <div className="bg-card rounded-2xl p-6 shadow-lg border border-border">
          <h2 className="text-sm font-medium text-muted-foreground mb-4">
            Shift Summary
          </h2>
          
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-[var(--muted-teal)]/10 rounded-xl p-4 border border-[var(--muted-teal)]/20">
              <div className="flex items-center gap-2 mb-2">
                <CheckCircle2 className="w-5 h-5 text-[var(--muted-teal)]" />
                <span className="text-sm text-muted-foreground">Completed</span>
              </div>
              <p className="text-3xl font-bold text-[var(--evergreen)]">5</p>
              <p className="text-xs text-muted-foreground">deliveries</p>
            </div>

            <div className="bg-amber-50 rounded-xl p-4 border border-amber-200">
              <div className="flex items-center gap-2 mb-2">
                <AlertTriangle className="w-5 h-5 text-amber-500" />
                <span className="text-sm text-muted-foreground">Exceptions</span>
              </div>
              <p className="text-3xl font-bold text-amber-600">0</p>
              <p className="text-xs text-muted-foreground">reported</p>
            </div>

            <div className="bg-[var(--twilight-indigo)]/10 rounded-xl p-4 border border-[var(--twilight-indigo)]/20">
              <div className="flex items-center gap-2 mb-2">
                <Clock className="w-5 h-5 text-[var(--twilight-indigo)]" />
                <span className="text-sm text-muted-foreground">Time</span>
              </div>
              <p className="text-3xl font-bold text-[var(--twilight-indigo)]">4.2</p>
              <p className="text-xs text-muted-foreground">hours worked</p>
            </div>

            <div className="bg-[var(--thistle)]/30 rounded-xl p-4 border border-[var(--thistle)]">
              <div className="flex items-center gap-2 mb-2">
                <MapPin className="w-5 h-5 text-[var(--midnight-violet)]" />
                <span className="text-sm text-muted-foreground">Distance</span>
              </div>
              <p className="text-3xl font-bold text-[var(--midnight-violet)]">38.4</p>
              <p className="text-xs text-muted-foreground">miles driven</p>
            </div>
          </div>
        </div>

        {/* Route Completion Bar */}
        <div className="bg-card rounded-xl p-5 border border-border">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-medium text-foreground">Route Completion</span>
            <span className="text-sm font-bold text-[var(--muted-teal)]">100%</span>
          </div>
          <div className="h-3 bg-muted rounded-full overflow-hidden">
            <div className="h-full bg-[var(--muted-teal)] rounded-full w-full" />
          </div>
          <div className="flex items-center justify-between mt-3 text-xs text-muted-foreground">
            <span>Started: 7:45 AM</span>
            <span>Finished: 2:55 PM</span>
          </div>
        </div>

        {/* Vehicle Info */}
        <div className="bg-card rounded-xl p-4 border border-border">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-muted">
              <Truck className="w-5 h-5 text-muted-foreground" />
            </div>
            <div className="flex-1">
              <p className="text-sm text-muted-foreground">Vehicle</p>
              <p className="font-medium text-foreground">Van #12 - Route NE-47</p>
            </div>
            <span className="text-xs text-[var(--muted-teal)] bg-[var(--muted-teal)]/10 px-2 py-1 rounded-full">
              Returned
            </span>
          </div>
        </div>

        {/* Performance Note */}
        <div className="bg-[var(--muted-teal)]/10 rounded-xl p-4 border border-[var(--muted-teal)]/30">
          <p className="text-sm text-[var(--evergreen)] font-medium">
            Excellent Performance
          </p>
          <p className="text-sm text-muted-foreground mt-1">
            All deliveries completed on time with zero exceptions. Keep up the great work!
          </p>
        </div>

        {/* Action Buttons */}
        <div className="space-y-3 pt-4">
          <Button
            onClick={() => router.push("/dashboard")}
            className="w-full h-14 bg-[var(--evergreen)] hover:bg-[var(--evergreen)]/90 text-white font-semibold rounded-xl"
          >
            <Home className="w-5 h-5 mr-2" />
            Return to Dashboard
          </Button>
          
          <Button
            onClick={() => router.push("/")}
            variant="outline"
            className="w-full h-14 border-border text-foreground font-semibold rounded-xl"
          >
            End Shift
            <ArrowRight className="w-5 h-5 ml-2" />
          </Button>
        </div>

        {/* Footer */}
        <p className="text-center text-xs text-muted-foreground pt-2">
          Shift data synced to dispatch at 2:56 PM
        </p>
      </main>
    </AppShell>
  )
}
