import { useCallback, useRef, useState } from 'react'
import { analyzeRoutes, ApiError } from '../api/routesApi'
import type { AnalyzeRequest, AnalyzeResponse } from '../types/api'

interface State {
  data: AnalyzeResponse | null
  loading: boolean
  error: string | null
  fieldErrors: Record<string, string>
}

const INITIAL: State = { data: null, loading: false, error: null, fieldErrors: {} }

/** Runs one analysis at a time; starting a new one cancels the previous request. */
export function useRouteAnalysis() {
  const [state, setState] = useState<State>(INITIAL)
  const controllerRef = useRef<AbortController | null>(null)

  const analyze = useCallback(async (payload: AnalyzeRequest) => {
    controllerRef.current?.abort()
    const controller = new AbortController()
    controllerRef.current = controller

    setState((prev) => ({ ...prev, loading: true, error: null, fieldErrors: {} }))
    try {
      const data = await analyzeRoutes(payload, controller.signal)
      setState({ data, loading: false, error: null, fieldErrors: {} })
    } catch (err) {
      if (controller.signal.aborted) return
      const apiError =
        err instanceof ApiError ? err : new ApiError('Something went wrong. Please try again.')
      setState((prev) => ({
        ...prev,
        loading: false,
        error: apiError.message,
        fieldErrors: apiError.fieldErrors,
      }))
    }
  }, [])

  return { ...state, analyze }
}
