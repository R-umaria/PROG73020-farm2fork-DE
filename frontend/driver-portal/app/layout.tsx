import type { Metadata, Viewport } from "next"
import { Analytics } from "@vercel/analytics/next"
import { PwaProvider } from "@/components/pwa/pwa-provider"
import "./globals.css"

export const metadata: Metadata = {
  title: "Farm2Fork Driver",
  description: "Farm-to-Fork delivery driver application for shift selection, route management, and delivery execution.",
  applicationName: "Farm2Fork Driver Portal",
  manifest: "/manifest.webmanifest",
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "Farm2Fork Driver",
  },
  formatDetection: {
    telephone: false,
  },
  icons: {
    icon: [{ url: "/favicon.ico" }],
    shortcut: [{ url: "/favicon.ico" }],
    apple: [{ url: "/apple-touch-icon.png", sizes: "180x180" }],
  },
}

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
  themeColor: "#17301c",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <body className="font-sans antialiased">
        <PwaProvider />
        {children}
        <Analytics />
      </body>
    </html>
  )
}
