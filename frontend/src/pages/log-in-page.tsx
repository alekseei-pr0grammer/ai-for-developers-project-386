import { useMutation, useQueryClient } from '@tanstack/react-query'
import type { FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router'
import { getMeQueryKey, logInMutation } from '@/api/generated/@tanstack/react-query.gen'
import { AuthCard } from '@/components/auth-card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { errorMessage } from '@/lib/api-errors'

export function LogInPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const queryClient = useQueryClient()
  // RequireHost sends Hosts here with the page they wanted; go back there after logging in.
  const from = (location.state as { from?: string } | null)?.from ?? '/dashboard'
  const logIn = useMutation({
    ...logInMutation(),
    onSuccess: (host) => {
      queryClient.setQueryData(getMeQueryKey(), host)
      navigate(from, { replace: true })
    },
  })

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    logIn.mutate({ body: { email: String(form.get('email')), password: String(form.get('password')) } })
  }

  return (
    <AuthCard
      title="Log in"
      description="Manage your Event Types, hours and Bookings."
      footer={
        <span>
          New here?{' '}
          <Link to="/signup" className="text-foreground underline">
            Create an account
          </Link>
        </span>
      }
    >
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        {logIn.isError && (
          <Alert variant="destructive">
            <AlertDescription>{errorMessage(logIn.error)}</AlertDescription>
          </Alert>
        )}
        <div className="flex flex-col gap-2">
          <Label htmlFor="email">Email</Label>
          <Input id="email" name="email" type="email" required autoComplete="email" />
        </div>
        <div className="flex flex-col gap-2">
          <Label htmlFor="password">Password</Label>
          <Input id="password" name="password" type="password" required autoComplete="current-password" />
        </div>
        <Button type="submit" disabled={logIn.isPending}>
          {logIn.isPending ? 'Logging in…' : 'Log in'}
        </Button>
      </form>
    </AuthCard>
  )
}
