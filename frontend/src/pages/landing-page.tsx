import { Link } from 'react-router'
import { Button } from '@/components/ui/button'

export function LandingPage() {
  return (
    <section className="flex flex-col items-start gap-6 py-12">
      <h1 className="text-4xl font-bold tracking-tight">Calendar</h1>
      <p className="max-w-xl text-lg text-muted-foreground">
        Share one link and let people book time with you. Set your weekly hours, offer the
        kinds of meetings you want, and never get double-booked. Guests don't need an account.
      </p>
      <div className="flex gap-3">
        <Button asChild>
          <Link to="/signup">Get started</Link>
        </Button>
        <Button asChild variant="outline">
          <Link to="/login">Log in</Link>
        </Button>
      </div>
    </section>
  )
}
