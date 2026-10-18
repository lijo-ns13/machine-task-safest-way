import type { RouteResult } from '../types/api'
import { formatDateTime, formatDuration, formatMiles } from '../utils/format'
import { RISK_COLORS, ROUTE_COLORS } from '../utils/risk'
import './RouteCard.css'

interface Props {
  route: RouteResult
  index: number
  recommended: boolean
  selected: boolean
  onSelect: () => void
}

export default function RouteCard({ route, index, recommended, selected, onSelect }: Props) {
  const { stats } = route
  return (
    <button
      type="button"
      className={`route-card${selected ? ' route-card--selected' : ''}`}
      onClick={onSelect}
      aria-pressed={selected}
    >
      <div className="route-card__top">
        <span className="route-card__swatch" style={{ background: ROUTE_COLORS[index % ROUTE_COLORS.length] }} />
        <span className="route-card__title">{route.summary}</span>
        {recommended && <span className="badge badge--recommended">Recommended</span>}
      </div>

      <div className="route-card__metrics">
        <Metric label="Distance" value={formatMiles(route.distance_miles)} />
        <Metric label="Drive time" value={formatDuration(route.duration_hours)} />
        <Metric label="Arrival" value={formatDateTime(route.eta)} />
      </div>

      <div className="route-card__risk">
        <span className="badge" style={{ background: RISK_COLORS[stats.max_risk] }}>
          Worst: {stats.max_risk}
        </span>
        <span>No Travel {Math.round(stats.no_travel_miles)} mi</span>
        <span>Severe {Math.round(stats.severe_miles)} mi</span>
        <span>High {Math.round(stats.high_miles)} mi</span>
        <span>Avg risk {stats.avg_risk.toFixed(2)}</span>
      </div>
    </button>
  )
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="muted">{label}</div>
      <div className="route-card__value">{value}</div>
    </div>
  )
}
