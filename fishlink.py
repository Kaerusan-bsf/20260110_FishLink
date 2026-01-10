from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


DELIVERY_RATE = 2.5


class RequestStatus(str, Enum):
    REQUESTED = "Requested"
    ACCEPTED = "Accepted"
    PREPARING = "Preparing"
    READY = "Ready"
    COMPLETED = "Completed"


_ALLOWED_TRANSITIONS = {
    RequestStatus.REQUESTED: {RequestStatus.ACCEPTED},
    RequestStatus.ACCEPTED: {RequestStatus.PREPARING},
    RequestStatus.PREPARING: {RequestStatus.READY},
    RequestStatus.READY: {RequestStatus.COMPLETED},
    RequestStatus.COMPLETED: set(),
}


@dataclass(frozen=True)
class FarmerListing:
    listing_id: str
    farmer_name: str
    location: str


@dataclass
class Request:
    request_id: str
    listing: FarmerListing
    distance_km: float
    status: RequestStatus = field(default=RequestStatus.REQUESTED)

    def __post_init__(self) -> None:
        if self.listing is None:
            raise ValueError("listing must be provided")
        if self.distance_km < 0:
            raise ValueError("distance_km must be non-negative")

    @property
    def estimated_delivery_fee(self) -> float:
        return self.distance_km * DELIVERY_RATE

    def transition_to(self, next_status: RequestStatus) -> None:
        allowed = _ALLOWED_TRANSITIONS[self.status]
        if next_status not in allowed:
            raise ValueError(
                f"invalid status transition: {self.status.value} -> {next_status.value}"
            )
        self.status = next_status
