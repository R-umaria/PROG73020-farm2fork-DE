export interface DriverSession {
  email: string
  driverId: number
  driverName: string
  vehicleType: string
  driverStatus: string
  signedInAt: string
  selectedShiftId?: string | null
  selectedShiftName?: string | null
  selectedZoneCode?: string | null
}

const SESSION_KEY = "f2f_driver_portal_session_v2"
const LEGACY_SESSION_KEY = "f2f_driver_portal_session_v1"

function canUseBrowserStorage(): boolean {
  return typeof window !== "undefined"
}

function readFromStorage(storage: Storage | null): DriverSession | null {
  if (!storage) return null
  const rawValue = storage.getItem(SESSION_KEY) ?? storage.getItem(LEGACY_SESSION_KEY)
  if (!rawValue) return null
  try {
    const parsed = JSON.parse(rawValue) as DriverSession
    return { ...parsed, selectedShiftId: parsed.selectedShiftId ?? null, selectedShiftName: parsed.selectedShiftName ?? null, selectedZoneCode: parsed.selectedZoneCode ?? null }
  } catch {
    storage.removeItem(SESSION_KEY); storage.removeItem(LEGACY_SESSION_KEY); return null
  }
}

export function getDriverSession(): DriverSession | null {
  if (!canUseBrowserStorage()) return null
  return readFromStorage(window.sessionStorage) ?? readFromStorage(window.localStorage)
}

export function saveDriverSession(session: DriverSession, rememberMe = false): void {
  if (!canUseBrowserStorage()) return
  const serialized = JSON.stringify(session)
  for (const key of [SESSION_KEY, LEGACY_SESSION_KEY]) {
    window.sessionStorage.removeItem(key); window.localStorage.removeItem(key)
  }
  if (rememberMe) window.localStorage.setItem(SESSION_KEY, serialized)
  else window.sessionStorage.setItem(SESSION_KEY, serialized)
}

export function updateSelectedShift(shift: { shiftId: string; shiftName: string; zoneCode: string | null }): DriverSession | null {
  const session = getDriverSession(); if (!session) return null
  const nextSession: DriverSession = { ...session, selectedShiftId: shift.shiftId, selectedShiftName: shift.shiftName, selectedZoneCode: shift.zoneCode }
  saveDriverSession(nextSession, Boolean(window.localStorage.getItem(SESSION_KEY))); return nextSession
}

export function clearSelectedShift(): DriverSession | null {
  const session = getDriverSession(); if (!session) return null
  const nextSession: DriverSession = { ...session, selectedShiftId: null, selectedShiftName: null, selectedZoneCode: null }
  saveDriverSession(nextSession, Boolean(window.localStorage.getItem(SESSION_KEY))); return nextSession
}

export function clearDriverSession(): void {
  if (!canUseBrowserStorage()) return
  for (const key of [SESSION_KEY, LEGACY_SESSION_KEY]) {
    window.sessionStorage.removeItem(key); window.localStorage.removeItem(key)
  }
}
