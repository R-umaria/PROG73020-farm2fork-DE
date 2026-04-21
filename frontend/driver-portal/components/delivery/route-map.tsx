"use client"

import { useEffect, useMemo, useRef, useState } from "react"
import { Crosshair, Expand, LocateFixed, Minimize } from "lucide-react"

import type { RouteMapCoordinate, RouteMapData, RouteMapWaypoint } from "@/lib/api-client"
import { cn } from "@/lib/utils"

interface RouteMapProps {
  routeData: RouteMapData | null
  className?: string
}

interface ResolvedRouteMapState {
  warehouse: RouteMapWaypoint
  origin: RouteMapWaypoint
  stops: RouteMapWaypoint[]
  path: RouteMapCoordinate[]
  pathLabel: string
}

interface BrowserLocation {
  latitude: number
  longitude: number
  accuracy: number
}

declare global {
  interface Window {
    L?: any
  }
}

let leafletLoader: Promise<any> | null = null


function decodePolyline(encoded: string, precision = 6): RouteMapCoordinate[] {
  const coordinates: RouteMapCoordinate[] = []
  let index = 0
  let latitude = 0
  let longitude = 0
  const factor = 10 ** precision

  while (index < encoded.length) {
    let result = 0
    let shift = 0
    let byte = 0

    do {
      byte = encoded.charCodeAt(index++) - 63
      result |= (byte & 0x1f) << shift
      shift += 5
    } while (byte >= 0x20)

    latitude += (result & 1) !== 0 ? ~(result >> 1) : result >> 1

    result = 0
    shift = 0
    do {
      byte = encoded.charCodeAt(index++) - 63
      result |= (byte & 0x1f) << shift
      shift += 5
    } while (byte >= 0x20)

    longitude += (result & 1) !== 0 ? ~(result >> 1) : result >> 1

    coordinates.push({
      latitude: latitude / factor,
      longitude: longitude / factor,
    })
  }

  return coordinates
}


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

function buildMarkerHtml(label: string, accentColor: string): string {
  return `
    <div style="display:flex;align-items:center;justify-content:center;width:32px;height:32px;border-radius:9999px;background:white;border:3px solid ${accentColor};box-shadow:0 10px 25px rgba(0,0,0,0.18);font-weight:700;font-size:12px;color:${accentColor};">
      ${label}
    </div>
  `
}

function buildCurrentLocationHtml(): string {
  return `
    <div style="display:flex;align-items:center;justify-content:center;width:18px;height:18px;border-radius:9999px;background:#3b82f6;border:3px solid white;box-shadow:0 8px 18px rgba(59,130,246,0.35);"></div>
  `
}

function dedupePath(path: RouteMapCoordinate[]): RouteMapCoordinate[] {
  const deduped: RouteMapCoordinate[] = []
  for (const coordinate of path) {
    const previous = deduped[deduped.length - 1]
    if (!previous || previous.latitude !== coordinate.latitude || previous.longitude !== coordinate.longitude) {
      deduped.push(coordinate)
    }
  }
  return deduped
}

function buildStraightFallbackPath(warehouse: RouteMapWaypoint, stops: RouteMapWaypoint[]): RouteMapCoordinate[] {
  return dedupePath([
    { latitude: warehouse.latitude, longitude: warehouse.longitude },
    ...stops.map((stop) => ({ latitude: stop.latitude, longitude: stop.longitude })),
  ])
}

function hasUsableCoordinate(waypoint: RouteMapWaypoint | null | undefined): waypoint is RouteMapWaypoint {
  return !!waypoint && Number.isFinite(waypoint.latitude) && Number.isFinite(waypoint.longitude) && !(waypoint.latitude === 0 && waypoint.longitude === 0)
}

