/** A readable message from an error thrown by the generated API client. */
export function errorMessage(error: unknown): string {
  if (error && typeof error === 'object' && 'detail' in error) {
    const { detail } = error
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail) && detail.length > 0) {
      const [first] = detail as { loc?: (string | number)[]; msg?: string }[]
      const field = first.loc?.at(-1)
      const message = first.msg ?? 'is invalid'
      return typeof field === 'string' ? `${field.replaceAll('_', ' ')}: ${message}` : message
    }
  }
  return 'Something went wrong. Please try again.'
}
