import { useMutation } from '@tanstack/react-query'
import type { FormEvent } from 'react'
import { createBookingMutation } from '@/api/generated/@tanstack/react-query.gen'
import type { BookingConfirmation } from '@/api/generated'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
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
import { formatDate, formatTime } from '@/lib/dates'

export function GuestFormDialog({
  handle,
  eventTypeId,
  slot,
  onBooked,
  onFailed,
  onClose,
}: {
  handle: string
  eventTypeId: number
  slot: Date
  onBooked: (booking: BookingConfirmation) => void
  /** The time may have been taken meanwhile: the caller refreshes the Slots. */
  onFailed: () => void
  onClose: () => void
}) {
  const createBooking = useMutation({ ...createBookingMutation(), onSuccess: onBooked, onError: onFailed })

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    createBooking.mutate({
      path: { handle, event_type_id: eventTypeId },
      body: {
        start: slot.toISOString(),
        guest_name: String(form.get('guest_name')),
        guest_email: String(form.get('guest_email')),
        guest_note: String(form.get('guest_note')),
      },
    })
  }

  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Your details</DialogTitle>
          <DialogDescription>
            {formatDate(slot)}, {formatTime(slot)}. No account needed.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          {createBooking.isError && (
            <Alert variant="destructive">
              <AlertDescription>{errorMessage(createBooking.error)}</AlertDescription>
            </Alert>
          )}
          <div className="flex flex-col gap-2">
            <Label htmlFor="guest_name">Name</Label>
            <Input id="guest_name" name="guest_name" required maxLength={100} autoComplete="name" />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="guest_email">Email</Label>
            <Input id="guest_email" name="guest_email" type="email" required autoComplete="email" />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="guest_note">Note (optional)</Label>
            <Textarea
              id="guest_note"
              name="guest_note"
              maxLength={2000}
              placeholder="What would you like to talk about?"
            />
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose}>
              Back
            </Button>
            <Button type="submit" disabled={createBooking.isPending}>
              {createBooking.isPending ? 'Booking…' : 'Confirm Booking'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
