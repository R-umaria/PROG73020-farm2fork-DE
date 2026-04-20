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

const NOMINATIM_SEARCH_URL = "https://nominatim.openstreetmap.org/search"
const OSRM_ROUTE_URL = "https://router.project-osrm.org/route/v1/driving"

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

async function geocodeAddress(address: string): Promise<RouteMapCoordinate | null> {
  const response = await fetch(
    `${NOMINATIM_SEARCH_URL}?format=jsonv2&limit=1&countrycodes=ca&q=${encodeURIComponent(address)}`,
    {
      headers: {
        Accept: "application/json",
      },
      cache: "force-cache",
    },
  )

  if (!response.ok) {
    return null
  }

  const payload = (await response.json()) as Array<{ lat?: string; lon?: string }>
  const first = payload[0]
  if (!first?.lat || !first?.lon) {
    return null
  }

  const latitude = Number(first.lat)
  const longitude = Number(first.lon)
  if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) {
    return null
  }

  return { latitude, longitude }
}

function hasUsableCoordinate(waypoint: RouteMapWaypoint): boolean {
  return Number.isFinite(waypoint.latitude) && Number.isFinite(waypoint.longitude) && !(waypoint.latitude === 0 && waypoint.longitude === 0)
}

async function refineWaypointByAddress(waypoint: RouteMapWaypoint): Promise<RouteMapWaypoint> {
  if (hasUsableCoordinate(waypoint) || !waypoint.address) {
    return waypoint
  }

  try {
    const preciseCoordinate = await geocodeAddress(waypoint.address)
    if (!preciseCoordinate) {
      return waypoint
    }
    return {
      ...waypoint,
      latitude: preciseCoordinate.latitude,
      longitude: preciseCoordinate.longitude,
    }
  } catch {
    return waypoint
  }
}

async function buildRoadPath(waypoints: RouteMapWaypoint[]): Promise<RouteMapCoordinate[]> {
  if (waypoints.length < 2) {
    return []
  }

  const coordinates = waypoints.map((waypoint) => `${waypoint.longitude},${waypoint.latitude}`).join(";")
  const response = await fetch(
    `${OSRM_ROUTE_URL}/${coordinates}?overview=full&geometries=geojson&steps=false`,
    { cache: "no-store" },
  )

  if (!response.ok) {
    return []
  }

  const payload = (await response.json()) as {
    code?: string
    routes?: Array<{ geometry?: { coordinates?: Array<[number, number]> } }>
  }

  if (payload.code !== "Ok") {
    return []
  }

  const coordinatesPath = payload.routes?.[0]?.geometry?.coordinates ?? []
  return dedupePath(
    coordinatesPath
      .map(([longitude, latitude]) => ({ latitude, longitude }))
      .filter((coordinate) => Number.isFinite(coordinate.latitude) && Number.isFinite(coordinate.longitude)),
  )
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

    let isCancelled = false

    void (async () => {
      // Preserve backend/customer geocodes as the source of truth.
      // Browser-side address search is only used when coordinates are missing.
      const refinedWarehouse = await refineWaypointByAddress(routeData.warehouse)
      const refinedStops = await Promise.all(routeData.stops.map((stop) => refineWaypointByAddress(stop)))

      let roadPath: RouteMapCoordinate[] = []
      try {
        roadPath = await buildRoadPath([refinedWarehouse, ...refinedStops])
      } catch {
        roadPath = []
      }

      const backendPath = dedupePath(routeData.path)
      const path = roadPath.length >= 2 ? roadPath : backendPath.length >= 2 ? backendPath : buildStraightFallbackPath(refinedWarehouse, refinedStops)
      const pathLabel = roadPath.length >= 2 ? "Road route" : routeData.routing_status === "optimized" && backendPath.length >= 2 ? "Valhalla route" : "Fallback route"

      if (!isCancelled) {
        setResolvedRouteData({
          warehouse: refinedWarehouse,
          stops: refinedStops,
          path,
          pathLabel,
        })
      }
    })().catch(() => {
      if (!isCancelled) {
        setResolvedRouteData({
          warehouse: routeData.warehouse,
          stops: routeData.stops,
          path: buildStraightFallbackPath(routeData.warehouse, routeData.stops),
          pathLabel: "Fallback route",
        })
      }
    })

    return () => {
      isCancelled = true
    }
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
            stops: routeData.stops,
            path: buildStraightFallbackPath(routeData.warehouse, routeData.stops),
            pathLabel: routeData.routing_status === "optimized" ? "Valhalla route" : "Fallback route",
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

        const warehouseLatLng: [number, number] = [displayRoute.warehouse.latitude, displayRoute.warehouse.longitude]
        const stopLatLngs = displayRoute.stops.map((stop) => [stop.latitude, stop.longitude] as [number, number])
        const pathLatLngs = displayRoute.path.map((coordinate) => [coordinate.latitude, coordinate.longitude] as [number, number])
        const allLatLngs = [warehouseLatLng, ...stopLatLngs]

        if (pathLatLngs.length >= 2) {
          L.polyline(pathLatLngs, {
            color: "#2f855a",
            weight: 6,
            opacity: 0.9,
            lineCap: "round",
            lineJoin: "round",
          }).addTo(layers)
        }

        L.marker(warehouseLatLng, {
          icon: L.divIcon({
            className: "farm2fork-route-marker",
            html: buildMarkerHtml("W", "#17301c"),
            iconSize: [32, 32],
            iconAnchor: [16, 16],
          }),
        })
          .bindPopup(`<strong>${displayRoute.warehouse.label}</strong><br/>${displayRoute.warehouse.address ?? "Warehouse"}`)
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
          map.setView(warehouseLatLng, 13)
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
