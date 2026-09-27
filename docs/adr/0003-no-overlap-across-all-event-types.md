# A Host's Bookings never overlap, across all Event Types, enforced by the database

A Host has one Weekly Schedule and one person's time, so an active Booking blocks that time for all of the Host's Event Types, not only the one that was booked. The rule is enforced by a database constraint, not only in Python, so concurrent requests for the same Slot can't both succeed. Cancelled Bookings don't count, which frees their time again.

## Consequences

- Only Bookings where a person is the Host block their time. When a Host books another Host, the Booking does not block time in their own calendar.
