import { useMutation, useQueryClient } from '@tanstack/react-query'
import type { FormEvent } from 'react'
import { getMeQueryKey, updateMeMutation } from '@/api/generated/@tanstack/react-query.gen'
import type { HostResponse } from '@/api/generated'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { NativeSelect, NativeSelectOption } from '@/components/ui/native-select'
import { errorMessage } from '@/lib/api-errors'
import { timeZones } from '@/lib/time-zones'

export function ProfileCard({ host }: { host: HostResponse }) {
  const queryClient = useQueryClient()
  const updateMe = useMutation({
    ...updateMeMutation(),
    onSuccess: (updated) => queryClient.setQueryData(getMeQueryKey(), updated),
  })

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    updateMe.mutate({
      body: { public_name: String(form.get('public_name')), time_zone: String(form.get('time_zone')) },
    })
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Profile</CardTitle>
        <CardDescription>
          Guests see your public name. Your public link stays the same when you change it.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="grid gap-4 sm:grid-cols-[1fr_1fr_auto] sm:items-end">
          <div className="flex flex-col gap-2">
            <Label htmlFor="profile_public_name">Public name</Label>
            <Input
              id="profile_public_name"
              name="public_name"
              required
              maxLength={100}
              defaultValue={host.public_name}
            />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="profile_time_zone">Time zone</Label>
            <NativeSelect
              id="profile_time_zone"
              name="time_zone"
              defaultValue={host.time_zone}
              className="w-full"
            >
              {timeZones.map((zone) => (
                <NativeSelectOption key={zone} value={zone}>
                  {zone}
                </NativeSelectOption>
              ))}
            </NativeSelect>
          </div>
          <Button type="submit" disabled={updateMe.isPending}>
            {updateMe.isSuccess && !updateMe.isPending ? 'Saved' : 'Save'}
          </Button>
          {updateMe.isError && (
            <Alert variant="destructive" className="sm:col-span-3">
              <AlertDescription>{errorMessage(updateMe.error)}</AlertDescription>
            </Alert>
          )}
        </form>
      </CardContent>
    </Card>
  )
}