export function RouteMap({ routeData, className }: RouteMapProps) {
  const wrapperRef = useRef<HTMLDivElement | null>(null)
  const containerRef = useRef<HTMLDivElement | null>(null)
  const mapRef = useRef<any>(null)
  const layersRef = useRef<any>(null)
  const currentLocationMarkerRef = useRef<any>(null)
  const currentLocationCircleRef = useRef<any>(null)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [resolvedRouteData, setResolvedRouteData] = useState<ResolvedRouteMapState | null>(null)
  const [userLocation, setUserLocation] = useState<BrowserLocation | null>(null)
  const [isLocating, setIsLocating] = useState(false)
  const [isFullscreen, setIsFullscreen] = useState(false)

  useEffect(() => {
    if (!routeData) {
      setResolvedRouteData(null)
      return
    }

    const origin = hasUsableCoordinate(routeData.active_origin) ? routeData.active_origin : routeData.warehouse
    const stops = routeData.active_stop ? [routeData.active_stop] : routeData.stops
    const polylinePath = routeData.encoded_polyline ? dedupePath(decodePolyline(routeData.encoded_polyline)) : []
    const backendPath = dedupePath(routeData.path)
    const resolvedBackendPath = polylinePath.length >= 2 ? polylinePath : backendPath
    const path = resolvedBackendPath.length >= 2 ? resolvedBackendPath : buildStraightFallbackPath(origin, stops)
    const pathLabel = routeData.routing_status === "optimized" ? "Active road route" : routeData.routing_status === "completed" ? "Route completed" : "Fallback route"

    setResolvedRouteData({
      warehouse: routeData.warehouse,
      origin,
      stops,
      path,
      pathLabel,
    })
  }, [routeData])

  useEffect(() => {
    if (typeof window === "undefined" || !navigator.geolocation) {
      return
    }

    let isCancelled = false
    setIsLocating(true)

    navigator.geolocation.getCurrentPosition(
      (position) => {
        if (!isCancelled) {
          setUserLocation({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy: position.coords.accuracy,
          })
          setIsLocating(false)
        }
      },
      () => {
        if (!isCancelled) {
          setIsLocating(false)
        }
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 60000,
      },
    )

    return () => {
      isCancelled = true
    }
  }, [])

  useEffect(() => {
    const onFullscreenChange = () => {
      const activeElement = document.fullscreenElement
      setIsFullscreen(activeElement === wrapperRef.current)
      if (mapRef.current) {
        window.requestAnimationFrame(() => mapRef.current.invalidateSize())
      }
    }

    document.addEventListener("fullscreenchange", onFullscreenChange)
    return () => {
      document.removeEventListener("fullscreenchange", onFullscreenChange)
    }
  }, [])

  const displayRoute = useMemo(
    () =>
      resolvedRouteData ??
      (routeData
        ? {
            warehouse: routeData.warehouse,
            origin: routeData.active_origin ?? routeData.warehouse,
            stops: routeData.active_stop ? [routeData.active_stop] : routeData.stops,
            path: (() => {
              const polylinePath = routeData.encoded_polyline ? dedupePath(decodePolyline(routeData.encoded_polyline)) : []
              const backendPath = dedupePath(routeData.path)
              return polylinePath.length >= 2 ? polylinePath : backendPath.length >= 2 ? backendPath : buildStraightFallbackPath(routeData.active_origin ?? routeData.warehouse, routeData.active_stop ? [routeData.active_stop] : routeData.stops)
            })(),
            pathLabel: routeData.routing_status === "optimized" ? "Active road route" : routeData.routing_status === "completed" ? "Route completed" : "Fallback route",
          }
        : null),
    [resolvedRouteData, routeData],
  )

  useEffect(() => {
    let isCancelled = false

    if (!displayRoute || !containerRef.current) {
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

                const originLatLng: [number, number] = [displayRoute.origin.latitude, displayRoute.origin.longitude]
        const stopLatLngs = displayRoute.stops.map((stop) => [stop.latitude, stop.longitude] as [number, number])
        const pathLatLngs = displayRoute.path.map((coordinate) => [coordinate.latitude, coordinate.longitude] as [number, number])
        const allLatLngs = [...pathLatLngs, originLatLng, ...stopLatLngs]

        if (pathLatLngs.length >= 2) {
          L.polyline(pathLatLngs, {
            color: "#2f855a",
            weight: 6,
            opacity: 0.9,
            lineCap: "round",
            lineJoin: "round",
          }).addTo(layers)
        }

        const originLabel = displayRoute.origin.route_stop_id ? `S${displayRoute.origin.sequence ?? ""}` : "W"

        L.marker(originLatLng, {
          icon: L.divIcon({
            className: "farm2fork-route-marker",
            html: buildMarkerHtml(originLabel, "#17301c"),
            iconSize: [32, 32],
            iconAnchor: [16, 16],
          }),
        })
          .bindPopup(`<strong>${displayRoute.origin.label}</strong><br/>${displayRoute.origin.address ?? "Current origin"}`)
          .addTo(layers)

        displayRoute.stops.forEach((stop, index) => {
          L.marker([stop.latitude, stop.longitude], {
            icon: L.divIcon({
              className: "farm2fork-route-marker",
              html: buildMarkerHtml(String(stop.sequence ?? index + 1), "#414066"),
              iconSize: [32, 32],
              iconAnchor: [16, 16],
            }),
          })
            .bindPopup(`<strong>${stop.label}</strong><br/>${stop.address ?? "Delivery stop"}<br/>Stop ${stop.sequence ?? index + 1}`)
            .addTo(layers)
        })

        if (allLatLngs.length > 1) {
          map.fitBounds(allLatLngs, { padding: [28, 28] })
        } else {
          map.setView(originLatLng, 13)
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
  }, [displayRoute])

  useEffect(() => {
    if (!mapRef.current || !window.L) {
      return
    }

    const L = window.L

    if (currentLocationMarkerRef.current) {
      currentLocationMarkerRef.current.remove()
      currentLocationMarkerRef.current = null
    }

    if (currentLocationCircleRef.current) {
      currentLocationCircleRef.current.remove()
      currentLocationCircleRef.current = null
    }

    if (!userLocation) {
      return
    }

    currentLocationMarkerRef.current = L.marker([userLocation.latitude, userLocation.longitude], {
      icon: L.divIcon({
        className: "farm2fork-current-location-marker",
        html: buildCurrentLocationHtml(),
        iconSize: [18, 18],
        iconAnchor: [9, 9],
      }),
      zIndexOffset: 1000,
    }).addTo(mapRef.current)

    currentLocationCircleRef.current = L.circle([userLocation.latitude, userLocation.longitude], {
      radius: Math.max(userLocation.accuracy, 20),
      color: "#60a5fa",
      fillColor: "#60a5fa",
      fillOpacity: 0.15,
      weight: 1,
    }).addTo(mapRef.current)
  }, [userLocation])

  useEffect(() => {
    return () => {
      if (mapRef.current) {
        mapRef.current.remove()
        mapRef.current = null
        layersRef.current = null
      }
    }
  }, [])

  const handleLocateMe = () => {
    if (!navigator.geolocation) {
      return
    }

    setIsLocating(true)
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const nextLocation = {
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          accuracy: position.coords.accuracy,
        }
        setUserLocation(nextLocation)
        setIsLocating(false)
        if (mapRef.current) {
          mapRef.current.flyTo([nextLocation.latitude, nextLocation.longitude], 15)
        }
      },
      () => {
        setIsLocating(false)
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0,
      },
    )
  }

  const handleToggleFullscreen = async () => {
    if (!wrapperRef.current) {
      return
    }

    if (document.fullscreenElement === wrapperRef.current) {
      await document.exitFullscreen()
    } else {
      await wrapperRef.current.requestFullscreen()
    }
  }

  return (
    <div ref={wrapperRef} className={cn("relative isolate z-0 overflow-hidden rounded-2xl border border-border bg-card", className)}>
      <div ref={containerRef} className="h-full min-h-[240px] w-full" />

      <div className="pointer-events-none absolute inset-x-3 top-3 z-[700] flex items-start justify-between gap-3">
        <div className="rounded-full bg-background/90 px-3 py-1 text-[11px] font-medium text-foreground shadow-sm backdrop-blur-sm">
          {displayRoute ? displayRoute.pathLabel : "Route map"}
        </div>
        <div className="pointer-events-auto flex items-center gap-2">
          <button
            type="button"
            onClick={handleLocateMe}
            className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-background/95 text-foreground shadow-sm transition hover:bg-background"
            aria-label={userLocation ? "Center map on current location" : "Use current location"}
            title={userLocation ? "Center on current location" : "Use current location"}
          >
            {isLocating ? <LocateFixed className="h-4 w-4 animate-pulse" /> : <Crosshair className="h-4 w-4" />}
          </button>
          <button
            type="button"
            onClick={() => void handleToggleFullscreen()}
            className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-background/95 text-foreground shadow-sm transition hover:bg-background"
            aria-label={isFullscreen ? "Exit fullscreen map" : "Open fullscreen map"}
            title={isFullscreen ? "Exit fullscreen" : "Open fullscreen"}
          >
            {isFullscreen ? <Minimize className="h-4 w-4" /> : <Expand className="h-4 w-4" />}
          </button>
        </div>
      </div>

      {loadError ? (
        <div className="absolute inset-0 z-[650] flex items-center justify-center bg-background/80 px-6 text-center text-sm text-muted-foreground">
          {loadError}
        </div>
      ) : null}
    </div>
  )
}
