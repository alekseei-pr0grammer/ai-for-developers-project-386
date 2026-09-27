import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Plus } from 'lucide-react'
import { type FormEvent, useState } from 'react'
import {
  createEventTypeMutation,
  listMyEventTypesOptions,
  listMyEventTypesQueryKey,
  updateEventTypeMutation,
} from '@/api/generated/@tanstack/react-query.gen'
import type { EventTypeResponse } from '@/api/generated'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardAction, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { errorMessage } from '@/lib/api-errors'

export function EventTypesCard() {
  const eventTypes = useQuery(listMyEventTypesOptions())
  // null = closed, 'new' = creating, otherwise the Event Type being edited.
  const [editing, setEditing] = useState<EventTypeResponse | 'new' | null>(null)

  return (
    <Card>
      <CardHeader>
        <CardTitle>Event Types</CardTitle>
        <CardDescription>The kinds of meetings Guests can book with you.</CardDescription>
        <CardAction>
          <Button size="sm" onClick={() => setEditing('new')}>
            <Plus /> New
          </Button>
        </CardAction>
      </CardHeader>
      <CardContent className="flex flex-col gap-2">
        {eventTypes.isPending && <p className="text-sm text-muted-foreground">Loading…</p>}
        {eventTypes.data?.length === 0 && (
          <p className="text-sm text-muted-foreground">No Event Types yet. Create one to start taking Bookings.</p>
        )}
        {eventTypes.data?.map((eventType) => (
          <EventTypeRow key={eventType.id} eventType={eventType} onEdit={() => setEditing(eventType)} />
        ))}
      </CardContent>
      {editing !== null && (
        <EventTypeDialog
          eventType={editing === 'new' ? undefined : editing}
          onClose={() => setEditing(null)}
        />
      )}
    </Card>
  )
}

function EventTypeRow({ eventType, onEdit }: { eventType: EventTypeResponse; onEdit: () => void }) {
  const queryClient = useQueryClient()
  const update = useMutation({
    ...updateEventTypeMutation(),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: listMyEventTypesQueryKey() }),
  })

  return (
    <div className="flex items-center gap-3 rounded-lg border p-3">
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="truncate font-medium">{eventType.title}</span>
          <Badge variant="secondary">{eventType.duration_minutes} min</Badge>
          {eventType.archived && <Badge variant="outline">Archived</Badge>}
        </div>
        {eventType.description && (
          <p className="truncate text-sm text-muted-foreground">{eventType.description}</p>
        )}
      </div>
      <Button variant="ghost" size="sm" onClick={onEdit}>
        Edit
      </Button>
      <Button
        variant="outline"
        size="sm"
        disabled={update.isPending}
        onClick={() =>
          update.mutate({ path: { event_type_id: eventType.id }, body: { archived: !eventType.archived } })
        }
      >
        {eventType.archived ? 'Restore' : 'Archive'}
      </Button>
    </div>
  )
}

function EventTypeDialog({ eventType, onClose }: { eventType?: EventTypeResponse; onClose: () => void }) {
  const queryClient = useQueryClient()
  const onSuccess = () => {
    queryClient.invalidateQueries({ queryKey: listMyEventTypesQueryKey() })
    onClose()
  }
  const create = useMutation({ ...createEventTypeMutation(), onSuccess })
  const update = useMutation({ ...updateEventTypeMutation(), onSuccess })
  const mutation = eventType ? update : create

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    const body = {
      title: String(form.get('title')),
      description: String(form.get('description')),
      duration_minutes: Number(form.get('duration_minutes')),
    }
    if (eventType) update.mutate({ path: { event_type_id: eventType.id }, body })
    else create.mutate({ body })
  }

  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{eventType ? 'Edit Event Type' : 'New Event Type'}</DialogTitle>
          <DialogDescription>
            {eventType
              ? 'Changing the duration only affects new Bookings.'
              : 'Guests pick a start time; the meeting lasts this long.'}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          {mutation.isError && (
            <Alert variant="destructive">
              <AlertDescription>{errorMessage(mutation.error)}</AlertDescription>
            </Alert>
          )}
          <div className="flex flex-col gap-2">
            <Label htmlFor="title">Title</Label>
            <Input id="title" name="title" required maxLength={100} defaultValue={eventType?.title} />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="description">Description</Label>
            <Textarea id="description" name="description" maxLength={2000} defaultValue={eventType?.description} />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="duration_minutes">Duration (minutes)</Label>
            <Input
              id="duration_minutes"
              name="duration_minutes"
              type="number"
              required
              min={1}
              max={720}
              defaultValue={eventType?.duration_minutes ?? 30}
            />
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={mutation.isPending}>
              Save
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
