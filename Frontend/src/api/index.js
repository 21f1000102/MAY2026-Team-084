import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' }
})

// attach JWT token to every request
api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Redirect to login when a *session* expires.
// The auth endpoints are excluded: a wrong password also returns 401, and
// reloading the page there tore the component down before its error banner
// could render, so a failed login looked like a silent no-op.
const AUTH_PATHS = ['/auth/login', '/auth/register']

api.interceptors.response.use(
  res => res,
  err => {
    const url = err.config?.url || ''
    const isAuthAttempt = AUTH_PATHS.some(p => url.includes(p))
    if (err.response?.status === 401 && !isAuthAttempt) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      if (!window.location.pathname.startsWith('/login')) {
        window.location.href = '/login'
      }
    }
    return Promise.reject(err)
  }
)

/**
 * Human-readable message for any axios failure.
 * Handles JSON {error}, HTML error pages, and network failures — pages used to
 * render `e.response.data.error` which is undefined for non-JSON responses.
 */
export function errText(e, fallback = 'Something went wrong. Please try again.') {
  if (e?.response) {
    const { status, data } = e.response
    if (data && typeof data === 'object' && data.error) return data.error
    if (typeof data === 'string' && data && !data.trim().startsWith('<')) return data
    if (status === 403) return 'You are not allowed to perform this action.'
    if (status === 404) return 'Not found.'
    if (status === 409) return 'That conflicts with existing data.'
    return `Server error (${status}). Please try again.`
  }
  if (e?.request) return 'Cannot reach the server. Is the backend running?'
  return fallback
}

// ── AUTH ──────────────────────────────────────────────────────
export const authAPI = {
  login: (data) => api.post('/auth/login', data),
  register: (data) => api.post('/auth/register', data),
  me: () => api.get('/auth/me'),
  changePassword: (data) => api.put('/auth/change-password', data)
}

// ── MEMBERS ───────────────────────────────────────────────────
export const membersAPI = {
  getAll: () => api.get('/members/'),
  add: (data) => api.post('/members/', data),
  update: (id, data) => api.put(`/members/${id}`, data),
  deactivate: (id) => api.delete(`/members/${id}`),
  getApartments: () => api.get('/members/apartments'),
  addApartment: (data) => api.post('/members/apartments', data),
  getWorkers: () => api.get('/members/workers'),
}

// ── COMPLAINTS ────────────────────────────────────────────────
export const complaintsAPI = {
  getAll: () => api.get('/complaints/'),
  raise: (data) => api.post('/complaints/', data),
  get: (id) => api.get(`/complaints/${id}`),
  assign: (id, data) => api.put(`/complaints/${id}/assign`, data),
  updateStatus: (id, data) => api.put(`/complaints/${id}/status`, data),
  delete: (id) => api.delete(`/complaints/${id}`)
}

// ── INVOICES ──────────────────────────────────────────────────
export const invoicesAPI = {
  getAll: () => api.get('/invoices/'),
  create: (data) => api.post('/invoices/', data),
  bulkGenerate: (data) => api.post('/invoices/bulk', data),
  markPaid: (id, data) => api.put(`/invoices/${id}/pay`, data),
  getReceipt: (id) => api.get(`/invoices/${id}/receipt`),
  getPending: () => api.get('/invoices/pending')
}

// ── EXPENSES ──────────────────────────────────────────────────
export const expensesAPI = {
  getAll: () => api.get('/expenses/'),
  add: (data) => api.post('/expenses/', data),
  update: (id, data) => api.put(`/expenses/${id}`, data),
  delete: (id) => api.delete(`/expenses/${id}`),
  summary: (month, year) => api.get(`/expenses/summary?month=${month}&year=${year}`)
}

// ── NOTICES ───────────────────────────────────────────────────
export const noticesAPI = {
  getAll: () => api.get('/notices/'),
  add: (data) => api.post('/notices/', data),
  update: (id, data) => api.put(`/notices/${id}`, data),
  delete: (id) => api.delete(`/notices/${id}`)
}

// ── EMERGENCY CONTACTS ────────────────────────────────────────
export const emergencyAPI = {
  getAll: () => api.get('/emergency/'),
  add: (data) => api.post('/emergency/', data),
  update: (id, data) => api.put(`/emergency/${id}`, data),
  remove: (id) => api.delete(`/emergency/${id}`)
}

// ── POLLS ─────────────────────────────────────────────────────
export const pollsAPI = {
  getAll: () => api.get('/polls/'),
  create: (data) => api.post('/polls/', data),
  get: (id) => api.get(`/polls/${id}`),
  vote: (id, data) => api.post(`/polls/${id}/vote`, data),
  close: (id) => api.put(`/polls/${id}/close`),
  delete: (id) => api.delete(`/polls/${id}`)
}

// ── MAINTENANCE ───────────────────────────────────────────────
export const maintenanceAPI = {
  getAll: () => api.get('/maintenance/'),
  add: (data) => api.post('/maintenance/', data),
  complete: (id) => api.put(`/maintenance/${id}/complete`),
  update: (id, data) => api.put(`/maintenance/${id}`, data),
  delete: (id) => api.delete(`/maintenance/${id}`)
}

// ── EQUIPMENT (Smart Maintenance Predictor) ───────────────────
export const equipmentAPI = {
  getAll: () => api.get('/equipment/'),
  add: (data) => api.post('/equipment/', data),
  markServiced: (id, data) => api.put(`/equipment/${id}/service`, data),
  forecast: () => api.get('/equipment/forecast'),
  history: (id) => api.get(`/equipment/${id}/history`),
  delete: (id) => api.delete(`/equipment/${id}`)
}

// ── HEALTH SCORE ──────────────────────────────────────────────
export const healthAPI = {
  calculate: (month, year) => api.get(`/health/calculate?month=${month}&year=${year}`),
  history: () => api.get('/health/history')
}

// ── CONFLICTS (Neighbour Conflict Resolver) ───────────────────
export const conflictsAPI = {
  getAll: () => api.get('/conflicts/'),
  raise: (data) => api.post('/conflicts/', data),
  respond: (id, data) => api.put(`/conflicts/${id}/respond`, data),
  resolve: (id, data) => api.put(`/conflicts/${id}/resolve`, data),
  getPending: () => api.get('/conflicts/pending')
}

// ── PARKING ───────────────────────────────────────────────────
export const parkingAPI = {
  getAll: () => api.get('/parking/'),
  getAvailable: () => api.get('/parking/available'),
  add: (data) => api.post('/parking/', data),
  reserve: (id, data) => api.put(`/parking/${id}/reserve`, data),
  occupy: (id, data) => api.put(`/parking/${id}/occupy`, data),
  release: (id) => api.put(`/parking/${id}/release`),
  delete: (id) => api.delete(`/parking/${id}`)
}

export default api
