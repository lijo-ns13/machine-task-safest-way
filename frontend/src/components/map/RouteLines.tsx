import { Polyline, Tooltip } from 'react-leaflet'
import type { RouteResult } from '../../types/api'
import { ROUTE_COLORS } from '../../utils/risk'

interface Props {
  routes: RouteResult[]
  selectedRouteId: string
  recommendedRouteId: string
  onSelect: (id: string) => void
}

/** Draws every route; the selected one is thick and on top, the others faded. */
export default function RouteLines({ routes, selectedRouteId, recommendedRouteId, onSelect }: Props) {
  // Selected route last so Leaflet paints it above the others.
  const ordered = [...routes].sort(
    (a, b) => Number(a.id === selectedRouteId) - Number(b.id === selectedRouteId),
  )

  return (
    <>
      {ordered.map((route) => {
        const selected = route.id === selectedRouteId
        const color = ROUTE_COLORS[routes.indexOf(route) % ROUTE_COLORS.length]
        return (
          <Polyline
            key={route.id}
            positions={route.geometry}
            pathOptions={{
              color,
              weight: selected ? 7 : 4,
              opacity: selected ? 0.95 : 0.5,
              dashArray: route.id === recommendedRouteId ? undefined : '8 8',
            }}
            eventHandlers={{ click: () => onSelect(route.id) }}
          >
            <Tooltip sticky>{route.summary}</Tooltip>
          </Polyline>
        )
      })}
    </>
  )
}
