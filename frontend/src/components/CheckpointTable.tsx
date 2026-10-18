import type { Checkpoint } from '../types/api'
import { formatDateTime } from '../utils/format'
import { RISK_COLORS } from '../utils/risk'
import './CheckpointTable.css'

export default function CheckpointTable({ checkpoints }: { checkpoints: Checkpoint[] }) {
  return (
    <div className="checkpoints">
      <h2>Checkpoints</h2>
      <div className="checkpoints__scroll">
        <table>
          <thead>
            <tr>
              <th>Mile</th>
              <th>ETA</th>
              <th>Wind</th>
              <th>Rain</th>
              <th>Snow</th>
              <th>Risk</th>
            </tr>
          </thead>
          <tbody>
            {checkpoints.map((cp) => (
              <tr key={cp.mile} title={cp.reason}>
                <td>{cp.mile}</td>
                <td>{formatDateTime(cp.eta)}</td>
                <td>{cp.weather.wind_mph} mph</td>
                <td>{cp.weather.rain_in_hr}</td>
                <td>{cp.weather.snow_in_hr}</td>
                <td>
                  <span className="badge" style={{ background: RISK_COLORS[cp.risk] }}>
                    {cp.risk}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="muted">Rain and snow in in/hr. Hover a row for the reason.</p>
    </div>
  )
}
