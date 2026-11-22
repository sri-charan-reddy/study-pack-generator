import React from 'react'

export class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught an unhandled rendering error:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '60px 20px', maxWidth: 640, margin: '40px auto', textAlign: 'center', fontFamily: 'Inter, system-ui, sans-serif' }}>
          <div style={{ fontSize: 52, marginBottom: 16 }}>⚠️</div>
          <h2 style={{ fontSize: 22, fontWeight: 700, color: 'var(--text, #111827)', marginBottom: 10 }}>Application Encountered an Error</h2>
          <p style={{ color: 'var(--muted, #6b7280)', fontSize: 14, lineHeight: 1.5, marginBottom: 24 }}>
            {this.state.error?.message || 'An unexpected rendering error occurred. You can reload the page or navigate back to the dashboard.'}
          </p>
          <div style={{ display: 'flex', gap: 12, justifyContent: 'center' }}>
            <button
              onClick={() => window.location.reload()}
              style={{
                padding: '9px 18px',
                background: 'var(--primary, #4f46e5)',
                color: '#fff',
                border: 'none',
                borderRadius: 8,
                cursor: 'pointer',
                fontWeight: 600,
                fontSize: 14
              }}
            >
              Reload Page
            </button>
            <button
              onClick={() => { this.setState({ hasError: false, error: null }); window.location.href = '/' }}
              style={{
                padding: '9px 18px',
                background: 'var(--card, #f3f4f6)',
                color: 'var(--text, #374151)',
                border: '1px solid var(--border, #e5e7eb)',
                borderRadius: 8,
                cursor: 'pointer',
                fontWeight: 600,
                fontSize: 14
              }}
            >
              Go to Dashboard
            </button>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}
