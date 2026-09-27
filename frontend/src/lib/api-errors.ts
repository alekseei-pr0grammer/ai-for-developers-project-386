/** A readable message from an error thrown by the generated API client. */
export function errorMessage(error: unknown): string {
  if (error && typeof error === 'object' && 'detail' in error) {
    const { detail } = error
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail) && detail.length > 0) {
      const [first] = detail as { loc?: (string | number)[]; msg?: string }[]
      const field = first.loc?.at(-1)
      // Pydantic prefixes errors raised by our own validators with "Value error, ".
      const message = (first.msg ?? 'is invalid').replace(/^Value error, /, '')
      // loc ends in "body" for errors about the request as a whole.
      return typeof field === 'string' && field !== 'body'
        ? `${field.replaceAll('_', ' ')}: ${message}`
        : message
    }
  }
  return 'Something went wrong. Please try again.'
}
