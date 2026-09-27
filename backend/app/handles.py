"""Handle derivation: a Host's permanent public identifier (ADR 0001)."""

import re

from anyascii import anyascii
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import Host

MAX_LENGTH = 50
# First path segments the web app uses for its own pages; public links are /{handle}.
RESERVED = frozenset({"api", "assets", "dashboard", "login", "logout", "signup"})


def slugify(public_name: str) -> str:
    """'Alex Alekseev' -> 'alex-alekseev'; non-Latin scripts are transliterated."""
    slug = re.sub(r"[^a-z0-9]+", "-", anyascii(public_name).lower()).strip("-")
    return slug[:MAX_LENGTH].rstrip("-") or "host"


def derive_handle(db: Session, public_name: str) -> str:
    """The slug of the Public name, with the smallest numeric suffix that makes it free."""
    base = slugify(public_name)
    taken = (
        set(
            db.scalars(
                select(Host.handle).where(or_(Host.handle == base, Host.handle.like(f"{base}-%")))
            )
        )
        | RESERVED
    )
    if base not in taken:
        return base
    suffix = 2
    while f"{base}-{suffix}" in taken:
        suffix += 1
    return f"{base}-{suffix}"
