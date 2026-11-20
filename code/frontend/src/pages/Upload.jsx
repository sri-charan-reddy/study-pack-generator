import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, SUPPORTED_EXTENSIONS, validateFile } from '../api.js'
import { Alert, Spinner } from '../components/ui.jsx'
import { formatBytes } from '../utils/format.js'

const DIFFICULTIES = ['mixed', 'easy', 'medium', 'hard']
const PROMPT_VERSIONS = [
  { id: 'v1', label: 'V1 – Baseline' },
  { id: 'v2', label: 'V2 – Role-Based' },
  { id: 'v3', label: 'V3 – Few-Shot Grounded' },
]

export default function Upload() {
  const navigate = useNavigate()
  const inputRef = useRef(null)
  const [file, setFile] = useState(null)
  const [over, setOver] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploaded, setUploaded] = useState(null)
  const [starting, setStarting] = useState(false)
  const [error, setError] = useState('')
  const [versions, setVersions] = useState([])
  const [options, setOptions] = useState({
    prompt_version: 'v3',
    difficulty: 'mixed',
    assignment_mcq_count: 10,
    assignment_difficulty: 'mixed',
    mcq_count: 10,
    short_count: 5,
    long_count: 3,
    run_review: true,
    apply_corrections: true,
  })

  useEffect(() => {
    api.promptVersions()
      .then((v) => {
        setVersions(v.versions.filter((x) => x.complete))
        setOptions((o) => ({ ...o, prompt_version: v.versions.some((x) => x.version === 'v3') ? 'v3' : v.default }))
      })
      .catch((e) => setError(e.message))
  }, [])

  function pick(f) {
    setError('')
    setUploaded(null)
    const problem = validateFile(f)
    if (problem) {
      setFile(null)
      setError(problem)
      return
    }
    setFile(f)
  }

  function onDrop(e) {
    e.preventDefault()
    setOver(false)
    if (e.dataTransfer.files?.[0]) pick(e.dataTransfer.files[0])
  }

  async function doUpload() {
    setUploading(true)
    setError('')
    try {
      const res = await api.upload(file)
      setUploaded(res)
    } catch (e) {
      setError(e.message)
    } finally {
      setUploading(false)
    }
  }

  async function doGenerate() {
    setStarting(true)
    setError('')
    try {
      const res = await api.startGeneration(uploaded.file_id, {
        ...options,
        mcq_count: Number(options.mcq_count),
        short_count: Number(options.short_count),
        long_count: Number(options.long_count),
      })
      navigate(`/generate/${res.study_pack_id}`)
    } catch (e) {
      setError(e.message)
      setStarting(false)
    }
  }

  const set = (k) => (e) => setOptions((o) => ({ ...o, [k]: e.target.value }))
  const totalQuestions = Number(options.mcq_count) + Number(options.short_count) + Number(options.long_count)

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Upload document</h1>
          <p>Supported: {SUPPORTED_EXTENSIONS.join(', ')} · up to 25 MB</p>
        </div>
      </div>

      {error && <div className="mb"><Alert>{error}</Alert></div>}

      <div className="card">
        <div className="card-title"><h2>1. Choose a file</h2></div>
        <div
          className={`dropzone${over ? ' over' : ''}`}
          onDragOver={(e) => { e.preventDefault(); setOver(true) }}
          onDragLeave={() => setOver(false)}
          onDrop={onDrop}
          onClick={() => inputRef.current?.click()}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => e.key === 'Enter' && inputRef.current?.click()}
        >
          <svg className="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"><path d="M12 16V4m0 0l-4 4m4-4l4 4M4 20h16" /></svg>
          <div><strong>Click to browse</strong> or drag and drop your lecture notes here</div>
          <div className="hint">PDF, PPT/PPTX, DOCX or TXT</div>
          <input ref={inputRef} type="file" accept={SUPPORTED_EXTENSIONS.join(',')} hidden onChange={(e) => e.target.files?.[0] && pick(e.target.files[0])} />
        </div>

        {file && (
          <div className="file-chip">
            <div>
              <div className="name">{file.name}</div>
              <div className="meta">{formatBytes(file.size)}{uploaded && ` · ${uploaded.page_count} ${uploaded.file_type === 'pptx' ? 'slides' : uploaded.file_type === 'docx' ? 'paragraphs' : 'pages'} · ${uploaded.word_count.toLocaleString()} words extracted`}</div>
            </div>
            <div className="spacer" />
            {!uploaded && (
              <button className="btn btn-primary btn-sm" onClick={doUpload} disabled={uploading}>
                {uploading ? <><Spinner /> Extracting…</> : 'Upload & extract text'}
              </button>
            )}
            {uploaded && <span className="badge badge-completed">Text extracted</span>}
            <button className="btn btn-outline btn-sm" onClick={() => { setFile(null); setUploaded(null); setError('') }} disabled={uploading}>Remove</button>
          </div>
        )}

        {uploaded?.warnings?.length > 0 && (
          <div className="mt"><Alert kind="warn">{uploaded.warnings.slice(0, 3).join(' ')}</Alert></div>
        )}
        {uploaded && (
          <details className="mt small">
            <summary className="muted">Preview extracted text</summary>
            <pre style={{ whiteSpace: 'pre-wrap', background: 'var(--bg)', padding: 12, borderRadius: 10, maxHeight: 240, overflow: 'auto' }}>{uploaded.text_preview}</pre>
          </details>
        )}
      </div>

      <div className="card">
        <div className="card-title"><h2>2. Generation settings</h2></div>
        <div className="grid grid-2 mb">
          <div className="field">
            <label>Prompt version</label>
            <div className="segmented">
              {PROMPT_VERSIONS.map((pv) => (
                <button
                  key={pv.id}
                  type="button"
                  className={options.prompt_version === pv.id ? 'active' : ''}
                  onClick={() => setOptions((o) => ({ ...o, prompt_version: pv.id }))}
                >
                  {pv.label}
                </button>
              ))}
            </div>
          </div>
          <div className="field">
            <label>Difficulty</label>
            <div className="segmented">
              {DIFFICULTIES.map((d) => (
                <button key={d} type="button" className={options.difficulty === d ? 'active' : ''} onClick={() => setOptions((o) => ({ ...o, difficulty: d, assignment_difficulty: d }))}>{d}</button>
              ))}
            </div>
            <span className="help">Mixed gives a balanced spread of easy, medium and hard.</span>
          </div>
        </div>
        <div className="card mb" style={{ background: 'var(--card)', border: '1px solid var(--border)', padding: '16px' }}>
          <div style={{ fontWeight: 600, marginBottom: 8, color: 'var(--primary)' }}>Practice Assignment (MCQ only)</div>
          <div className="grid grid-2">
            <div className="field">
              <label>Assignment questions (MCQ only)</label>
              <div className="segmented">
                {[5, 10, 15, 20].map((count) => (
                  <button
                    key={count}
                    type="button"
                    className={options.assignment_mcq_count === count ? 'active' : ''}
                    onClick={() => setOptions((o) => ({ ...o, assignment_mcq_count: count }))}
                  >
                    {count} MCQs
                  </button>
                ))}
              </div>
            </div>
            <div className="field">
              <label>Assignment difficulty</label>
              <div className="segmented">
                {DIFFICULTIES.map((d) => (
                  <button
                    key={d}
                    type="button"
                    className={options.assignment_difficulty === d ? 'active' : ''}
                    onClick={() => setOptions((o) => ({ ...o, assignment_difficulty: d }))}
                  >
                    {d}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
        <div className="form-grid">
          <div className="field">
            <label>MCQs (0–40)</label>
            <input type="number" min="0" max="40" value={options.mcq_count} onChange={set('mcq_count')} />
          </div>
          <div className="field">
            <label>Short-answer questions (0–20)</label>
            <input type="number" min="0" max="20" value={options.short_count} onChange={set('short_count')} />
          </div>
          <div className="field">
            <label>Long-answer questions (0–10)</label>
            <input type="number" min="0" max="10" value={options.long_count} onChange={set('long_count')} />
          </div>
        </div>
        <div className="row space mt">
          <label className="row small">
            <input type="checkbox" checked={options.run_review} onChange={(e) => setOptions((o) => ({ ...o, run_review: e.target.checked }))} />
            Run quality reviewer and apply its corrections
          </label>
          <button className="btn btn-primary btn-lg" onClick={doGenerate} disabled={!uploaded || starting || totalQuestions === 0}>
            {starting ? <><Spinner /> Starting…</> : 'Generate study pack'}
          </button>
        </div>
        {!uploaded && <p className="help mt muted small">Upload and extract a file first.</p>}
        {uploaded && totalQuestions === 0 && <p className="help mt muted small">Request at least one question.</p>}
      </div>
    </>
  )
}
