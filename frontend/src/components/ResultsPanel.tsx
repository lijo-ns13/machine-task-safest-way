import type { AnalyzeResponse } from '../types/api'
import RouteCard from './RouteCard'
import CheckpointTable from './CheckpointTable'
import './ResultsPanel.css'

interface Props {
  data: AnalyzeResponse
  selectedRouteId: string
  onSelectRoute: (id: string) => void
}

export default function ResultsPanel({ data, selectedRouteId, onSelectRoute }: Props) {
  const selectedRoute = data.routes.find((r) => r.id === selectedRouteId)
  return (
    <section className="results">
      <div className="recommendation">
        <div className="recommendation__title">Safest route: {recommendedSummary(data)}</div>
        <div className="muted">{data.recommendation_reason}</div>
      </div>

      {data.warnings.map((warning) => (
        <div key={warning} className="alert alert-warning">
          {warning}
        </div>
      ))}

      <div className="results__routes">
        {data.routes.map((route, index) => (
          <RouteCard
            key={route.id}
            route={route}
            index={index}
            recommended={route.id === data.recommended_route_id}
            selected={route.id === selectedRouteId}
            onSelect={() => onSelectRoute(route.id)}
          />
        ))}
      </div>
      <CheckpointTable checkpoints={selectedRoute?.checkpoints ?? []} />
    </section>
  )
}

function recommendedSummary(data: AnalyzeResponse): string {
  return data.routes.find((r) => r.id === data.recommended_route_id)?.summary ?? ''
}
