import type { AnalyzeRequest, AnalyzeResponse } from '../types/api'

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''

/** Error carrying a user-friendly message and, for 400s, per-field messages. */
export class ApiError extends Error {
  fieldErrors: Record<string, string>

  constructor(message: string, fieldErrors: Record<string, string> = {}) {
    super(message)
    this.fieldErrors = fieldErrors
  }
}

export async function analyzeRoutes(
  payload: AnalyzeRequest,
  signal?: AbortSignal,
): Promise<AnalyzeResponse> {
  let response: Response
  try {
    response = await fetch(`${BASE_URL}/api/routes/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal,
    })
  } catch (err) {
    if (err instanceof DOMException && err.name === 'AbortError') throw err
    throw new ApiError('Cannot reach the server. Is the backend running?')
  }

  const body = await response.json().catch(() => null)
  if (response.ok) return body as AnalyzeResponse

  // 400 -> { field: ["msg"] }, 422/502 -> { error: "msg" }
  if (response.status === 400 && body) {
    const fieldErrors: Record<string, string> = {}
    for (const [field, messages] of Object.entries(body)) {
      fieldErrors[field] = Array.isArray(messages) ? messages.join(' ') : String(messages)
    }
    throw new ApiError('Please fix the highlighted fields.', fieldErrors)
  }
  throw new ApiError(body?.error ?? `Request failed (${response.status})`)
}
