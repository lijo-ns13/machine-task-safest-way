// Mirrors the JSON returned by POST /api/routes/analyze (see README).

export type RiskLabel = 'Low' | 'Moderate' | 'High' | 'Severe' | 'No Travel'

export type LatLng = [number, number]

export interface AnalyzeRequest {
  origin: string
  destination: string
  departure_time: string // ISO 8601
  load_weight_lb: number
  checkpoint_interval_miles?: 10 | 25 | 50 | null
}

export interface Place {
  name: string
  lat: number
  lng: number
}

export interface CheckpointWeather {
  wind_mph: number
  rain_in_hr: number
  snow_in_hr: number
}

export interface Checkpoint {
  mile: number
  lat: number
  lng: number
  eta: string
  weather: CheckpointWeather
  risk: RiskLabel
  risk_level: number // 0..4
  reason: string
}

export interface RouteStats {
  miles_by_risk: Record<RiskLabel, number>
  no_travel_miles: number
  severe_miles: number
  high_miles: number
  avg_risk: number
  max_risk: RiskLabel
  no_travel: boolean
}

export interface RouteResult {
  id: string
  summary: string
  distance_miles: number
  duration_hours: number
  eta: string
  geometry: LatLng[]
  stats: RouteStats
  checkpoints: Checkpoint[]
}

export interface Heatmap {
  start_time: string
  hours: number
  points: LatLng[]
  frames: number[][] // frames[hour][pointIndex] = intensity 0..1
}

export interface AnalyzeResponse {
  origin: Place
  destination: Place
  departure_time: string
  load_weight_lb: number
  recommended_route_id: string
  recommendation_reason: string
  routes: RouteResult[]
  heatmap: Heatmap
  warnings: string[]
}
