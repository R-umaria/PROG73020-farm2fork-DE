"use client"

import { useEffect, useRef, useState } from "react"

import type { RouteMapData } from "@/lib/api-client"
import { cn } from "@/lib/utils"

interface RouteMapProps {
  routeData: RouteMapData | null
  className?: string
}

declare global {
  interface Window {
    L?: any
  }
}

let leafletLoader: Promise<any> | null = null

function ensureLeafletLoaded(): Promise<any> {
  if (typeof window === "undefined") {
    return Promise.reject(new Error("Leaflet can only load in the browser."))
  }

  if (window.L) {
    return Promise.resolve(window.L)
  }

  if (!leafletLoader) {
    leafletLoader = new Promise((resolve, reject) => {
      const stylesheetId = "leaflet-stylesheet"
      if (!document.getElementById(stylesheetId)) {
        const link = document.createElement("link")
        link.id = stylesheetId
        link.rel = "stylesheet"
        link.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
        document.head.appendChild(link)
      }

      const existingScript = document.getElementById("leaflet-script") as HTMLScriptElement | null
      if (existingScript) {
        existingScript.addEventListener("load", () => resolve(window.L), { once: true })
        existingScript.addEventListener("error", () => reject(new Error("Unable to load Leaflet.")), { once: true })
        return
      }

      const script = document.createElement("script")
      script.id = "leaflet-script"
      script.src = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
      script.async = true
      script.onload = () => resolve(window.L)
      script.onerror = () => reject(new Error("Unable to load Leaflet."))
      document.body.appendChild(script)
    })
  }

  return leafletLoader
}

function buildMarkerHtml(label: string, accentClassName: string): string {
  return `
    <div style="display:flex;align-items:center;justify-content:center;width:30px;height:30px;border-radius:9999px;background:white;border:3px solid ${accentClassName};box-shadow:0 10px 25px rgba(0,0,0,0.18);font-weight:700;font-size:12px;color:${accentClassName};">
      ${label}
    </div>
  `
}

export function RouteMap({ routeData, className }: RouteMapProps) {
  const containerRef = useRef<HTMLDivElement | null>(null)
  const mapRef = useRef<any>(null)
  const layersRef = useRef<any>(null)
  const [loadError, setLoadError] = useState<string | null>(null)

  useEffect(() => {
    let isCancelled = false

    if (!routeData || !containerRef.current) {
      return
    }

    void ensureLeafletLoaded()
      .then((L) => {
        if (isCancelled || !containerRef.current) {
          return
        }

        if (!mapRef.current) {
          mapRef.current = L.map(containerRef.current, {
            zoomControl: true,
            scrollWheelZoom: true,
          })

          L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            maxZoom: 19,
            attribution: '&copy; OpenStreetMap contributors',
          }).addTo(mapRef.current)

          layersRef.current = L.layerGroup().addTo(mapRef.current)
        }

        const map = mapRef.current
        const layers = layersRef.current
        layers.clearLayers()

        const warehouseLatLng: [number, number] = [routeData.warehouse.latitude, routeData.warehouse.longitude]
        const stopLatLngs = routeData.stops.map((stop) => [stop.latitude, stop.longitude] as [number, number])
        const pathLatLngs = routeData.path.map((coordinate) => [coordinate.latitude, coordinate.longitude] as [number, number])
        const allLatLngs = [warehouseLatLng, ...stopLatLngs]

        if (pathLatLngs.length >= 2) {
          L.polyline(pathLatLngs, {
            color: "#83b692",
            weight: 5,
            opacity: 0.9,
          }).addTo(layers)
        }

        L.marker(warehouseLatLng, {
          icon: L.divIcon({
            className: "farm2fork-route-marker",
            html: buildMarkerHtml("W", "#17301c"),
            iconSize: [30, 30],
            iconAnchor: [15, 15],
          }),
        })
          .bindPopup(`<strong>${routeData.warehouse.label}</strong><br/>${routeData.warehouse.address ?? "Warehouse"}`)
          .addTo(layers)

        routeData.stops.forEach((stop, index) => {
          L.marker([stop.latitude, stop.longitude], {
            icon: L.divIcon({
              className: "farm2fork-route-marker",
              html: buildMarkerHtml(String(stop.sequence ?? index + 1), "#414066"),
              iconSize: [30, 30],
              iconAnchor: [15, 15],
            }),
          })
            .bindPopup(
              `<strong>${stop.label}</strong><br/>${stop.address ?? "Delivery stop"}<br/>Stop ${stop.sequence ?? index + 1}`,
            )
            .addTo(layers)
        })

        if (allLatLngs.length > 1) {
          map.fitBounds(allLatLngs, { padding: [28, 28] })
        } else {
          map.setView(warehouseLatLng, 12)
        }

        window.requestAnimationFrame(() => {
          map.invalidateSize()
        })

        setLoadError(null)
      })
      .catch((error: unknown) => {
        if (!isCancelled) {
          setLoadError(error instanceof Error ? error.message : "Unable to load route map.")
        }
      })

    return () => {
      isCancelled = true
    }
  }, [routeData])

  useEffect(() => {
    return () => {
      if (mapRef.current) {
        mapRef.current.remove()
        mapRef.current = null
        layersRef.current = null
      }
    }
  }, [])

  return (
    <div className={cn("relative overflow-hidden rounded-2xl border border-border bg-card", className)}>
      <div ref={containerRef} className="h-full min-h-[240px] w-full" />

      {loadError ? (
        <div className="absolute inset-0 flex items-center justify-center bg-background/80 px-6 text-center text-sm text-muted-foreground">
          {loadError}
        </div>
      ) : null}

      {routeData ? (
        <div className="pointer-events-none absolute bottom-3 left-3 rounded-full bg-background/90 px-3 py-1 text-[11px] font-medium text-foreground shadow-sm">
          {routeData.routing_status === "optimized" ? "Valhalla route" : "Fallback route"}
        </div>
      ) : null}
    </div>
  )
}
