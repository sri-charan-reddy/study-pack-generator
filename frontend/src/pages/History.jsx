import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api.js'
import { Alert, Badge, Empty, Loading } from '../components/ui.jsx'
import { formatDate, formatSeconds } from '../utils/format.js'

export default function History() {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [deleting, setDeleting] = useState(null)

  const load = () => api.listStudyPacks(200).then(setData).catch((e) => setError(e.message))
  useEffect(() => { load() }, [])

  async function remove(p) {
    if (!window.confirm(`Delete the study pack for "${p.title || p.filename}"? This cannot be undone.`)) return
    setDeleting(p.id)
    setError('')
    try {
      await api.deleteStudyPack(p.id)
      await load()
    } catch (e) {
      setError(e.message)
    } finally {
      setDeleting(null)
    }
  }

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Study pack history</h1>
          <p>Every generated pack is saved in SQLite and can be reopened, downloaded or deleted.</p>
        </div>
        <Link to="/upload" className="btn btn-primary">New study pack</Link>
      </div>

      {error && <div className="mb"><Alert>{error}</Alert></div>}
      {!data && !error && <Loading />}

      {data && (
        <div className="card">
          {data.items.length === 0 ? (
            <Empty title="Nothing saved yet">Generate a study pack and it will appear here.</Empty>
          ) : (
            <div className="table-wrap">
              <table className="table">
                <thead>
                  <tr>
                    <th>Document</th><th>Version</th><th>Status</th><th>Questions</th><th>Score</th><th>Created</th><th></th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((p) => (
                    <tr key={p.id}>
                      <td className="doc-cell">
                        <div className="title-cell" title={p.title}>{p.title || p.filename}</div>
                        <div className="small muted">{p.filename}</div>
                      </td>
                      <td><Badge value={p.prompt_version} className="badge-neutral" /></td>
                      <td><Badge value={p.status} />{p.status === 'running' && <span className="small muted"> {p.current_stage.slice(3).replace(/_/g, ' ')}</span>}</td>
                      <td>{p.status === 'completed' ? `${p.mcq_count} / ${p.short_count} / ${p.long_count}` : '–'}</td>
                      <td className="nowrap">{p.overall_score != null ? <><strong>{p.overall_score}</strong> <Badge value={p.verdict} /></> : '–'}</td>
                      <td className="small nowrap">{formatDate(p.created_at)}{p.total_seconds ? <div className="muted">{formatSeconds(p.total_seconds)}</div> : null}</td>
                      <td className="actions">
                        <div className="btn-row">
                          {p.status === 'completed' && <Link className="btn btn-outline btn-sm" to={`/packs/${p.id}`}>Open</Link>}
                          {(p.status === 'running' || p.status === 'pending') && <Link className="btn btn-outline btn-sm" to={`/generate/${p.id}`}>Progress</Link>}
                          <button className="btn btn-danger btn-sm" onClick={() => remove(p)} disabled={deleting === p.id}>{deleting === p.id ? 'Deleting…' : 'Delete'}</button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </>
  )
}
