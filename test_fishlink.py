import unittest

from fishlink import (
    DELIVERY_RATE,
    FarmerListing,
    Request,
    RequestStatus,
)


class RequestModelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.listing = FarmerListing(
            listing_id="listing-1",
            farmer_name="Aiko",
            location="Port Town",
        )

    def test_estimated_delivery_fee_uses_rate(self) -> None:
        request = Request(
            request_id="req-1",
            listing=self.listing,
            distance_km=12.0,
        )
        self.assertEqual(request.estimated_delivery_fee, 12.0 * DELIVERY_RATE)

    def test_status_flow(self) -> None:
        request = Request(
            request_id="req-2",
            listing=self.listing,
            distance_km=3.0,
        )
        request.transition_to(RequestStatus.ACCEPTED)
        request.transition_to(RequestStatus.PREPARING)
        request.transition_to(RequestStatus.READY)
        request.transition_to(RequestStatus.COMPLETED)
        self.assertEqual(request.status, RequestStatus.COMPLETED)

    def test_invalid_transition_raises(self) -> None:
        request = Request(
            request_id="req-3",
            listing=self.listing,
            distance_km=1.0,
        )
        with self.assertRaises(ValueError):
            request.transition_to(RequestStatus.READY)

    def test_listing_is_required(self) -> None:
        with self.assertRaises(ValueError):
            Request(
                request_id="req-4",
                listing=None,
                distance_km=2.0,
            )


if __name__ == "__main__":
    unittest.main()
