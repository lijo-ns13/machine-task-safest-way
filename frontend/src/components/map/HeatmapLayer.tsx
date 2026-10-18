import { useEffect, useRef } from 'react'
import { useMap } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet.heat'
import type { Heatmap } from '../../types/api'

interface Props {
  heatmap: Heatmap
  hour: number
}

// Colours line up with the intensity of each risk level (level / 4).
const GRADIENT = { 0.25: '#facc15', 0.5: '#f97316', 0.75: '#dc2626', 1: '#7f1d1d' }

/**
 * One heat layer for the whole session. Moving the slider only swaps its data
 * (setLatLngs), so nothing is re-created and dragging stays smooth.
 */
export default function HeatmapLayer({ heatmap, hour }: Props) {
  const map = useMap()
  const layerRef = useRef<L.HeatLayer | null>(null)

  useEffect(() => {
    const layer = L.heatLayer([], { radius: 45, blur: 35, max: 1, minOpacity: 0.35, gradient: GRADIENT })
    layer.addTo(map)
    layerRef.current = layer
    return () => {
      layerRef.current = null
      // leaflet.heat redraws on the next animation frame and crashes if the layer was
      // already removed, so remove it one frame later (after any pending redraw).
      requestAnimationFrame(() => layer.remove())
    }
  }, [map])

  useEffect(() => {
    const frame = heatmap.frames[hour] ?? []
    const weighted: [number, number, number][] = []
    heatmap.points.forEach(([lat, lng], i) => {
      if (frame[i] > 0) weighted.push([lat, lng, frame[i]]) // clear (0) cells draw nothing
    })
    layerRef.current?.setLatLngs(weighted)
  }, [heatmap, hour])

  return null
}
