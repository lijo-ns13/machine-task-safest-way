import { useMemo } from 'react'
import { CircleMarker, MapContainer, TileLayer, Tooltip } from 'react-leaflet'
import type { AnalyzeResponse } from '../../types/api'
import CheckpointMarkers from './CheckpointMarkers'
import FitBounds from './FitBounds'
import RouteLines from './RouteLines'
import 'leaflet/dist/leaflet.css'
import './MapView.css'

interface Props {
  data: AnalyzeResponse | null
  selectedRouteId: string
  onSelectRoute: (id: string) => void
}

const US_CENTER: [number, number] = [39.5, -98.35]

export default function MapView({ data, selectedRouteId, onSelectRoute }: Props) {
  const selected = data?.routes.find((r) => r.id === selectedRouteId)

  // Fit to all routes (not only the selected one) so switching routes doesn't move the map.
  const bounds = useMemo(
    () => (data ? data.routes.flatMap((r) => r.geometry) : null),
    [data],
  )

  return (
    <MapContainer center={US_CENTER} zoom={4} preferCanvas className="map">
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {data && bounds && (
        <>
          <FitBounds bounds={bounds} />
          <RouteLines
            routes={data.routes}
            selectedRouteId={selectedRouteId}
            recommendedRouteId={data.recommended_route_id}
            onSelect={onSelectRoute}
          />
          {selected && <CheckpointMarkers checkpoints={selected.checkpoints} />}
          <EndpointMarker label="Origin" place={data.origin} />
          <EndpointMarker label="Destination" place={data.destination} />
        </>
      )}
    </MapContainer>
  )
}

function EndpointMarker({ label, place }: { label: string; place: AnalyzeResponse['origin'] }) {
  return (
    <CircleMarker
      center={[place.lat, place.lng]}
      radius={10}
      pathOptions={{ color: '#fff', weight: 3, fillColor: '#0f172a', fillOpacity: 1 }}
    >
      <Tooltip permanent direction="top" offset={[0, -8]}>
        {label}
      </Tooltip>
    </CircleMarker>
  )
}
