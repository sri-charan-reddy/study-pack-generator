import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { api } from '../api.js'
import { Alert, Badge, Loading, Spinner } from '../components/ui.jsx'
import { STAGE_LABELS, STAGE_ORDER, formatSeconds } from '../utils/format.js'

const POLL_MS = 2000

export default function Generation() {
  const { packId } = useParams()
  const navigate = useNavigate()
  const [pack, setPack] = useState(null)
  const [error, setError] = useState('')
  const [elapsed, setElapsed] = useState(0)
  const timer = useRef(null)

  useEffect(() => {
    let cancelled = false
    const started = Date.now()
    const tick = setInterval(() => setElapsed((Date.now() - started) / 1000), 1000)

    async function poll() {
      try {
        const p = await api.getStudyPack(packId)
        if (cancelled) return
        setPack(p)
        setError('')
        if (p.status === 'completed') {
          clearInterval(tick)
          setTimeout(() => !cancelled && navigate(`/packs/${packId}`, { replace: true }), 900)
          return
        }
        if (p.status === 'failed') {
          clearInterval(tick)
          return
        }
      } catch (e) {
        if (cancelled) return
        setError(e.message)
        if (e.status === 404) { clearInterval(tick); return }
      }
      timer.current = setTimeout(poll, POLL_MS)
    }
    poll()
    return () => { cancelled = true; clearInterval(tick); clearTimeout(timer.current) }
  }, [packId, navigate])

  if (!pack && !error) return <Loading text="Connecting to generation job…" />

  const current = pack?.current_stage || ''
  const currentIdx = STAGE_ORDER.indexOf(current)
  const done = pack?.status === 'completed'
  const failed = pack?.status === 'failed'
  const progress = done ? 100 : Math.max(4, ((currentIdx + 0.5) / STAGE_ORDER.length) * 100)

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Generating study pack</h1>
          <p>{pack?.filename} · prompt {pack?.prompt_version?.toUpperCase()} · {pack?.model}</p>
        </div>
        {pack && <Badge value={pack.status} />}
      </div>

      {error && <div className="mb"><Alert>{error}</Alert></div>}

      <div className="card">
        <div className="row space">
          <div className="row">
            {!done && !failed && <Spinner />}
            <strong>{done ? 'Completed' : failed ? 'Generation failed' : current ? STAGE_LABELS[current] : 'Queued, waiting to start…'}</strong>
          </div>
          <span className="muted small">{done ? `Took ${formatSeconds(pack.total_seconds)}` : `${formatSeconds(elapsed)} elapsed`}</span>
        </div>
        <div className="progress"><div style={{ width: `${progress}%` }} /></div>

        <div className="stages">
          {STAGE_ORDER.map((stage, i) => {
            const state = done || i < currentIdx ? 'done' : i === currentIdx ? (failed ? 'failed' : 'active') : ''
            return (
              <div className={`stage ${state}`} key={stage}>
                <span className="num">{state === 'done' ? '✓' : i + 1}</span>
                <span className="label">{STAGE_LABELS[stage]}</span>
                <span className="sub">{state === 'active' ? 'Running…' : state === 'done' ? 'Done' : state === 'failed' ? 'Failed' : 'Pending'}</span>
              </div>
            )
          })}
        </div>

        {failed && (
          <div className="mt">
            <Alert>
              <div>
                <strong>Error:</strong> {pack.error || 'Unknown error.'}
                <div className="small mt">Check the backend terminal for details, then try again. Rate limits usually clear after a minute.</div>
              </div>
            </Alert>
            <div className="btn-row mt">
              <Link to="/upload" className="btn btn-primary">Try again</Link>
              <Link to="/packs" className="btn btn-outline">Go to history</Link>
            </div>
          </div>
        )}
        {done && <div className="mt"><Alert kind="success">Study pack ready. Opening the viewer…</Alert></div>}
      </div>
    </>
  )
}
