export function Spinner({ large }) {
  return <span className={`spinner${large ? ' lg' : ''}`} role="status" aria-label="Loading" />
}

export function Loading({ text = 'Loading…' }) {
  return (
    <div className="center">
      <Spinner large />
      <span>{text}</span>
    </div>
  )
}

export function Alert({ kind = 'error', children }) {
  return (
    <div className={`alert alert-${kind}`} role={kind === 'error' ? 'alert' : 'status'}>
      {children}
    </div>
  )
}

export function Badge({ value, className = '' }) {
  const key = String(value || 'neutral').toLowerCase().replace(/\s+/g, '_')
  return <span className={`badge badge-${key} ${className}`}>{String(value || '').replace('_', ' ')}</span>
}

export function Empty({ title, children }) {
  return (
    <div className="empty">
      <h3>{title}</h3>
      <div>{children}</div>
    </div>
  )
}

export function Stat({ label, value, hint }) {
  return (
    <div className="card stat">
      <span className="stat-label">{label}</span>
      <span className="stat-value">{value}</span>
      {hint && <span className="stat-hint">{hint}</span>}
    </div>
  )
}
