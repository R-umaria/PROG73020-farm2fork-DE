"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Checkbox } from "@/components/ui/checkbox"
import { Field, FieldLabel } from "@/components/ui/field"
import { Truck, Leaf, ArrowRight, Eye, EyeOff } from "lucide-react"
import { Spinner } from "@/components/ui/spinner"

export default function LoginPage() {
  const router = useRouter()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [rememberMe, setRememberMe] = useState(false)
  const [isLoading, setIsLoading] = useState(false)

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    // Hardcoded demo credentials for testing
    if ((email === "demo" || email === "driver@farm2fork.com") && password === "demo") {
      localStorage.setItem("isLoggedIn", "true")
      localStorage.setItem("driverName", "Alex Johnson")
      localStorage.setItem("driverId", "DRV-2024-001")
      await new Promise(resolve => setTimeout(resolve, 1000))
      router.push("/dashboard")
    } else {
      setIsLoading(false)
    }
  }

  const handleDemoLogin = async () => {
    setIsLoading(true)
    localStorage.setItem("isLoggedIn", "true")
    localStorage.setItem("driverName", "Alex Johnson")
    localStorage.setItem("driverId", "DRV-2024-001")
    await new Promise(resolve => setTimeout(resolve, 800))
    router.push("/dashboard")
  }

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-b from-[var(--evergreen)] via-[var(--evergreen)] to-[#1a3a20]">
      {/* Top Section with Branding */}
      <div className="flex-1 flex flex-col items-center justify-center px-6 pt-12 pb-8">
        {/* Logo */}
        <div className="flex items-center justify-center w-20 h-20 bg-[var(--muted-teal)]/20 rounded-2xl mb-6 border border-[var(--muted-teal)]/30">
          <div className="relative">
            <Truck className="w-10 h-10 text-[var(--muted-teal)]" />
            <Leaf className="w-5 h-5 text-[var(--muted-teal)] absolute -top-1 -right-2" />
          </div>
        </div>

        {/* Title */}
        <h1 className="text-3xl font-bold text-white tracking-tight text-balance text-center">
          Farm2Fork
        </h1>
        <p className="text-lg text-[var(--muted-teal)] font-medium mt-1">
          Driver Portal
        </p>
        <p className="text-sm text-white/60 mt-3 text-center max-w-[280px] text-pretty">
          Sign in to view your deliveries and start your route
        </p>

        {/* Decorative Element */}
        <div className="flex items-center gap-2 mt-8">
          <div className="w-8 h-[2px] bg-[var(--muted-teal)]/30 rounded-full" />
          <div className="w-2 h-2 bg-[var(--muted-teal)]/50 rounded-full" />
          <div className="w-8 h-[2px] bg-[var(--muted-teal)]/30 rounded-full" />
        </div>
      </div>

      {/* Bottom Section with Form */}
      <div className="bg-card rounded-t-[32px] px-6 pt-8 pb-10 shadow-2xl">
        <form onSubmit={handleLogin} className="max-w-sm mx-auto space-y-5">
          <Field>
            <FieldLabel className="text-sm font-medium text-foreground">
              Driver ID or Email
            </FieldLabel>
            <Input
              type="text"
              placeholder="Enter your driver ID or email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="h-12 bg-background border-border rounded-xl text-base placeholder:text-muted-foreground/60"
              required
            />
          </Field>

          <Field>
            <FieldLabel className="text-sm font-medium text-foreground">
              Password
            </FieldLabel>
            <div className="relative">
              <Input
                type={showPassword ? "text" : "password"}
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="h-12 bg-background border-border rounded-xl text-base pr-12 placeholder:text-muted-foreground/60"
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
              >
                {showPassword ? (
                  <EyeOff className="w-5 h-5" />
                ) : (
                  <Eye className="w-5 h-5" />
                )}
                <span className="sr-only">
                  {showPassword ? "Hide password" : "Show password"}
                </span>
              </button>
            </div>
          </Field>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Checkbox
                id="remember"
                checked={rememberMe}
                onCheckedChange={(checked) => setRememberMe(checked as boolean)}
                className="border-border data-[state=checked]:bg-[var(--muted-teal)] data-[state=checked]:border-[var(--muted-teal)]"
              />
              <label
                htmlFor="remember"
                className="text-sm text-muted-foreground cursor-pointer select-none"
              >
                Remember me
              </label>
            </div>
            <button
              type="button"
              className="text-sm font-medium text-[var(--twilight-indigo)] hover:text-[var(--midnight-violet)] transition-colors"
            >
              Forgot password?
            </button>
          </div>

          <Button
            type="submit"
            disabled={isLoading || !email || !password}
            className="w-full h-12 bg-[var(--muted-teal)] hover:bg-[var(--muted-teal)]/90 text-[var(--evergreen)] font-semibold text-base rounded-xl mt-2 transition-all disabled:opacity-50"
          >
            {isLoading ? (
              <Spinner className="w-5 h-5" />
            ) : (
              <>
                Sign In
                <ArrowRight className="w-5 h-5 ml-2" />
              </>
            )}
          </Button>

          {/* Demo Login Button */}
          <Button
            type="button"
            onClick={handleDemoLogin}
            disabled={isLoading}
            className="w-full h-12 bg-[var(--twilight-indigo)]/20 hover:bg-[var(--twilight-indigo)]/30 text-[var(--twilight-indigo)] font-semibold text-base rounded-xl border border-[var(--twilight-indigo)]/30 transition-all disabled:opacity-50"
          >
            {isLoading ? (
              <Spinner className="w-5 h-5" />
            ) : (
              "Demo Login"
            )}
          </Button>

          {/* Help Text */}
          <p className="text-center text-xs text-muted-foreground pt-4">
            {"Having trouble signing in? "}
            <span className="text-[var(--twilight-indigo)] font-medium">
              Contact dispatch
            </span>
          </p>
          <p className="text-center text-[10px] text-muted-foreground/50 mt-2">
            Demo credentials: driver@farm2fork.com / demo
          </p>
        </form>

        {/* Footer */}
        <div className="mt-8 pt-6 border-t border-border">
          <p className="text-center text-xs text-muted-foreground">
            Farm2Fork Delivery System v2.4.1
          </p>
          <p className="text-center text-[10px] text-muted-foreground/60 mt-1">
            Powered by Enterprise Logistics Platform
          </p>
        </div>
      </div>
    </div>
  )
}
