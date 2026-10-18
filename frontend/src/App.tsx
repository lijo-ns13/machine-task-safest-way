import { useState } from 'react'
import ResultsPanel from './components/ResultsPanel'
import MapView from './components/map/MapView'
import RouteForm from './components/RouteForm'
import { useRouteAnalysis } from './hooks/useRouteAnalysis'
import './App.css'

export default function App() {
  const { data, loading, error, fieldErrors, analyze } = useRouteAnalysis()
  // The user's pick; falls back to the recommended route whenever there is no valid pick.
  const [pickedRouteId, setPickedRouteId] = useState<string | null>(null)
  const selectedRouteId = data?.routes.some((r) => r.id === pickedRouteId)
    ? pickedRouteId!
    : (data?.recommended_route_id ?? '')

  function handleSubmit(payload: Parameters<typeof analyze>[0]) {
    setPickedRouteId(null)
    analyze(payload)
  }

  return (
    <div className="app">
      <aside className="sidebar">
        <header className="sidebar__header">
          <h1>Weather-Aware Truck Routing</h1>
          <p className="muted">Compare routes by weather risk, load and travel time.</p>
        </header>
        <RouteForm loading={loading} fieldErrors={fieldErrors}         onSubmit={handleSubmit} />
        {error && <div className="alert alert-error">{error}</div>}
                {data && (
                  <ResultsPanel
                    data={data}
                    selectedRouteId={selectedRouteId}
                    onSelectRoute={setPickedRouteId}
                  />
                )}
      </aside>
      <main className="map-area">
        <MapView data={data} selectedRouteId={selectedRouteId} onSelectRoute={setPickedRouteId} />
      </main>
    </div>
  )
}
