import { Link } from 'react-router'
import { Button } from '@/components/ui/button'

export function NotFoundPage() {
  return (
    <section className="flex flex-col items-start gap-4 py-12">
      <h1 className="text-2xl font-semibold">Page not found</h1>
      <p className="text-muted-foreground">The link may be wrong, or the page no longer exists.</p>
      <Button asChild variant="outline">
        <Link to="/">Go to the home page</Link>
      </Button>
    </section>
  )
}
