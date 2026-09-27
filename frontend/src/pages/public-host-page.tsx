import { useQuery } from '@tanstack/react-query'
import { Clock } from 'lucide-react'
import { Link, useParams } from 'react-router'
import { getPublicHostOptions } from '@/api/generated/@tanstack/react-query.gen'
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { NotFoundPage } from '@/pages/not-found-page'

export function PublicHostPage() {
  const { handle = '' } = useParams()
  const host = useQuery({ ...getPublicHostOptions({ path: { handle } }), retry: false })

  if (host.isPending) return <p className="text-muted-foreground">Loading…</p>
  if (host.isError) return <NotFoundPage />

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold">{host.data.public_name}</h1>
        <p className="text-muted-foreground">Pick the kind of meeting you'd like to book.</p>
      </div>
      {host.data.event_types.length === 0 ? (
        <p className="text-muted-foreground">There is nothing to book here yet.</p>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {host.data.event_types.map((eventType) => (
            <Link key={eventType.id} to={`/${host.data.handle}/${eventType.id}`}>
              <Card className="h-full transition-colors hover:bg-muted/50">
                <CardHeader>
                  <CardTitle>{eventType.title}</CardTitle>
                  <CardDescription className="flex items-center gap-1">
                    <Clock className="size-4" /> {eventType.duration_minutes} min
                  </CardDescription>
                  {eventType.description && <p className="text-sm">{eventType.description}</p>}
                </CardHeader>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
