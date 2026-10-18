import { useState, type FormEvent } from 'react'
import type { AnalyzeRequest } from '../types/api'
import { toLocalInputValue } from '../utils/format'
import './RouteForm.css'

interface Props {
  loading: boolean
  fieldErrors: Record<string, string>
  onSubmit: (payload: AnalyzeRequest) => void
}

const MAX_LOAD_LB = 80_000

export default function RouteForm({ loading, fieldErrors, onSubmit }: Props) {
  const [origin, setOrigin] = useState('')
  const [destination, setDestination] = useState('')
  const [departure, setDeparture] = useState(() =>
    toLocalInputValue(new Date(Date.now() + 60 * 60 * 1000)),
  )
  const [load, setLoad] = useState('40000')
  const [localErrors, setLocalErrors] = useState<Record<string, string>>({})

  const errors = { ...fieldErrors, ...localErrors }

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    const found: Record<string, string> = {}
    const loadNumber = Number(load)

    if (!origin.trim()) found.origin = 'Enter an origin'
    if (!destination.trim()) found.destination = 'Enter a destination'
    if (!departure) found.departure_time = 'Choose a departure time'
    if (load === '' || !Number.isInteger(loadNumber) || loadNumber < 0 || loadNumber > MAX_LOAD_LB) {
      found.load_weight_lb = `Enter a whole number from 0 to ${MAX_LOAD_LB.toLocaleString()}`
    }
    setLocalErrors(found)
    if (Object.keys(found).length > 0) return

    onSubmit({
      origin: origin.trim(),
      destination: destination.trim(),
      departure_time: new Date(departure).toISOString(),
      load_weight_lb: loadNumber,
    })
  }

  return (
    <form className="route-form" onSubmit={handleSubmit} noValidate>
      <Field label="Origin" error={errors.origin}>
        <input
          value={origin}
          onChange={(e) => setOrigin(e.target.value)}
          placeholder="Dallas, TX"
          autoComplete="off"
        />
      </Field>
      <Field label="Destination" error={errors.destination}>
        <input
          value={destination}
          onChange={(e) => setDestination(e.target.value)}
          placeholder="Denver, CO"
          autoComplete="off"
        />
      </Field>
      <div className="route-form__row">
        <Field label="Departure" error={errors.departure_time}>
          <input
            type="datetime-local"
            value={departure}
            onChange={(e) => setDeparture(e.target.value)}
          />
        </Field>
        <Field label="Load (lb)" error={errors.load_weight_lb}>
          <input
            type="number"
            inputMode="numeric"
            min={0}
            max={MAX_LOAD_LB}
            step={500}
            value={load}
            onChange={(e) => setLoad(e.target.value)}
          />
        </Field>
      </div>
      <button className="btn-primary" type="submit" disabled={loading}>
        {loading ? 'Analyzing routes…' : 'Find safest route'}
      </button>
    </form>
  )
}

function Field({
  label,
  error,
  children,
}: {
  label: string
  error?: string
  children: React.ReactNode
}) {
  return (
    <label className={`field${error ? ' field--invalid' : ''}`}>
      <span className="field__label">{label}</span>
      {children}
      {error && <span className="field__error">{error}</span>}
    </label>
  )
}
