/** The browser's IANA time zone, e.g. "Europe/London". */
export const browserTimeZone = Intl.DateTimeFormat().resolvedOptions().timeZone

/** All IANA time zones the browser knows, always including the browser's own. */
export const timeZones = [...new Set([...Intl.supportedValuesOf('timeZone'), browserTimeZone, 'UTC'])].sort()
