import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  cancelBookingMutation,
  listMyBookingsOptions,
  listMyBookingsQueryKey,
} from '@/api/generated/@tanstack/react-query.gen'
import type { HostBooking } from '@/api/generated'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { formatDate, formatDateTime, formatTime } from '@/lib/dates'

type Scope = 'upcoming' | 'past'

export function BookingsCard({ timeZone }: { timeZone: string }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Bookings</CardTitle>
        <CardDescription>Times are in your time zone ({timeZone}).</CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="upcoming">
          <TabsList>
            <TabsTrigger value="upcoming">Upcoming</TabsTrigger>
            <TabsTrigger value="past">Past and cancelled</TabsTrigger>
          </TabsList>
          <TabsContent value="upcoming">
            <BookingList scope="upcoming" timeZone={timeZone} />
          </TabsContent>
          <TabsContent value="past">
            <BookingList scope="past" timeZone={timeZone} />
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  )
}

function BookingList({ scope, timeZone }: { scope: Scope; timeZone: string }) {
  const bookings = useQuery(listMyBookingsOptions({ query: { scope } }))

  if (bookings.isPending) return <p className="py-2 text-sm text-muted-foreground">Loading…</p>
  if (bookings.data?.length === 0) {
    return (
      <p className="py-2 text-sm text-muted-foreground">
        {scope === 'upcoming' ? 'No upcoming Bookings.' : 'Nothing here yet.'}
      </p>
    )
  }
  return (
    <div className="flex flex-col gap-2 pt-2">
      {bookings.data?.map((booking) => (
        <BookingRow key={booking.id} booking={booking} timeZone={timeZone} />
      ))}
    </div>
  )
}

function BookingRow({ booking, timeZone }: { booking: HostBooking; timeZone: string }) {
  const queryClient = useQueryClient()
  const cancel = useMutation({
    ...cancelBookingMutation(),
    // Both lists change: the Booking moves from upcoming to past.
    onSuccess: () => {
      for (const scope of ['upcoming', 'past'] as const) {
        queryClient.invalidateQueries({ queryKey: listMyBookingsQueryKey({ query: { scope } }) })
      }
    },
  })
  const start = new Date(booking.start)
  const end = new Date(booking.end)

  return (
    <div className="flex flex-wrap items-start gap-3 rounded-lg border p-3">
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-medium">
            {formatDate(start, timeZone)}, {formatTime(start, timeZone)}–{formatTime(end, timeZone)}
          </span>
          {booking.status === 'cancelled' && <Badge variant="destructive">Cancelled</Badge>}
        </div>
        <p className="text-sm">
          {booking.event_type_title} · {booking.guest_name} ·{' '}
          <a href={`mailto:${booking.guest_email}`} className="underline">
            {booking.guest_email}
          </a>
        </p>
        {booking.guest_note && (
          <p className="whitespace-pre-line text-sm text-muted-foreground">{booking.guest_note}</p>
        )}
        <p className="text-xs text-muted-foreground">
          Booked {formatDateTime(new Date(booking.created_at), timeZone)}
          {booking.cancelled_at && `, cancelled ${formatDateTime(new Date(booking.cancelled_at), timeZone)}`}
        </p>
      </div>
      {booking.status === 'active' && new Date() < end && (
        <AlertDialog>
          <AlertDialogTrigger asChild>
            <Button variant="outline" size="sm" disabled={cancel.isPending}>
              Cancel
            </Button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Cancel this Booking?</AlertDialogTitle>
              <AlertDialogDescription>
                {booking.guest_name}'s {booking.event_type_title} on {formatDate(start, timeZone)} at{' '}
                {formatTime(start, timeZone)}. The time becomes bookable again. Let {booking.guest_name} know
                yourself: they are not notified.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Keep it</AlertDialogCancel>
              <AlertDialogAction onClick={() => cancel.mutate({ path: { booking_id: booking.id } })}>
                Cancel Booking
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      )}
    </div>
  )
}
