import { Navigate, Outlet, useLocation } from 'react-router'
import { useCurrentHost } from '@/hooks/use-current-host'

/** Route guard: renders the child route for a logged-in Host, else sends them to log in. */
export function RequireHost() {
  const host = useCurrentHost()
  const location = useLocation()

  if (host.isPending) return <p className="text-muted-foreground">Loading…</p>
  if (host.isError) return <Navigate to="/login" replace state={{ from: location.pathname }} />
  return <Outlet />
}
