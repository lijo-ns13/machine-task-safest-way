import { CircleMarker, Popup } from 'react-leaflet'
import type { Checkpoint } from '../../types/api'
import { formatDateTime } from '../../utils/format'
import { RISK_COLORS } from '../../utils/risk'

/** Risk-coloured dot for every checkpoint of the selected route; click for weather details. */
export default function CheckpointMarkers({ checkpoints }: { checkpoints: Checkpoint[] }) {
  return (
    <>
      {checkpoints.map((cp) => (
        <CircleMarker
          key={cp.mile}
          center={[cp.lat, cp.lng]}
          radius={7}
          pathOptions={{ color: '#fff', weight: 2, fillColor: RISK_COLORS[cp.risk], fillOpacity: 1 }}
        >
          <Popup>
            <strong>Mile {cp.mile}</strong>
            <br />
            ETA {formatDateTime(cp.eta)}
            <br />
            Wind {cp.weather.wind_mph} mph · Rain {cp.weather.rain_in_hr} in/hr · Snow{' '}
            {cp.weather.snow_in_hr} in/hr
            <br />
            <strong style={{ color: RISK_COLORS[cp.risk] }}>{cp.risk}</strong>: {cp.reason}
          </Popup>
        </CircleMarker>
      ))}
    </>
  )
}
