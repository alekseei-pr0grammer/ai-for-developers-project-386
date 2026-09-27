import { useMutation, useQueryClient } from '@tanstack/react-query'
import type { FormEvent } from 'react'
import { Link, useNavigate } from 'react-router'
import { getMeQueryKey, signUpMutation } from '@/api/generated/@tanstack/react-query.gen'
import { AuthCard } from '@/components/auth-card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { NativeSelect, NativeSelectOption } from '@/components/ui/native-select'
import { errorMessage } from '@/lib/api-errors'
import { browserTimeZone, timeZones } from '@/lib/time-zones'

export function SignUpPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const signUp = useMutation({
    ...signUpMutation(),
    onSuccess: (host) => {
      queryClient.setQueryData(getMeQueryKey(), host)
      navigate('/dashboard')
    },
  })

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    signUp.mutate({
      body: {
        public_name: String(form.get('public_name')),
        email: String(form.get('email')),
        password: String(form.get('password')),
        time_zone: String(form.get('time_zone')),
      },
    })
  }

  return (
    <AuthCard
      title="Create your calendar"
      description="Guests will see your public name when they book time with you."
      footer={
        <span>
          Already have an account?{' '}
          <Link to="/login" className="text-foreground underline">
            Log in
          </Link>
        </span>
      }
    >
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        {signUp.isError && (
          <Alert variant="destructive">
            <AlertDescription>{errorMessage(signUp.error)}</AlertDescription>
          </Alert>
        )}
        <div className="flex flex-col gap-2">
          <Label htmlFor="public_name">Public name</Label>
          <Input id="public_name" name="public_name" required maxLength={100} placeholder="Alex Alekseev" />
        </div>
        <div className="flex flex-col gap-2">
          <Label htmlFor="email">Email</Label>
          <Input id="email" name="email" type="email" required autoComplete="email" />
        </div>
        <div className="flex flex-col gap-2">
          <Label htmlFor="password">Password</Label>
          <Input id="password" name="password" type="password" required minLength={8} autoComplete="new-password" />
        </div>
        <div className="flex flex-col gap-2">
          <Label htmlFor="time_zone">Time zone</Label>
          <NativeSelect id="time_zone" name="time_zone" defaultValue={browserTimeZone} className="w-full">
            {timeZones.map((zone) => (
              <NativeSelectOption key={zone} value={zone}>
                {zone}
              </NativeSelectOption>
            ))}
          </NativeSelect>
        </div>
        <Button type="submit" disabled={signUp.isPending}>
          {signUp.isPending ? 'Creating…' : 'Sign up'}
        </Button>
      </form>
    </AuthCard>
  )
}
