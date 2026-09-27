# Import every model module here so Alembic autogenerate can see it.
from app.models.event_type import EventType  # noqa: F401
from app.models.host import Host, HostSession  # noqa: F401
from app.models.schedule import ScheduleInterval  # noqa: F401
