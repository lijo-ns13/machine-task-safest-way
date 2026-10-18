import RouteForm from './components/RouteForm'
import { useRouteAnalysis } from './hooks/useRouteAnalysis'
import './App.css'

export default function App() {
  const { loading, error, fieldErrors, analyze } = useRouteAnalysis()

  return (
    <div className="app">
      <aside className="sidebar">
        <header className="sidebar__header">
          <h1>Weather-Aware Truck Routing</h1>
          <p className="muted">Compare routes by weather risk, load and travel time.</p>
        </header>
        <RouteForm loading={loading} fieldErrors={fieldErrors} onSubmit={analyze} />
        {error && <div className="alert alert-error">{error}</div>}
      </aside>
    </div>
  )
}
