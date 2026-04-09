export interface DriverSession {
  driverId: number
  driverName: string
  vehicleType: string
  driverStatus: string
  signedInAt: string
}

const SESSION_KEY = "f2f_driver_portal_session_v1"

function canUseBrowserStorage(): boolean {
  return typeof window !== "undefined"
}

function readFromStorage(storage: Storage | null): DriverSession | null {
  if (!storage) {
    return null
  }

  const rawValue = storage.getItem(SESSION_KEY)
  if (!rawValue) {
    return null
  }

  try {
    return JSON.parse(rawValue) as DriverSession
  } catch {
    storage.removeItem(SESSION_KEY)
    return null
  }
}

export function getDriverSession(): DriverSession | null {
  if (!canUseBrowserStorage()) {
    return null
  }

  return readFromStorage(window.sessionStorage) ?? readFromStorage(window.localStorage)
}

export function saveDriverSession(session: DriverSession, rememberMe: boolean): void {
  if (!canUseBrowserStorage()) {
    return
  }

  const serialized = JSON.stringify(session)
  window.sessionStorage.removeItem(SESSION_KEY)
  window.localStorage.removeItem(SESSION_KEY)

  if (rememberMe) {
    window.localStorage.setItem(SESSION_KEY, serialized)
  } else {
    window.sessionStorage.setItem(SESSION_KEY, serialized)
  }
}

export function clearDriverSession(): void {
  if (!canUseBrowserStorage()) {
    return
  }

  window.sessionStorage.removeItem(SESSION_KEY)
  window.localStorage.removeItem(SESSION_KEY)
}
