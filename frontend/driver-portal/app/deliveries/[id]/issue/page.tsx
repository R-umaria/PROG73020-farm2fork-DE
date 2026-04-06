"use client"

import { useState } from "react"
import { useRouter, useParams } from "next/navigation"
import { AppShell } from "@/components/delivery/app-shell"
import { PageHeader } from "@/components/delivery/page-header"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Field, FieldLabel } from "@/components/ui/field"
import { Spinner } from "@/components/ui/spinner"
import { cn } from "@/lib/utils"
import { 
  UserX, 
  Car, 
  MapPinOff, 
  Lock, 
  PackageX,
  AlertOctagon,
  Camera,
  Send,
  Check
} from "lucide-react"

const issueTypes = [
  {
    id: "customer-unavailable",
    label: "Customer Unavailable",
    description: "No one present to receive delivery",
    icon: UserX,
  },
  {
    id: "traffic-delay",
    label: "Delayed by Traffic",
    description: "Unexpected traffic or road conditions",
    icon: Car,
  },
  {
    id: "address-problem",
    label: "Address Problem",
    description: "Cannot locate or incorrect address",
    icon: MapPinOff,
  },
  {
    id: "access-issue",
    label: "Unable to Access",
    description: "Gate, security, or access restriction",
    icon: Lock,
  },
  {
    id: "partial-delivery",
    label: "Partial Delivery",
    description: "Only some items could be delivered",
    icon: PackageX,
  },
  {
    id: "damaged-items",
    label: "Damaged Items",
    description: "Items damaged during transit",
    icon: AlertOctagon,
  },
]

export default function ReportIssuePage() {
  const router = useRouter()
  const params = useParams()
  const deliveryId = params.id as string
  
  const [selectedIssue, setSelectedIssue] = useState<string | null>(null)
  const [notes, setNotes] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isSubmitted, setIsSubmitted] = useState(false)

  const handleSubmit = async () => {
    if (!selectedIssue) return
    
    setIsSubmitting(true)
    await new Promise(resolve => setTimeout(resolve, 1500))
    setIsSubmitting(false)
    setIsSubmitted(true)
    
    setTimeout(() => {
      router.push(`/deliveries/${deliveryId}`)
    }, 2000)
  }

  if (isSubmitted) {
    return (
      <AppShell showNav={false}>
        <div className="min-h-screen flex flex-col items-center justify-center px-6 bg-background">
          <div className="w-20 h-20 rounded-full bg-[var(--muted-teal)]/20 flex items-center justify-center mb-6">
            <Check className="w-10 h-10 text-[var(--muted-teal)]" />
          </div>
          <h1 className="text-2xl font-bold text-foreground text-center">
            Issue Reported
          </h1>
          <p className="text-muted-foreground text-center mt-2 max-w-sm">
            Dispatch has been notified. Redirecting back to delivery...
          </p>
        </div>
      </AppShell>
    )
  }

  return (
    <AppShell showNav={false}>
      <PageHeader 
        title="Report Issue"
        subtitle="Stop #2 - Sunrise Organic Co-op"
        backHref={`/deliveries/${deliveryId}`}
      />

      <main className="px-4 py-6 max-w-lg mx-auto space-y-6">
        {/* Issue Type Selection */}
        <section>
          <h2 className="text-sm font-medium text-muted-foreground mb-3">
            Select Issue Type
          </h2>
          <div className="grid grid-cols-2 gap-3">
            {issueTypes.map((issue) => (
              <button
                key={issue.id}
                onClick={() => setSelectedIssue(issue.id)}
                className={cn(
                  "flex flex-col items-start p-4 rounded-xl border transition-all text-left",
                  selectedIssue === issue.id
                    ? "border-[var(--muted-teal)] bg-[var(--muted-teal)]/10 ring-1 ring-[var(--muted-teal)]/20"
                    : "border-border bg-card hover:border-[var(--muted-teal)]/50"
                )}
              >
                <div className={cn(
                  "p-2 rounded-lg mb-3",
                  selectedIssue === issue.id
                    ? "bg-[var(--muted-teal)]/20"
                    : "bg-muted"
                )}>
                  <issue.icon className={cn(
                    "w-5 h-5",
                    selectedIssue === issue.id
                      ? "text-[var(--muted-teal)]"
                      : "text-muted-foreground"
                  )} />
                </div>
                <p className={cn(
                  "font-medium text-sm",
                  selectedIssue === issue.id
                    ? "text-[var(--evergreen)]"
                    : "text-foreground"
                )}>
                  {issue.label}
                </p>
                <p className="text-xs text-muted-foreground mt-0.5">
                  {issue.description}
                </p>
              </button>
            ))}
          </div>
        </section>

        {/* Notes Field */}
        <Field>
          <FieldLabel className="text-sm font-medium text-foreground">
            Additional Notes
          </FieldLabel>
          <Textarea
            placeholder="Provide any additional details about the issue..."
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            className="min-h-[120px] bg-background border-border rounded-xl resize-none"
          />
        </Field>

        {/* Photo Upload Placeholder */}
        <div className="border-2 border-dashed border-border rounded-xl p-6 text-center hover:border-[var(--muted-teal)]/50 transition-colors cursor-pointer">
          <div className="w-12 h-12 rounded-full bg-muted mx-auto mb-3 flex items-center justify-center">
            <Camera className="w-6 h-6 text-muted-foreground" />
          </div>
          <p className="text-sm font-medium text-foreground">
            Add Photo Evidence
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            Tap to capture or upload a photo
          </p>
        </div>

        {/* Submit Button */}
        <div className="pt-4">
          <Button
            onClick={handleSubmit}
            disabled={!selectedIssue || isSubmitting}
            className="w-full h-14 bg-[var(--midnight-violet)] hover:bg-[var(--midnight-violet)]/90 text-white font-semibold rounded-xl disabled:opacity-50"
          >
            {isSubmitting ? (
              <Spinner className="w-5 h-5" />
            ) : (
              <>
                <Send className="w-5 h-5 mr-2" />
                Submit Issue Report
              </>
            )}
          </Button>
          
          <p className="text-xs text-center text-muted-foreground mt-3">
            Dispatch will be notified immediately
          </p>
        </div>
      </main>
    </AppShell>
  )
}
