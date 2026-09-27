import { useQuery } from '@tanstack/react-query'
import { getMeOptions } from '@/api/generated/@tanstack/react-query.gen'

/** The logged-in Host; errors (401) when there is no session. */
export function useCurrentHost() {
  // No retries: a 401 means "not logged in", not a transient failure.
  return useQuery({ ...getMeOptions(), retry: false })
}
