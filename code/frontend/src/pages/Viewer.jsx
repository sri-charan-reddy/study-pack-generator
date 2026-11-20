import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { api } from '../api.js'
import { Alert, Badge, Loading, Spinner } from '../components/ui.jsx'
import { formatDate, formatSeconds } from '../utils/format.js'

const LETTERS = ['A', 'B', 'C', 'D']
const DIFFICULTIES = ['mixed', 'easy', 'medium', 'hard']

export default function Viewer() {
  const { packId } = useParams()
  const navigate = useNavigate()
  const [record, setRecord] = useState(null)
  const [error, setError] = useState('')
  const [tab, setTab] = useState('summary')
  const [showAnswers, setShowAnswers] = useState(true)

  useEffect(() => {
    api.getStudyPack(packId).then((r) => {
      if (r.status !== 'completed') navigate(`/generate/${packId}`, { replace: true })
      setRecord(r)
    }).catch((e) => setError(e.message))
  }, [packId, navigate])

  if (error) return <Alert>{error}</Alert>
  if (!record?.pack) return <Loading text="Loading study pack…" />

  const pack = record.pack
  const { document: doc, summaries, key_concepts: kc, questions: q, review, meta, practice_assignment } = pack
  const assignment = practice_assignment || {
    title: 'Practice Assignment',
    difficulty: 'mixed',
    mcq_count: 0,
    questions: [],
    submission: null,
  }

  const tabs = [
    ['summary', 'Summary', summaries.topics.length],
    ['assignment', 'Practice Assignment', assignment.questions?.length || 0],
    ['concepts', 'Key concepts', kc.terms.length + kc.formulas.length + kc.key_concepts.length],
    ['mcq', 'MCQs', q.mcqs.length],
    ['short', 'Short questions', q.short_answer.length],
    ['long', 'Long questions', q.long_answer.length],
    ['review', 'Quality report', review ? review.issues.length : 0],
  ]

  function updateAssignment(updated) {
    setRecord((prev) => ({
      ...prev,
      pack: {
        ...prev.pack,
        practice_assignment: updated,
      },
    }))
  }

  return (
    <>
      <div className="page-head">
        <div>
          <h1>{doc.title}</h1>
          <p>{doc.subject} · {record.filename} · prompt {meta.prompt_version.toUpperCase()} · {meta.model} · {formatDate(record.created_at)} · {formatSeconds(meta.total_seconds)}</p>
        </div>
        <div className="btn-row">
          <a className="btn btn-primary" href={api.downloadUrl(record.id, 'pdf')} download>Download PDF</a>
          <a className="btn btn-outline" href={api.downloadUrl(record.id, 'docx')} download>Download DOCX</a>
          <Link className="btn btn-outline" to="/packs">History</Link>
        </div>
      </div>

      <div className="grid grid-4 mb">
        <div className="card stat"><span className="stat-label">Topics</span><span className="stat-value">{doc.main_topics.length}</span></div>
        <div className="card stat"><span className="stat-label">Questions</span><span className="stat-value">{q.mcqs.length + q.short_answer.length + q.long_answer.length}</span><span className="stat-hint">{q.mcqs.length} MCQ · {q.short_answer.length} short · {q.long_answer.length} long</span></div>
        <div className="card stat"><span className="stat-label">Quality score</span><span className="stat-value">{review ? review.overall_score : '–'}</span><span className="stat-hint">{review ? <Badge value={review.verdict} /> : 'Review skipped'}</span></div>
        <div className="card stat"><span className="stat-label">Tokens</span><span className="stat-value">{(meta.prompt_tokens + meta.output_tokens).toLocaleString()}</span><span className="stat-hint">{meta.chunk_count} chunk{meta.chunk_count > 1 ? 's' : ''} · {meta.corrections_applied} corrections applied</span></div>
      </div>

      <div className="card">
        <div className="tabs">
          {tabs.map(([key, label, count]) => (
            <button key={key} className={tab === key ? 'active' : ''} onClick={() => setTab(key)}>{label}<span className="count">{count}</span></button>
          ))}
        </div>

        {tab === 'summary' && (
          <SummaryTab
            doc={doc}
            summaries={summaries}
            assignment={assignment}
            onGoToAssignment={() => setTab('assignment')}
          />
        )}
        {tab === 'assignment' && (
          <PracticeAssignmentTab
            packId={record.id}
            assignment={assignment}
            onUpdateAssignment={updateAssignment}
          />
        )}
        {tab === 'concepts' && <ConceptsTab kc={kc} />}
        {(tab === 'mcq' || tab === 'short' || tab === 'long') && (
          <div className="toggle-answers">
            <button className="btn btn-outline btn-sm" onClick={() => setShowAnswers((s) => !s)}>{showAnswers ? 'Hide answers' : 'Show answers'}</button>
          </div>
        )}
        {tab === 'mcq' && <McqTab items={q.mcqs} show={showAnswers} />}
        {tab === 'short' && <ShortTab items={q.short_answer} show={showAnswers} />}
        {tab === 'long' && <LongTab items={q.long_answer} show={showAnswers} />}
        {tab === 'review' && <ReviewTab review={review} meta={meta} />}
      </div>
    </>
  )
}

