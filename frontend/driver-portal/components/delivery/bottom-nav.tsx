"use client"

import { cn } from "@/lib/utils"
import { LayoutDashboard, Route, Package, History, User } from "lucide-react"
import Link from "next/link"
import { usePathname } from "next/navigation"

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/route", label: "Route", icon: Route },
  { href: "/deliveries", label: "Deliveries", icon: Package },
  { href: "/history", label: "History", icon: History },
  { href: "/profile", label: "Profile", icon: User },
]

export function BottomNav() {
  const pathname = usePathname()

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-[1100] bg-card border-t border-border safe-area-inset-bottom">
      <div className="flex items-center justify-around h-16 max-w-lg mx-auto px-2">
        {navItems.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`)
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex flex-col items-center justify-center gap-1 px-3 py-2 rounded-lg transition-all min-w-[64px]",
                isActive 
                  ? "text-[var(--evergreen)]" 
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              <div className={cn(
                "p-1.5 rounded-lg transition-colors",
                isActive && "bg-[var(--muted-teal)]/20"
              )}>
                <item.icon className={cn(
                  "w-5 h-5 transition-colors",
                  isActive && "text-[var(--muted-teal)]"
                )} />
              </div>
              <span className={cn(
                "text-[10px] font-medium",
                isActive && "text-[var(--evergreen)]"
              )}>
                {item.label}
              </span>
            </Link>
          )
        })}
      </div>
    </nav>
  )
}
