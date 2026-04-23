"use client"

import { useEffect, useState } from "react"
import { Download, Smartphone, CheckCircle2 } from "lucide-react"
import { Button } from "@/components/ui/button"

declare global {
  interface BeforeInstallPromptEvent extends Event {
    prompt: () => Promise<void>
    userChoice: Promise<{ outcome: "accepted" | "dismissed"; platform: string }>
  }
}

interface InstallAppButtonProps {
  className?: string
  compact?: boolean
}

export function InstallAppButton({ className, compact = false }: InstallAppButtonProps) {
  const [promptEvent, setPromptEvent] = useState<BeforeInstallPromptEvent | null>(null)
  const [installed, setInstalled] = useState(false)

  useEffect(() => {
    if (typeof window === "undefined") return

    const isStandalone = window.matchMedia("(display-mode: standalone)").matches || Boolean((window.navigator as Navigator & { standalone?: boolean }).standalone)
    if (isStandalone) setInstalled(true)

    const handleBeforeInstallPrompt = (event: Event) => {
      const installEvent = event as BeforeInstallPromptEvent
      installEvent.preventDefault()
      setPromptEvent(installEvent)
    }

    const handleInstalled = () => {
      setInstalled(true)
      setPromptEvent(null)
    }

    window.addEventListener("beforeinstallprompt", handleBeforeInstallPrompt)
    window.addEventListener("appinstalled", handleInstalled)

    return () => {
      window.removeEventListener("beforeinstallprompt", handleBeforeInstallPrompt)
      window.removeEventListener("appinstalled", handleInstalled)
    }
  }, [])

  const handleInstall = async () => {
    if (!promptEvent) return
    await promptEvent.prompt()
    await promptEvent.userChoice.catch(() => null)
    setPromptEvent(null)
  }

  if (installed) {
    return (
      <div className={className}>
        <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/10 px-3 py-2 text-sm font-medium text-white/80 backdrop-blur">
          <CheckCircle2 className="h-4 w-4 text-[var(--muted-teal)]" />
          Installed
        </div>
      </div>
    )
  }

  if (!promptEvent) return null

  return (
    <Button
      type="button"
      onClick={() => void handleInstall()}
      className={className}
      variant="outline"
    >
      {compact ? <Download className="h-4 w-4" /> : <Smartphone className="h-4 w-4" />}
      {compact ? "Install" : "Install app"}
    </Button>
  )
}
