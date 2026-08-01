/**
 * Small display helpers shared by the pages.
 * Purely defensive — none of these change the visual design.
 */

/**
 * Badge CSS class for a status/priority value.
 * Pages used to call `status.toLowerCase()` directly in the template; a single
 * null value threw during render, which unmounts the whole route (blank page).
 */
export function badgeClass(value, prefix = 'badge') {
  if (value === null || value === undefined || value === '') return `${prefix}-low`
  return `${prefix}-${String(value).toLowerCase().replace(/_/g, '-')}`
}

/** Safe label for a possibly-missing enum value. */
export function label(value, fallback = '—') {
  return value === null || value === undefined || value === '' ? fallback : String(value)
}

/** Numeric coercion so a missing amount renders 0 instead of NaN. */
export function num(value) {
  const n = Number(value)
  return Number.isFinite(n) ? n : 0
}

/** Money for display, e.g. 1234.5 -> "1,234.50". */
export function money(value) {
  return num(value).toLocaleString('en-IN', {
    minimumFractionDigits: 2, maximumFractionDigits: 2,
  })
}

/** Blank string -> null, so optional fields aren't sent as "" to typed columns. */
export function orNull(value) {
  if (value === null || value === undefined) return null
  if (typeof value === 'string' && value.trim() === '') return null
  return value
}

/** Strip blank strings from a payload object (returns a new object). */
export function clean(payload) {
  const out = {}
  for (const [k, v] of Object.entries(payload)) out[k] = orNull(v)
  return out
}

/**
 * Emergency-contact service types.
 * Single source of truth for the frontend — imported by both EmergencyPage and
 * the ResidentDashboard quick-dial card so the icon/colour map is not duplicated.
 * Must stay in step with ENUMS["service_type"] in Backend/utils.py.
 */
export const SERVICE_TYPES = [
  'PLUMBER', 'ELECTRICIAN', 'SECURITY', 'FIRE',
  'AMBULANCE', 'POLICE', 'LIFT', 'WATER', 'OTHER',
]

const SERVICE_META = {
  PLUMBER:     { icon: 'fa-faucet',            badge: 'badge-open',    label: 'Plumber' },
  ELECTRICIAN: { icon: 'fa-bolt',              badge: 'badge-medium',  label: 'Electrician' },
  SECURITY:    { icon: 'fa-shield-halved',     badge: 'badge-progress',label: 'Security' },
  FIRE:        { icon: 'fa-fire-extinguisher', badge: 'badge-urgent',  label: 'Fire' },
  AMBULANCE:   { icon: 'fa-truck-medical',     badge: 'badge-urgent',  label: 'Ambulance' },
  POLICE:      { icon: 'fa-building-shield',   badge: 'badge-urgent',  label: 'Police' },
  LIFT:        { icon: 'fa-elevator',          badge: 'badge-low',     label: 'Lift / Elevator' },
  WATER:       { icon: 'fa-droplet',           badge: 'badge-open',    label: 'Water Supply' },
  OTHER:       { icon: 'fa-circle-info',       badge: 'badge-low',     label: 'Other' },
}

/** Icon + badge class + friendly label for a service type. Null-safe. */
export function serviceMeta(type) {
  return SERVICE_META[type] || { icon: 'fa-circle-info', badge: 'badge-low', label: label(type) }
}

/**
 * Build a dialable href. Strips spaces/dashes/brackets so `tel:` works on
 * mobile, and returns null for a missing number so we never emit `tel:null`.
 */
export function telHref(phone) {
  if (!phone) return null
  const cleaned = String(phone).replace(/[^\d+]/g, '')
  return cleaned ? `tel:${cleaned}` : null
}

/** Today's date as YYYY-MM-DD, for date inputs and defaults. */
export function today() {
  const d = new Date()
  const pad = n => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}
