import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Check, Copy } from 'lucide-react'
import { useState } from 'react'
import { useNavigate } from 'react-router'
import { logOutMutation } from '@/api/generated/@tanstack/react-query.gen'
import { EventTypesCard } from '@/components/event-types-card'
import { ProfileCard } from '@/components/profile-card'
import { ScheduleCard } from '@/components/schedule-card'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useCurrentHost } from '@/hooks/use-current-host'

export function DashboardPage() {
  // RequireHost has already loaded the Host.
  const host = useCurrentHost().data!
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const logOut = useMutation({
    ...logOutMutation(),
    onSuccess: () => {
      queryClient.clear()
      navigate('/')
    },
  })

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">{host.public_name}</h1>
          <p className="text-sm text-muted-foreground">
            {host.email} · {host.time_zone}
          </p>
        </div>
        <Button variant="outline" onClick={() => logOut.mutate({})} disabled={logOut.isPending}>
          Log out
        </Button>
      </div>
      <PublicLinkCard handle={host.handle} />
      <EventTypesCard />
      <ScheduleCard timeZone={host.time_zone} />
      <ProfileCard host={host} />
    </div>
  )
}

function PublicLinkCard({ handle }: { handle: string }) {
  const link = `${window.location.origin}/${handle}`
  const [copied, setCopied] = useState(false)

  async function copy() {
    await navigator.clipboard.writeText(link)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Your public link</CardTitle>
        <CardDescription>Share it so Guests can book time with you. It never changes.</CardDescription>
      </CardHeader>
      <CardContent className="flex items-center gap-2">
        <code className="flex-1 truncate rounded-md bg-muted px-3 py-2 text-sm">{link}</code>
        <Button variant="outline" size="icon" onClick={copy} aria-label="Copy link">
          {copied ? <Check /> : <Copy />}
        </Button>
      </CardContent>
    </Card>
  )
}
