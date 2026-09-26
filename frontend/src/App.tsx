import { useQuery } from '@tanstack/react-query'
import { getReadinessOptions } from '@/api/generated/@tanstack/react-query.gen'

function App() {
  // Typed end-to-end: `data` has the shape of FastAPI's ReadinessResponse.
  const readiness = useQuery(getReadinessOptions())

  return (
    <main className="mx-auto flex min-h-svh max-w-md flex-col justify-center gap-4 p-6">
      <h1 className="text-2xl font-semibold">Calendar</h1>
      <p>
        API status:{' '}
        {readiness.isPending ? 'checking…' : readiness.isError ? 'unavailable' : readiness.data.database}
      </p>
      <button
        type="button"
        className="rounded-md border px-4 py-2"
        onClick={() => readiness.refetch()}
      >
        Check again
      </button>
    </main>
  )
}

export default App
