import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Plus, X } from 'lucide-react'
import { useState } from 'react'
import {
  getMyScheduleOptions,
  getMyScheduleQueryKey,
  replaceMyScheduleMutation,
} from '@/api/generated/@tanstack/react-query.gen'
import type { ScheduleIntervalModel } from '@/api/generated'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { errorMessage } from '@/lib/api-errors'

const WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

export function ScheduleCard({ timeZone }: { timeZone: string }) {
  const schedule = useQuery(getMyScheduleOptions())

  return (
    <Card>
      <CardHeader>
        <CardTitle>Weekly Schedule</CardTitle>
        <CardDescription>
          When you accept Bookings, in your time zone ({timeZone}). Days without hours are days off.
        </CardDescription>
      </CardHeader>
      {schedule.data ? (
        // Keyed by the saved data so the editor resets to it after a save.
        <ScheduleEditor key={JSON.stringify(schedule.data)} saved={schedule.data.intervals} />
      ) : (
        <CardContent className="text-sm text-muted-foreground">Loading…</CardContent>
      )}
    </Card>
  )
}

/** "09:00:00" -> "09:00", the format of <input type="time">. */
const toInputTime = (value: string) => value.slice(0, 5)

function ScheduleEditor({ saved }: { saved: ScheduleIntervalModel[] }) {
  const queryClient = useQueryClient()
  const [intervals, setIntervals] = useState(() =>
    saved.map((i) => ({ ...i, start: toInputTime(i.start), end: toInputTime(i.end) })),
  )
  const save = useMutation({
    ...replaceMyScheduleMutation(),
    onSuccess: (data) => queryClient.setQueryData(getMyScheduleQueryKey(), data),
  })

  const update = (index: number, change: Partial<ScheduleIntervalModel>) =>
    setIntervals((current) => current.map((interval, i) => (i === index ? { ...interval, ...change } : interval)))
  const remove = (index: number) => setIntervals((current) => current.filter((_, i) => i !== index))
  const add = (weekday: number) =>
    setIntervals((current) => [...current, { weekday, start: '09:00', end: '17:00' }])

  return (
    <>
      <CardContent className="flex flex-col divide-y">
        {WEEKDAYS.map((name, weekday) => {
          const day = intervals.map((interval, index) => ({ interval, index })).filter(({ interval }) => interval.weekday === weekday)
          return (
            <div key={name} className="flex flex-wrap items-start gap-3 py-3 first:pt-0 last:pb-0">
              <span className="w-24 pt-1.5 text-sm font-medium">{name}</span>
              <div className="flex flex-1 flex-col gap-2">
                {day.length === 0 && <span className="pt-1.5 text-sm text-muted-foreground">Day off</span>}
                {day.map(({ interval, index }) => (
                  <div key={index} className="flex items-center gap-2">
                    <Input
                      type="time"
                      aria-label={`${name} start`}
                      className="w-32"
                      value={interval.start}
                      onChange={(event) => update(index, { start: event.target.value })}
                    />
                    <span className="text-muted-foreground">–</span>
                    <Input
                      type="time"
                      aria-label={`${name} end`}
                      className="w-32"
                      value={interval.end}
                      onChange={(event) => update(index, { end: event.target.value })}
                    />
                    <Button variant="ghost" size="icon" aria-label="Remove hours" onClick={() => remove(index)}>
                      <X />
                    </Button>
                  </div>
                ))}
              </div>
              <Button variant="ghost" size="sm" onClick={() => add(weekday)}>
                <Plus /> Add hours
              </Button>
            </div>
          )
        })}
      </CardContent>
      <CardFooter className="flex flex-col items-stretch gap-3">
        {save.isError && (
          <Alert variant="destructive">
            <AlertDescription>{errorMessage(save.error)}</AlertDescription>
          </Alert>
        )}
        <Button className="self-end" disabled={save.isPending} onClick={() => save.mutate({ body: { intervals } })}>
          Save schedule
        </Button>
      </CardFooter>
    </>
  )
}
