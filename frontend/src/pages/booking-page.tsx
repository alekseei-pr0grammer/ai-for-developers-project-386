import { useQuery } from '@tanstack/react-query'
import { Clock, Globe } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useParams } from 'react-router'
import { getPublicEventTypeOptions, listSlotsOptions } from '@/api/generated/@tanstack/react-query.gen'
import { Button } from '@/components/ui/button'
import { Calendar } from '@/components/ui/calendar'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { formatDate, formatTime, localDateKey } from '@/lib/dates'
import { browserTimeZone } from '@/lib/time-zones'
import { NotFoundPage } from '@/pages/not-found-page'

// The API clips to the Host's booking window; asking a bit further covers every time zone.
const RANGE_DAYS = 16

export function BookingPage() {
  const { handle = '', eventTypeId = '' } = useParams()
  const path = { handle, event_type_id: Number(eventTypeId) }
  const eventType = useQuery({ ...getPublicEventTypeOptions({ path }), retry: false })

  if (eventType.isPending) return <p className="text-muted-foreground">Loading…</p>
  if (eventType.isError) return <NotFoundPage />

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-semibold">Book a call</h1>
      <div className="grid gap-6 lg:grid-cols-[1fr_auto_1fr]">
        <Card>
          <CardHeader>
            <CardDescription>{eventType.data.host_public_name}</CardDescription>
            <CardTitle className="text-xl">{eventType.data.title}</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-3 text-sm">
            <span className="flex items-center gap-2 text-muted-foreground">
              <Clock className="size-4" /> {eventType.data.duration_minutes} min
            </span>
            <span className="flex items-center gap-2 text-muted-foreground">
              <Globe className="size-4" /> Times are in {browserTimeZone}
            </span>
            {eventType.data.description && <p className="whitespace-pre-line">{eventType.data.description}</p>}
          </CardContent>
        </Card>
        <SlotPicker handle={handle} eventTypeId={path.event_type_id} />
      </div>
    </div>
  )
}

function SlotPicker({ handle, eventTypeId }: { handle: string; eventTypeId: number }) {
  // Fixed at mount so the query key stays stable.
  const [range] = useState(() => {
    const from = new Date()
    const to = new Date(from.getTime() + RANGE_DAYS * 24 * 60 * 60 * 1000)
    return { from: from.toISOString(), to: to.toISOString() }
  })
  const slots = useQuery(listSlotsOptions({ path: { handle, event_type_id: eventTypeId }, query: range }))

  // Slots grouped by the Guest's local date.
  const byDay = useMemo(() => {
    const days = new Map<string, Date[]>()
    for (const value of slots.data?.slots ?? []) {
      const slot = new Date(value)
      const key = localDateKey(slot)
      days.set(key, [...(days.get(key) ?? []), slot])
    }
    return days
  }, [slots.data])

  const [selectedDay, setSelectedDay] = useState<Date | undefined>()
  const [selectedSlot, setSelectedSlot] = useState<Date | undefined>()
  const firstBookableDay = byDay.size > 0 ? new Date(byDay.values().next().value![0]) : undefined
  const day = selectedDay ?? firstBookableDay
  const daySlots = day ? (byDay.get(localDateKey(day)) ?? []) : []

  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle>Pick a day</CardTitle>
        </CardHeader>
        <CardContent>
          <Calendar
            mode="single"
            selected={day}
            onSelect={(date) => {
              setSelectedDay(date)
              setSelectedSlot(undefined)
            }}
            defaultMonth={firstBookableDay}
            disabled={(date) => !byDay.has(localDateKey(date))}
            weekStartsOn={1}
            className="[--cell-size:--spacing(10)]"
          />
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Pick a time</CardTitle>
          <CardDescription>{day ? formatDate(day) : 'No free times in the next two weeks.'}</CardDescription>
        </CardHeader>
        <CardContent className="flex max-h-[28rem] flex-col gap-2 overflow-y-auto">
          {slots.isPending && <p className="text-sm text-muted-foreground">Loading…</p>}
          {daySlots.map((slot) => (
            <Button
              key={slot.toISOString()}
              variant={slot.getTime() === selectedSlot?.getTime() ? 'default' : 'outline'}
              onClick={() => setSelectedSlot(slot)}
            >
              {formatTime(slot)}
            </Button>
          ))}
        </CardContent>
      </Card>
    </>
  )
}
