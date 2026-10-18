import { useEffect } from 'react'
import { useMap } from 'react-leaflet'
import type { LatLngBoundsExpression } from 'leaflet'

/** Zooms the map to `bounds` whenever they change (i.e. after a new analysis). */
export default function FitBounds({ bounds }: { bounds: LatLngBoundsExpression }) {
  const map = useMap()
  useEffect(() => {
    map.fitBounds(bounds, { padding: [40, 40] })
  }, [map, bounds])
  return null
}
