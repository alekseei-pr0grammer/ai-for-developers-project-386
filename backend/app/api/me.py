from fastapi import APIRouter
from pydantic import BaseModel

from app.auth import CurrentHost

router = APIRouter(prefix="/me", tags=["me"])


class HostResponse(BaseModel):
    email: str
    public_name: str
    handle: str
    time_zone: str


@router.get("")
def get_me(host: CurrentHost) -> HostResponse:
    """The logged-in Host."""
    return HostResponse.model_validate(host, from_attributes=True)
