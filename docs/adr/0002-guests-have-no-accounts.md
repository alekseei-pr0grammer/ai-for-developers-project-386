# Guests have no accounts

A Guest is not a stored entity: it is just the name, email and optional note given on a Booking. Anyone can book a Host's time without signing up, which is the core promise of the product. A Host booking another Host acts as a Guest too, with no link to their own account.

## Consequences

- There is no "my bookings" view for Guests, and two Bookings from the same email are not known to be the same person.
- Adding Guest accounts later would need a data migration to group existing Bookings by person.
