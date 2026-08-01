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

/** Today's date as YYYY-MM-DD, for date inputs and defaults. */
export function today() {
  const d = new Date()
  const pad = n => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}
