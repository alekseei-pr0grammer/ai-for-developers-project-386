# Calendar

A booking calendar where Hosts publish Event Types and Guests book time with them without an account.

## People

**Host**:
A person with an account who offers Event Types and receives Bookings. Every account is a Host.
_Avoid_: Owner, User, Organizer, Account

**Public name**:
The name Guests see for a Host, e.g. "Alex Alekseev" or "Acme Support". Given at sign-up and changeable at any time.
_Avoid_: Display name, Full name, Title

**Handle**:
The permanent, unique identifier of a Host in public links, derived from the Public name at sign-up. Never changes, even when the Public name does. Not used to log in; Hosts log in with their email.
_Avoid_: Username, Login, Slug

**Guest**:
A person who books time with a Host. Has no account: a Guest is just the name, email and optional note given on a Booking. A Host booking another Host acts as a Guest.
_Avoid_: Attendee, Client, Visitor, Customer

## Offering time

**Event Type**:
A kind of meeting a Host offers, with a title, description and fixed duration. Belongs to exactly one Host.
_Avoid_: Service, Meeting type, Template

**Weekly Schedule**:
The recurring weekly hours when a Host accepts Bookings, expressed in the Host's time zone.
_Avoid_: Working hours, Availability rules, Calendar

**Slot**:
A candidate start time offered to a Guest, derived from the Host's Weekly Schedule and existing Bookings. Never stored; becomes a Booking once chosen.
_Avoid_: Time slot, Opening, Availability

## Booking time

**Booking**:
A reservation of a Host's time by a Guest, for one Event Type, at a specific start time. A Host's active Bookings never overlap, across all of that Host's Event Types. Only Bookings where a person is the Host block their time.
_Avoid_: Appointment, Meeting, Reservation, Call

**Cancellation**:
The Host withdrawing a Booking. The Booking stays in history as cancelled and its time is free again.
_Avoid_: Deletion, Removal
