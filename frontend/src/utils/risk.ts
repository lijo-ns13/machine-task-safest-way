import type { RiskLabel } from '../types/api'

export const RISK_COLORS: Record<RiskLabel, string> = {
  Low: '#16a34a',
  Moderate: '#ca8a04',
  High: '#ea580c',
  Severe: '#dc2626',
  'No Travel': '#7f1d1d',
}

export const RISK_ORDER: RiskLabel[] = ['Low', 'Moderate', 'High', 'Severe', 'No Travel']

// One colour per route so users can tell them apart on the map.
export const ROUTE_COLORS = ['#2563eb', '#9333ea', '#0891b2']