function SummaryTab({ doc, summaries, assignment, onGoToAssignment }) {
  return (
    <>
      {summaries.overall_summary && <div className="topic"><h3>Overview</h3><p>{summaries.overall_summary}</p></div>}
      <div className="topic">
        <h3>Topic outline</h3>
        <div className="row">
          {doc.main_topics.map((t) => <span key={t.name} className="badge badge-neutral" title={t.description}>{t.name}</span>)}
        </div>
        {doc.topic_relationships?.length > 0 && (
          <ul className="small muted">
            {doc.topic_relationships.map((r, i) => <li key={i}>{r.from} → {r.to}{r.relation ? ` (${r.relation})` : ''}</li>)}
          </ul>
        )}
      </div>
      {summaries.topics.map((t) => (
        <div className="topic" key={t.topic}>
          <h3>{t.topic}</h3>
          <p>{t.summary}</p>
          {t.simple_explanation && <div className="simple"><strong>In simple terms:</strong> {t.simple_explanation}</div>}
          {t.important_points.length > 0 && <><div className="sub-label">Important points</div><ul>{t.important_points.map((p, i) => <li key={i}>{p}</li>)}</ul></>}
          {t.formulas.length > 0 && <><div className="sub-label">Formulas</div><div>{t.formulas.map((f, i) => <div key={i}><span className="formula">{f}</span></div>)}</div></>}
          {t.examples.length > 0 && <><div className="sub-label">Examples</div><ul>{t.examples.map((e, i) => <li key={i}>{e}</li>)}</ul></>}
        </div>
      ))}

      {/* Practice Assignment Section immediately after summaries */}
      <div className="card mt" style={{ background: 'linear-gradient(135deg, rgba(30, 58, 138, 0.05), rgba(59, 130, 246, 0.08))', border: '1px solid rgba(59, 130, 246, 0.3)', padding: '20px', borderRadius: '12px' }}>
        <div className="row space">
          <div>
            <h3 style={{ margin: 0, color: 'var(--primary)' }}>Practice Assignment (MCQ Only)</h3>
            <p style={{ margin: '6px 0 0', color: 'var(--text-muted)', fontSize: '0.95rem' }}>
              Test your understanding of this lecture with {assignment?.questions?.length || 10} grounded multiple-choice questions with instant scoring, answer keys, and explanations.
            </p>
          </div>
          <button className="btn btn-primary" onClick={onGoToAssignment}>
            Open Practice Assignment →
          </button>
        </div>
      </div>
    </>
  )
}

