import type { Heatmap } from '../../types/api'
import { formatDateTime } from '../../utils/format'
import './HeatmapControls.css'

interface Props {
  heatmap: Heatmap
  hour: number
  visible: boolean
  onHourChange: (hour: number) => void
  onVisibleChange: (visible: boolean) => void
}

export default function HeatmapControls({ heatmap, hour, visible, onHourChange, onVisibleChange }: Props) {
  const time = new Date(new Date(heatmap.start_time).getTime() + hour * 3_600_000)

  return (
    <div className="heatmap-controls">
      <div className="heatmap-controls__top">
        <strong>Weather risk heatmap</strong>
        <label className="heatmap-controls__toggle">
          <input type="checkbox" checked={visible} onChange={(e) => onVisibleChange(e.target.checked)} />
          Show
        </label>
      </div>
      <div className="heatmap-controls__time">
        +{hour}h · {formatDateTime(time.toISOString())}
      </div>
      <input
        type="range"
        min={0}
        max={heatmap.hours}
        step={1}
        value={hour}
        disabled={!visible}
        onChange={(e) => onHourChange(Number(e.target.value))}
        aria-label="Forecast hour"
      />
      <div className="heatmap-controls__legend">
        <span style={{ background: '#facc15' }} />Moderate
        <span style={{ background: '#f97316' }} />High
        <span style={{ background: '#dc2626' }} />Severe
        <span style={{ background: '#7f1d1d' }} />No Travel
      </div>
    </div>
  )
}
