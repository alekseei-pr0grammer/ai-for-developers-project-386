import { useQuery } from '@tanstack/react-query'
import { getReadinessOptions } from '@/api/generated/@tanstack/react-query.gen'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'

function App() {
  // Typed end-to-end: `data` has the shape of FastAPI's ReadinessResponse.
  const readiness = useQuery(getReadinessOptions())

  return (
    <main className="mx-auto flex min-h-svh max-w-md flex-col justify-center p-6">
      <Card>
        <CardHeader>
          <CardTitle>Calendar</CardTitle>
          <CardDescription>Frontend → FastAPI → Postgres</CardDescription>
        </CardHeader>
        <CardContent className="flex items-center gap-2">
          API status:
          {readiness.isPending ? (
            <Badge variant="secondary">checking…</Badge>
          ) : readiness.isError ? (
            <Badge variant="destructive">unavailable</Badge>
          ) : (
            <Badge>database {readiness.data.database}</Badge>
          )}
        </CardContent>
        <CardFooter>
          <Button variant="outline" onClick={() => readiness.refetch()} disabled={readiness.isFetching}>
            Check again
          </Button>
        </CardFooter>
      </Card>
    </main>
  )
}

export default App