function PracticeAssignmentTab({ packId, assignment, onUpdateAssignment }) {
  const [answers, setAnswers] = useState(assignment.submission?.user_answers || {})
  const [submitting, setSubmitting] = useState(false)
  const [retrying, setRetrying] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [actionError, setActionError] = useState('')
  const [reqCount, setReqCount] = useState(assignment.questions?.length || 10)
  const [reqDiff, setReqDiff] = useState(assignment.difficulty || 'mixed')

  const submission = assignment.submission
  const isSubmitted = Boolean(submission?.is_submitted)
  const questions = assignment.questions || []
  const answeredCount = Object.keys(answers).filter((k) => answers[k]).length

  function handleSelect(qid, letter) {
    if (isSubmitted) return
    setAnswers((prev) => ({
      ...prev,
      [qid]: letter,
    }))
  }

  async function handleSubmit() {
    setSubmitting(true)
    setActionError('')
    try {
      const updated = await api.submitAssignment(packId, answers)
      onUpdateAssignment(updated)
    } catch (e) {
      setActionError(e.message)
    } finally {
      setSubmitting(false)
    }
  }

  async function handleRetry() {
    setRetrying(true)
    setActionError('')
    try {
      const updated = await api.retryAssignment(packId)
      setAnswers({})
      onUpdateAssignment(updated)
    } catch (e) {
      setActionError(e.message)
    } finally {
      setRetrying(false)
    }
  }

  async function handleReconfigure() {
    setGenerating(true)
    setActionError('')
    try {
      const updated = await api.generateAssignment(packId, {
        mcq_count: reqCount,
        difficulty: reqDiff,
      })
      setAnswers({})
      onUpdateAssignment(updated)
    } catch (e) {
      setActionError(e.message)
    } finally {
      setGenerating(false)
    }
  }

  return (
    <div style={{ marginTop: 8 }}>
      {actionError && <div className="mb"><Alert>{actionError}</Alert></div>}

      {/* Assignment Configuration & Metadata Toolbar */}
      <div className="card mb" style={{ background: 'var(--bg)', border: '1px solid var(--border)', padding: '16px' }}>
        <div className="row space">
          <div>
            <h3 style={{ margin: 0, fontSize: '1.15rem' }}>Practice Assignment Configuration</h3>
            <span className="small muted">Multiple Choice Questions (MCQ Only) · Strictly grounded in lecture notes</span>
          </div>
          <div className="row" style={{ gap: '10px' }}>
            <div className="row" style={{ gap: '6px' }}>
              <span className="small muted">Count:</span>
              <div className="segmented">
                {[5, 10, 15, 20].map((n) => (
                  <button
                    key={n}
                    type="button"
                    className={reqCount === n ? 'active' : ''}
                    onClick={() => setReqCount(n)}
                    disabled={generating}
                  >
                    {n}
                  </button>
                ))}
              </div>
            </div>
            <div className="row" style={{ gap: '6px' }}>
              <span className="small muted">Difficulty:</span>
              <div className="segmented">
                {DIFFICULTIES.map((d) => (
                  <button
                    key={d}
                    type="button"
                    className={reqDiff === d ? 'active' : ''}
                    onClick={() => setReqDiff(d)}
                    disabled={generating}
                  >
                    {d}
                  </button>
                ))}
              </div>
            </div>
            <button
              className="btn btn-outline btn-sm"
              onClick={handleReconfigure}
              disabled={generating || submitting || retrying}
            >
              {generating ? <><Spinner /> Generating…</> : 'Generate / Reconfigure'}
            </button>
          </div>
        </div>
      </div>

      {/* Submission Score & Result Banner */}
      {isSubmitted && submission && (
        <div className={`assignment-banner score-banner ${submission.percentage < 70 ? 'needs-review' : ''}`}>
          <div className="row space">
            <div>
              <div style={{ fontSize: '1.4rem', fontWeight: 700, color: submission.percentage >= 70 ? '#065f46' : '#92400e' }}>
                Score: {submission.score} / {submission.total} ({submission.percentage}%)
              </div>
              <div style={{ fontSize: '0.9rem', color: '#4b5563', marginTop: 4 }}>
                {submission.percentage >= 70
                  ? 'Great performance! You demonstrated solid mastery of the lecture concepts.'
                  : 'Review the explanations below and retry to strengthen your understanding.'}
              </div>
            </div>
            <div className="btn-row">
              <button className="btn btn-primary btn-sm" onClick={handleRetry} disabled={retrying}>
                {retrying ? <><Spinner /> Resetting…</> : 'Retry Assignment'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Questions List */}
      {questions.length === 0 ? (
        <p className="muted">No practice assignment questions generated. Click Generate above.</p>
      ) : (
        questions.map((q, idx) => {
          const userChoice = answers[q.id]
          const isCorrect = userChoice && userChoice === q.correct_option

          return (
            <div className="question" key={q.id || idx}>
              <div className="q-head">
                <span className="q-num">Q{idx + 1}.</span>
                <span className="q-text">{q.question}</span>
              </div>
              <div className="q-tags">
                <Badge value={q.difficulty || 'medium'} />
                {q.topic && <span className="badge badge-neutral">{q.topic}</span>}
                <span className="small muted">{q.id}</span>
                {isSubmitted && (
                  isCorrect ? (
                    <span className="badge badge-completed">Correct (+1)</span>
                  ) : (
                    <span className="badge badge-failed">Incorrect (0)</span>
                  )
                )}
              </div>

              {/* Four Selectable Options A, B, C, D */}
              <div className="mt" style={{ marginTop: '10px' }}>
                {q.options.map((opt, j) => {
                  const letter = LETTERS[j]
                  const isSelected = userChoice === letter
                  let btnClass = 'assignment-option-btn'
                  let tag = null

                  if (!isSubmitted) {
                    if (isSelected) btnClass += ' selected'
                  } else {
                    const isRightOption = letter === q.correct_option
                    if (isRightOption) {
                      btnClass += ' opt-correct'
                      tag = <span className="opt-tag correct">Correct Answer</span>
                    } else if (isSelected && !isRightOption) {
                      btnClass += ' opt-incorrect'
                      tag = <span className="opt-tag incorrect">Your Choice</span>
                    }
                  }

                  return (
                    <button
                      key={j}
                      type="button"
                      className={btnClass}
                      onClick={() => handleSelect(q.id, letter)}
                      disabled={isSubmitted}
                    >
                      <span className="letter" style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        width: '26px',
                        height: '26px',
                        borderRadius: '50%',
                        background: isSelected ? 'var(--primary)' : 'rgba(0,0,0,0.06)',
                        color: isSelected ? '#fff' : 'inherit',
                        fontWeight: 700,
                        fontSize: '13px',
                      }}>
                        {letter}
                      </span>
                      <span>{opt}</span>
                      {tag}
                    </button>
                  )
                })}
              </div>

              {/* Answer & Explanation (Shown only after submission) */}
              {isSubmitted && (
                <div className="answer-box">
                  <div className="label">
                    Correct Answer: Option {q.correct_option}
                  </div>
                  {q.explanation && (
                    <div className="explain">
                      <strong>Explanation: </strong>{q.explanation}
                    </div>
                  )}
                </div>
              )}
            </div>
          )
        })
      )}

      {/* Bottom Assignment Action Bar */}
      {questions.length > 0 && (
        <div className="card mt" style={{ background: 'var(--bg)', padding: '16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            {!isSubmitted ? (
              <span className="small muted">
                <strong>{answeredCount}</strong> of <strong>{questions.length}</strong> questions answered
                {answeredCount < questions.length && ' (unanswered questions will be scored 0)'}
              </span>
            ) : (
              <span className="small muted">
                Assignment completed. Review detailed answers above.
              </span>
            )}
          </div>
          <div>
            {!isSubmitted ? (
              <button
                className="btn btn-primary btn-lg"
                onClick={handleSubmit}
                disabled={submitting}
              >
                {submitting ? <><Spinner /> Scoring…</> : 'Submit Assignment'}
              </button>
            ) : (
              <button
                className="btn btn-outline btn-lg"
                onClick={handleRetry}
                disabled={retrying}
              >
                {retrying ? <><Spinner /> Resetting…</> : 'Retry Assignment'}
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

function ConceptsTab({ kc }) {
  return (
    <>
      {kc.terms.length > 0 && (
        <div className="topic">
          <h3>Terms and definitions</h3>
          {kc.terms.map((t) => (
            <div className="term-row" key={t.term}>
              <div className="t">{t.term}</div>
              <div>{t.definition}{t.example && <div className="small muted">Example: {t.example}</div>}</div>
            </div>
          ))}
        </div>
      )}
      {kc.formulas.length > 0 && (
        <div className="topic">
          <h3>Formulas</h3>
          {kc.formulas.map((f) => (
            <div className="term-row" key={f.name}>
              <div className="t">{f.name}</div>
              <div><span className="formula">{f.formula}</span>{(f.variables || f.usage) && <div className="small muted">{f.variables} {f.usage}</div>}</div>
            </div>
          ))}
        </div>
      )}
      {kc.key_concepts.length > 0 && (
        <div className="topic">
          <h3>Core concepts</h3>
          {kc.key_concepts.map((c) => (
            <div className="term-row" key={c.concept}>
              <div className="t">{c.concept}{c.topic && <div className="small muted">{c.topic}</div>}</div>
              <div>{c.explanation}</div>
            </div>
          ))}
        </div>
      )}
      {kc.examples.length > 0 && <div className="topic"><h3>Examples from the notes</h3><ul>{kc.examples.map((e, i) => <li key={i}>{e}</li>)}</ul></div>}
      {kc.terms.length + kc.formulas.length + kc.key_concepts.length === 0 && <p className="muted">No key concepts were extracted.</p>}
    </>
  )
}

function QHead({ n, item }) {
  return (
    <>
      <div className="q-head"><span className="q-num">Q{n}.</span><span className="q-text">{item.question}</span></div>
      <div className="q-tags"><Badge value={item.difficulty} />{item.topic && <span className="badge badge-neutral">{item.topic}</span>}<span className="small muted">{item.id}</span></div>
    </>
  )
}

function McqTab({ items, show }) {
  if (!items.length) return <p className="muted">No MCQs in this pack.</p>
  return items.map((m, i) => (
    <div className="question" key={m.id}>
      <QHead n={i + 1} item={m} />
      <ul className="options">
        {m.options.map((o, j) => (
          <li key={j} className={show && m.correct_option === LETTERS[j] ? 'correct' : ''}><span className="letter">{LETTERS[j]}</span><span>{o}</span></li>
        ))}
      </ul>
      {show && (
        <div className="answer-box">
          <div className="label">Answer: {m.correct_option || 'not available'}</div>
          {m.explanation && <div className="explain">{m.explanation}</div>}
        </div>
      )}
    </div>
  ))
}

function ShortTab({ items, show }) {
  if (!items.length) return <p className="muted">No short-answer questions in this pack.</p>
  return items.map((s, i) => (
    <div className="question" key={s.id}>
      <QHead n={i + 1} item={s} />
      {show && (
        <div className="answer-box">
          <div className="label">Model answer</div>
          <div>{s.answer || 'Not available'}</div>
          {s.explanation && <div className="explain">{s.explanation}</div>}
        </div>
      )}
    </div>
  ))
}

function LongTab({ items, show }) {
  if (!items.length) return <p className="muted">No long-answer questions in this pack.</p>
  return items.map((l, i) => (
    <div className="question" key={l.id}>
      <QHead n={i + 1} item={l} />
      {show && (
        <div className="answer-box">
          <div className="label">Model answer</div>
          <div style={{ whiteSpace: 'pre-wrap' }}>{l.answer || 'Not available'}</div>
          {l.key_points.length > 0 && <><div className="label" style={{ marginTop: 10 }}>Key points for marks</div><ul>{l.key_points.map((k, j) => <li key={j}>{k}</li>)}</ul></>}
        </div>
      )}
    </div>
  ))
}

function ReviewTab({ review, meta }) {
  if (!review) return <p className="muted">The quality reviewer was not run for this pack.</p>
  const s = review.scores
  return (
    <>
      <div className="scores mb">
        {Object.entries(s).map(([k, v]) => <div className="score" key={k}><div className="v">{v}</div><div className="l">{k.replace(/_/g, ' ')}</div></div>)}
      </div>
      <div className="row mb">
        <strong>Overall {review.overall_score} / 10</strong>
        <Badge value={review.verdict} />
        <span className="small muted">{meta.corrections_applied} corrections applied · {meta.duplicates_removed} duplicates removed</span>
      </div>
      {review.strengths.length > 0 && <div className="topic"><h3>Strengths</h3><ul>{review.strengths.map((x, i) => <li key={i}>{x}</li>)}</ul></div>}
      {review.issues.length > 0 && (
        <div className="topic">
          <h3>Issues found</h3>
          {review.issues.map((i, idx) => (
            <div className="issue" key={idx}>
              <div className="row"><Badge value={i.severity === 'high' ? 'failed' : i.severity === 'medium' ? 'running' : 'completed'} /><strong>{i.type}</strong><span className="small muted">{i.location}</span></div>
              <div>{i.description}</div>
              {i.suggested_fix && <div className="fix">Suggested fix: {i.suggested_fix}</div>}
            </div>
          ))}
        </div>
      )}
      {review.unsupported_claims.length > 0 && <div className="topic"><h3>Unsupported claims</h3><ul>{review.unsupported_claims.map((x, i) => <li key={i}>{x}</li>)}</ul></div>}
      {review.duplicate_questions.length > 0 && <div className="topic"><h3>Duplicate questions</h3><ul>{review.duplicate_questions.map((g, i) => <li key={i}>{g.join(' ≈ ')}</li>)}</ul></div>}
      {review.corrections.length > 0 && (
        <div className="topic">
          <h3>Corrections</h3>
          {review.corrections.map((c, i) => (
            <div className="issue" key={i}><strong>{c.target_type} {c.target_id}</strong> · {c.field}<div>{c.corrected_value}</div>{c.reason && <div className="fix">{c.reason}</div>}</div>
          ))}
        </div>
      )}
      {review.reviewer_notes && <div className="topic"><h3>Reviewer notes</h3><p>{review.reviewer_notes}</p></div>}
    </>
  )
}
