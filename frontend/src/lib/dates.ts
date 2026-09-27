/** Local calendar date of an instant in the browser's time zone, as "YYYY-MM-DD". */
export const localDateKey = (date: Date) =>
  `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`

/** Time of day, in `timeZone` (default: the browser's). */
export const formatTime = (date: Date, timeZone?: string) =>
  date.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit', timeZone })

/** Full date, in `timeZone` (default: the browser's). */
export const formatDate = (date: Date, timeZone?: string) =>
  date.toLocaleDateString(undefined, { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric', timeZone })

/** Short date and time, in `timeZone` (default: the browser's). */
export const formatDateTime = (date: Date, timeZone?: string) =>
  date.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short', timeZone })
