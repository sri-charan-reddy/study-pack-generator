import { useEffect, useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import { api } from '../api.js'

const Icon = ({ d }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d={d} />
  </svg>
)

const links = [
  { to: '/', label: 'Dashboard', icon: 'M3 12l9-8 9 8M5 10v10h14V10' },
  { to: '/upload', label: 'Upload document', icon: 'M12 16V4m0 0l-4 4m4-4l4 4M4 20h16' },
  { to: '/packs', label: 'Study pack history', icon: 'M4 6h16M4 12h16M4 18h10' },
]

export default function Layout() {
  const [health, setHealth] = useState(null)

  useEffect(() => {
    api.aiHealth().then(setHealth).catch(() => setHealth({ error: true }))
  }, [])

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-logo">SP</div>
          <div>
            <div className="brand-name">Study Pack</div>
            <div className="brand-sub">AI notes to exam prep</div>
          </div>
        </div>
        <nav className="nav">
          {links.map((l) => (
            <NavLink key={l.to} to={l.to} end={l.to === '/'}>
              <Icon d={l.icon} />
              <span>{l.label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-foot">
          {health === null && <span><span className="status-dot" />Checking backend…</span>}
          {health?.error && <span><span className="status-dot bad" />Backend offline</span>}
          {health && !health.error && (
            <span>
              <span className={`status-dot ${health.gemini_configured ? 'ok' : 'bad'}`} />
              {health.gemini_configured ? `Gemini ready · ${health.model}` : 'Gemini key missing'}
            </span>
          )}
        </div>
      </aside>
      <main className="main">
        <Outlet />
      </main>
    </div>
  )
}
