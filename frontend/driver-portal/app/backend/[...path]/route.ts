import type { NextRequest } from "next/server"

const METHODS_WITHOUT_BODY = new Set(["GET", "HEAD"])

function getBackendBaseUrl(): string {
  const candidates = [
    process.env.INTERNAL_API_BASE_URL,
    process.env.NEXT_PUBLIC_API_BASE_URL,
    process.env.API_BASE_URL,
    "http://localhost:8000",
  ]

  for (const candidate of candidates) {
    const value = candidate?.trim()
    if (value) return value.replace(/\/$/, "")
  }

  return "http://localhost:8000"
}

async function proxy(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params
  const backendUrl = new URL(`${getBackendBaseUrl()}/${path.join("/")}`)

  for (const [key, value] of request.nextUrl.searchParams.entries()) {
    backendUrl.searchParams.append(key, value)
  }

  const headers = new Headers(request.headers)
  headers.delete("host")
  headers.delete("connection")
  headers.delete("content-length")

  try {
    const upstreamResponse = await fetch(backendUrl, {
      method: request.method,
      headers,
      body: METHODS_WITHOUT_BODY.has(request.method) ? undefined : await request.arrayBuffer(),
      cache: "no-store",
      redirect: "manual",
    })

    const responseHeaders = new Headers(upstreamResponse.headers)
    responseHeaders.delete("content-encoding")
    responseHeaders.delete("transfer-encoding")
    responseHeaders.delete("connection")

    return new Response(upstreamResponse.body, {
      status: upstreamResponse.status,
      statusText: upstreamResponse.statusText,
      headers: responseHeaders,
    })
  } catch (error) {
    return Response.json(
      {
        detail: "Driver portal backend proxy could not reach the API service.",
        target: backendUrl.toString(),
        error: error instanceof Error ? error.message : String(error),
      },
      { status: 502 },
    )
  }
}

export const dynamic = "force-dynamic"

export { proxy as GET, proxy as POST, proxy as PUT, proxy as PATCH, proxy as DELETE, proxy as OPTIONS, proxy as HEAD }
