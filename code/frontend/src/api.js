// Centralised API service. The backend holds the Gemini key; the browser never sees it.
const BASE = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/$/, '')

export const SUPPORTED_EXTENSIONS = ['.pdf', '.pptx', '.ppt', '.docx', '.txt']
export const MAX_UPLOAD_MB = 25

export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.status = status
  }
}

async function request(path, options = {}) {
  let response
  try {
    response = await fetch(`${BASE}${path}`, options)
  } catch {
    throw new ApiError('Cannot reach the backend. Is the FastAPI server running on port 8000?', 0)
  }
  if (response.status === 204) return null
  const isJson = (response.headers.get('content-type') || '').includes('application/json')
  const body = isJson ? await response.json().catch(() => null) : await response.text().catch(() => '')
  if (!response.ok) {
    let detail = body && body.detail !== undefined ? body.detail : body
    if (Array.isArray(detail)) detail = detail.map((d) => `${(d.loc || []).slice(1).join('.')}: ${d.msg}`).join('; ')
    throw new ApiError(typeof detail === 'string' && detail ? detail : `Request failed (${response.status})`, response.status)
  }
  return body
}

const json = (method, data) => ({
  method,
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(data),
})

export const api = {
  health: () => request('/health'),
  aiHealth: () => request('/ai/health'),
  promptVersions: () => request('/prompts/versions'),

  upload(file) {
    const form = new FormData()
    form.append('file', file)
    return request('/upload', { method: 'POST', body: form })
  },

  startGeneration: (fileId, options) => request(`/generate/${fileId}/start`, json('POST', options)),

  listStudyPacks: (limit = 100) => request(`/study-packs?limit=${limit}`),
  getStudyPack: (id) => request(`/study-packs/${id}`),
  deleteStudyPack: (id) => request(`/study-packs/${id}`, { method: 'DELETE' }),
  downloadUrl: (id, format) => `${BASE}/study-packs/${id}/download?format=${format}`,
}

export function validateFile(file) {
  if (!file) return 'Choose a file first.'
  const ext = '.' + (file.name.split('.').pop() || '').toLowerCase()
  if (!SUPPORTED_EXTENSIONS.includes(ext)) return `Unsupported file type "${ext}". Allowed: ${SUPPORTED_EXTENSIONS.join(', ')}`
  if (file.size === 0) return 'The file is empty.'
  if (file.size > MAX_UPLOAD_MB * 1024 * 1024) return `File is larger than ${MAX_UPLOAD_MB} MB.`
  return null
}
