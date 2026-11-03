import { useEffect, useState } from 'react'
import './App.css'

type Property = {
  property_id: string
  city: string
  locality: string
  property_type: string
  area_sqft: number
  bedrooms: number
  estimated_value_inr: number
  data_source: string
}

type ValuationResult = {
  estimated_value_inr: number
  low_estimate_inr: number
  high_estimate_inr: number
  model: string
  data_source: string
  evaluation_metrics: {
    mae_inr: number
    rmse_inr: number
    r2: number
    evaluation_data: string
  }
  comparable_insights: {
    comparable_count: number
    average_rate_per_sqft_inr: number | null
    comparable_estimate_inr: number | null
    records: {
      city: string
      locality: string
      property_type: string
      area_sqft: number
      transaction_value_inr: number
      rate_per_sqft_inr: number
      data_source: string
      is_verified: boolean
    }[]
    notice: string
  }
  disclaimer: string
}

function App() {
  const [properties, setProperties] = useState<Property[]>([])
  const [city, setCity] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [activePage, setActivePage] = useState<'properties' | 'valuation'>('properties')

  const [valuationForm, setValuationForm] = useState({
    city: 'Indore',
    locality: 'Vijay Nagar',
    property_type: 'Apartment',
    area_sqft: '1200',
    bedrooms: '2',
    property_age_years: '5',
  })

  const [valuation, setValuation] = useState<ValuationResult | null>(null)
  const [valuationLoading, setValuationLoading] = useState(false)
  const [valuationError, setValuationError] = useState('')

  useEffect(() => {
    const params = new URLSearchParams({ limit: '50' })

    if (city) {
      params.set('city', city)
    }

    setLoading(true)
    setError('');

    fetch('http://localhost:8000/api/properties/?' + params.toString())
      .then((response) => {
        if (!response.ok) {
          throw new Error('Could not fetch properties')
        }
        return response.json()
      })
      .then((result) => {
        setProperties(result.data)
      })
      .catch(() => {
        setError('API connection failed. Check that the backend is running.')
      })
      .finally(() => {
        setLoading(false)
      })
  }, [city])

  const formatPrice = (value: number) =>
    new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(value)

  const handleValuation = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setValuationLoading(true)
    setValuationError('')
    setValuation(null)

    try {
      const response = await fetch('http://localhost:8000/api/valuation/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...valuationForm,
          area_sqft: Number(valuationForm.area_sqft),
          bedrooms: Number(valuationForm.bedrooms),
          property_age_years: Number(valuationForm.property_age_years),
        }),
      })

      if (!response.ok) {
const result = await response.json()

const message = Array.isArray(result.detail)
  ? result.detail.map((item: { msg: string }) => item.msg).join(', ')
  : result.detail || 'Valuation request failed'

throw new Error(message)
      }

      const result: ValuationResult = await response.json()
      setValuation(result)
    } catch (err) {
      setValuationError(
        err instanceof Error ? err.message : 'Could not connect to valuation API.',
      )
    } finally {
      setValuationLoading(false)
    }
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand"><span className="brand-mark">A</span> AURA</div>
        <p className="nav-label">WORKSPACE</p>

        <button
          className={`nav-item ${activePage === 'properties' ? 'active' : ''}`}
          onClick={() => setActivePage('properties')}
        >
          ▦ Property Intelligence
        </button>

        <button
          className={`nav-item ${activePage === 'valuation' ? 'active' : ''}`}
          onClick={() => setActivePage('valuation')}
        >
          ⌂ Valuation Studio
        </button>

        <div className="sidebar-bottom">
          AI-powered property intelligence<br />
          Demo environment
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <span>{activePage === 'properties' ? 'Property Intelligence' : 'Valuation Studio'}</span>
          <span className="demo-badge">● DEMO MODE</span>
        </header>

        <section className="page-heading">
          <p className="eyebrow">HERO HOUSING FINANCE · FINTECH CHALLENGE 2026</p>
          <h1>{activePage === 'properties' ? 'Property Intelligence' : 'Property Valuation Studio'}</h1>
          <p>
            {activePage === 'properties'
              ? 'Discover, evaluate, and understand property markets with AI.'
              : 'Generate an illustrative property value estimate using property details.'}
          </p>
        </section>

        {activePage === 'properties' ? (
          <>
            <section className="stats-grid">
              <div className="stat-card">
                <span>Properties in dataset</span>
                <strong>2,000</strong>
                <small>Synthetic demo records</small>
              </div>
              <div className="stat-card">
                <span>Data coverage</span>
                <strong>6 cities</strong>
                <small>Demo coverage — not verified market data</small>
              </div>
              <div className="stat-card">
                <span>Valuation engine</span>
                <strong>LightGBM</strong>
                <small>Trained on synthetic demo data</small>
              </div>
            </section>

            <section className="listing-section">
              <div className="section-heading">
                <div>
                  <h2>Property Explorer</h2>
                  <p>Browse properties from the demo dataset.</p>
                </div>

                <select value={city} onChange={(e) => setCity(e.target.value)}>
                  <option value="">All cities</option>
                  <option value="Mumbai">Mumbai</option>
                  <option value="Pune">Pune</option>
                  <option value="Bengaluru">Bengaluru</option>
                  <option value="Delhi">Delhi</option>
                  <option value="Hyderabad">Hyderabad</option>
                  <option value="Indore">Indore</option>
                </select>
              </div>

              {loading && <p className="status-message">Loading properties...</p>}
              {error && <p className="error-message">{error}</p>}

              {!loading && !error && (
                <div className="property-grid">
                  {properties.map((property) => (
                    <article className="property-card" key={property.property_id}>
                      <div className="property-visual">⌂</div>
                      <div className="property-info">
                        <span className="property-tag">{property.data_source}</span>
                        <h3>{property.locality}, {property.city}</h3>
                        <p>{property.property_type} · {property.area_sqft} sq.ft.</p>
                        <div className="property-footer">
                          <strong>{formatPrice(property.estimated_value_inr)}</strong>
                          <span>{property.bedrooms} BHK</span>
                        </div>
                      </div>
                    </article>
                  ))}
                </div>
              )}
            </section>
          </>
        ) : (
          <section className="listing-section valuation-layout">
            <div className="section-heading">
              <div>
                <h2>Property details</h2>
                <p>Enter details to generate a demo estimate.</p>
              </div>
            </div>

            <form className="valuation-form" onSubmit={handleValuation}>
              <label>
                City
                <select
                  value={valuationForm.city}
                  onChange={(e) => setValuationForm({ ...valuationForm, city: e.target.value })}
                >
                  <option>Indore</option>
                  <option>Mumbai</option>
                  <option>Pune</option>
                  <option>Bengaluru</option>
                  <option>Delhi</option>
                  <option>Hyderabad</option>
                </select>
              </label>

              <label>
                Locality
                <input
                  required
                  value={valuationForm.locality}
                  onChange={(e) => setValuationForm({ ...valuationForm, locality: e.target.value })}
                  placeholder="e.g. Vijay Nagar"
                />
              </label>

              <label>
                Property type
                <select
                  value={valuationForm.property_type}
                  onChange={(e) => setValuationForm({ ...valuationForm, property_type: e.target.value })}
                >
                  <option>Apartment</option>
                  <option>Independent House</option>
                  <option>Villa</option>
                  <option>Plot</option>
                </select>
              </label>

              <label>
                Area (sq. ft.)
                <input
                  type="number"
                  min="1"
                  required
                  value={valuationForm.area_sqft}
                  onChange={(e) => setValuationForm({ ...valuationForm, area_sqft: e.target.value })}
                />
              </label>

              <label>
                Bedrooms
                <input
                  type="number"
                  min="0"
                  required
                  value={valuationForm.bedrooms}
                  onChange={(e) => setValuationForm({ ...valuationForm, bedrooms: e.target.value })}
                />
              </label>

              <label>
                Property age (years)
                <input
                  type="number"
                  min="0"
                  required
                  value={valuationForm.property_age_years}
                  onChange={(e) => setValuationForm({ ...valuationForm, property_age_years: e.target.value })}
                />
              </label>

              <button className="valuation-submit" type="submit" disabled={valuationLoading}>
                {valuationLoading ? 'Calculating estimate...' : 'Estimate Property Value'}
              </button>
            </form>

            {valuationError && <p className="error-message">{valuationError}</p>}

           {valuation && (
           <div className="valuation-result">
           <span className="property-tag">ML DEMO ESTIMATE</span>

           <h2>{formatPrice(valuation.estimated_value_inr)}</h2>

            <p>
              {valuationForm.locality}, {valuationForm.city}
            </p>

            <div className="valuation-range">
            <div>
            <small>Low estimate</small>
            <strong>{formatPrice(valuation.low_estimate_inr)}</strong>
            </div>

            <div>
        <small>High estimate</small>
        <strong>{formatPrice(valuation.high_estimate_inr)}</strong>
      </div>
    </div>

    <div className="valuation-model-info">
      <p>
        <strong>Model:</strong> {valuation.model}
      </p>
      <p>
        <strong>Data source:</strong> {valuation.data_source}
      </p>
      <p>
        <strong>Test R²:</strong> {valuation.evaluation_metrics.r2}
      </p>
    </div>

    {valuation.comparable_insights && (
  <div className="comparable-section">
    <h3>Comparable Property Evidence</h3>

    <div className="comparable-stats">
      <div>
        <small>Matching records</small>
        <strong>{valuation.comparable_insights.comparable_count}</strong>
      </div>

      <div>
        <small>Average rate / sqft</small>
        <strong>
          {valuation.comparable_insights.average_rate_per_sqft_inr !== null
            ? formatPrice(
                valuation.comparable_insights.average_rate_per_sqft_inr
              )
            : 'Not available'}
        </strong>
      </div>

      <div>
        <small>Comparable estimate</small>
        <strong>
          {valuation.comparable_insights.comparable_estimate_inr !== null
            ? formatPrice(
                valuation.comparable_insights.comparable_estimate_inr
              )
            : 'Not available'}
        </strong>
      </div>
    </div>

    <p className="valuation-notice">
      {valuation.comparable_insights.notice}
    </p>

    {valuation.comparable_insights.records.length > 0 && (
      <div className="comparable-list">
        {valuation.comparable_insights.records.map((record, index) => (
          <article key={`${record.data_source}-${index}`}>
            <strong>
              {record.locality}, {record.city}
            </strong>

            <span>
              {record.property_type} · {record.area_sqft} sqft
            </span>

            <span>
              {formatPrice(record.transaction_value_inr)} ·{' '}
              {formatPrice(record.rate_per_sqft_inr)}/sqft
            </span>

            <small>
              Source: {record.data_source} ·{' '}
              {record.is_verified ? 'Verified' : 'Unverified demo'}
            </small>
          </article>
        ))}
      </div>
    )}
  </div>
)}

{valuation.comparable_insights && (
  <div className="comparable-section">
    <h3>Comparable Property Evidence</h3>

    <div className="comparable-stats">
      <div>
        <small>Matching records</small>
        <strong>{valuation.comparable_insights.comparable_count}</strong>
      </div>

      <div>
        <small>Average rate / sqft</small>
        <strong>
          {valuation.comparable_insights.average_rate_per_sqft_inr !== null
            ? formatPrice(
                valuation.comparable_insights.average_rate_per_sqft_inr
              )
            : 'Not available'}
        </strong>
      </div>

      <div>
        <small>Comparable estimate</small>
        <strong>
          {valuation.comparable_insights.comparable_estimate_inr !== null
            ? formatPrice(
                valuation.comparable_insights.comparable_estimate_inr
              )
            : 'Not available'}
        </strong>
      </div>
    </div>

    <p className="valuation-notice">
      {valuation.comparable_insights.notice}
    </p>

    {valuation.comparable_insights.records.length > 0 && (
      <div className="comparable-list">
        {valuation.comparable_insights.records.map((record, index) => (
          <article key={`${record.data_source}-${index}`}>
            <strong>
              {record.locality}, {record.city}
            </strong>

            <span>
              {record.property_type} · {record.area_sqft} sqft
            </span>

            <span>
              {formatPrice(record.transaction_value_inr)} ·{' '}
              {formatPrice(record.rate_per_sqft_inr)}/sqft
            </span>

            <small>
              Source: {record.data_source} ·{' '}
              {record.is_verified ? 'Verified' : 'Unverified demo'}
            </small>
          </article>
        ))}
      </div>
    )}
  </div>
)}

<p className="valuation-notice">{valuation.disclaimer}</p>
  </div>
)}
          </section>
        )}
      </main>
    </div>
  )
}

export default App
