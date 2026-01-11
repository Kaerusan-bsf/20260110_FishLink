import os
import unittest

from db import init_db
from repo import (
    avg_rating_for_farm,
    create_farm,
    create_listing,
    create_request,
    create_review,
    get_review_by_request,
    get_farm,
    get_listing,
    get_request,
    get_restaurant,
    list_farms,
    list_listings,
    list_requests,
    update_request_status,
    upsert_restaurant,
)


class RepoTests(unittest.TestCase):
    def setUp(self):
        self.db_path = "fishlink_test.db"
        os.environ["FISHLINK_DB_PATH"] = self.db_path
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        init_db()

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.environ.pop("FISHLINK_DB_PATH", None)

    def test_restaurant_upsert_and_get(self):
        restaurant_id = upsert_restaurant(
            "Harbor Bistro",
            "Downtown",
            35.0,
            139.0,
            "https://maps.example/restaurant",
            "contact@harbor.test",
        )
        self.assertEqual(restaurant_id, 1)
        restaurant = get_restaurant()
        self.assertEqual(restaurant["name"], "Harbor Bistro")
        self.assertEqual(restaurant["contact"], "contact@harbor.test")

    def test_farm_listing_request_review_flow(self):
        farm_id = create_farm(
            "Aiko Fisheries",
            "Port Town",
            35.6,
            139.7,
            "",
            "farmer@aiko.test",
        )
        listing_id = create_listing(
            farm_id,
            "Mackerel",
            120.0,
            14.5,
            True,
            False,
            True,
            False,
            True,
            True,
            False,
            True,
            "Ready by 9 AM",
        )
        restaurant_id = upsert_restaurant(
            "Harbor Bistro",
            "Downtown",
            35.0,
            139.0,
            "",
            "",
        )
        request_id = create_request(
            listing_id,
            restaurant_id,
            10.0,
            "600-800",
            "Chilled",
            "Today Morning",
            "Any morning",
            "Delivery",
            "Please pack with ice",
        )
        update_request_status(request_id, "Accepted")

        farm = get_farm(farm_id)
        self.assertEqual(farm["name"], "Aiko Fisheries")
        self.assertEqual(len(list_farms()), 1)

        listing = get_listing(listing_id)
        self.assertEqual(listing["fish_name"], "Mackerel")
        self.assertEqual(len(list_listings()), 1)

        request = get_request(request_id)
        self.assertEqual(request["status"], "Accepted")
        self.assertIsNotNone(request["updated_at"])

        all_requests = list_requests()
        self.assertEqual(len(all_requests), 1)
        filtered_by_restaurant = list_requests(restaurant_id=restaurant_id)
        self.assertEqual(len(filtered_by_restaurant), 1)
        filtered_by_farm = list_requests(farm_id=farm_id)
        self.assertEqual(len(filtered_by_farm), 1)
        filtered_by_status = list_requests(status="Accepted")
        self.assertEqual(len(filtered_by_status), 1)

        review_id = create_review(
            request_id,
            farm_id,
            restaurant_id,
            4,
            "Great quality",
        )
        self.assertIsInstance(review_id, int)
        avg_rating = avg_rating_for_farm(farm_id)
        self.assertAlmostEqual(avg_rating, 4.0)
        review = get_review_by_request(request_id)
        self.assertEqual(review["stars"], 4)


if __name__ == "__main__":
    unittest.main()
