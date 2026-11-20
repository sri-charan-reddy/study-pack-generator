export function formatBytes(bytes) {
  if (!bytes && bytes !== 0) return ''
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
}

export function formatDate(value) {
  if (!value) return ''
  const d = new Date(value)
  return Number.isNaN(d.getTime()) ? value : d.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
}

export function formatSeconds(s) {
  if (s === undefined || s === null) return ''
  return s < 60 ? `${s.toFixed(0)} s` : `${Math.floor(s / 60)} min ${Math.round(s % 60)} s`
}

export const STAGE_LABELS = {
  '01_document_understanding': 'Document understanding',
  '02_summary_generation': 'Summary generation',
  '03_key_concept_extraction': 'Key concept extraction',
  '04_question_generation': 'Question generation',
  '05_answer_generation': 'Answer generation',
  '06_quality_evaluation': 'Quality review',
}

export const STAGE_ORDER = Object.keys(STAGE_LABELS)
