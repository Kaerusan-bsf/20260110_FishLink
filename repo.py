from db import get_conn


def _row_to_dict(row):
    if row is None:
        return None
    return dict(row)


def upsert_restaurant(name, location_text, lat, lng, maps_url, contact):
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO restaurants (
                id,
                name,
                location_text,
                lat,
                lng,
                maps_url,
                contact
            )
            VALUES (1, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                location_text = excluded.location_text,
                lat = excluded.lat,
                lng = excluded.lng,
                maps_url = excluded.maps_url,
                contact = excluded.contact
            """,
            (name, location_text, lat, lng, maps_url, contact),
        )
    return 1


def get_restaurant(restaurant_id=1):
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT id, name, location_text, lat, lng, maps_url, contact
            FROM restaurants
            WHERE id = ?
            """,
            (restaurant_id,),
        ).fetchone()
    return _row_to_dict(row)


def create_farm(name, location_text, lat, lng, maps_url, contact):
    with get_conn() as conn:
        cursor = conn.execute(
            """
            INSERT INTO farms (name, location_text, lat, lng, maps_url, contact)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (name, location_text, lat, lng, maps_url, contact),
        )
    return cursor.lastrowid


def get_farm(farm_id):
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT id, name, location_text, lat, lng, maps_url, contact
            FROM farms
            WHERE id = ?
            """,
            (farm_id,),
        ).fetchone()
    return _row_to_dict(row)


def list_farms():
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT id, name, location_text, lat, lng, maps_url, contact
            FROM farms
            ORDER BY id
            """
        ).fetchall()
    return [dict(row) for row in rows]


def create_listing(
    farm_id,
    fish_name,
    quantity_kg,
    price_per_kg,
    slot_today_morning,
    slot_today_evening,
    slot_next_morning,
    slot_next_evening,
    allow_delivery,
    allow_pickup,
    allow_live,
    allow_fresh,
    approx_time,
):
    with get_conn() as conn:
        cursor = conn.execute(
            """
            INSERT INTO listings (
                farm_id,
                fish_name,
                quantity_kg,
                price_per_kg,
                slot_today_morning,
                slot_today_evening,
                slot_next_morning,
                slot_next_evening,
                allow_delivery,
                allow_pickup,
                allow_live,
                allow_fresh,
                approx_time
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                farm_id,
                fish_name,
                quantity_kg,
                price_per_kg,
                int(bool(slot_today_morning)),
                int(bool(slot_today_evening)),
                int(bool(slot_next_morning)),
                int(bool(slot_next_evening)),
                int(bool(allow_delivery)),
                int(bool(allow_pickup)),
                int(bool(allow_live)),
                int(bool(allow_fresh)),
                approx_time,
            ),
        )
    return cursor.lastrowid


def list_listings():
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT
                id,
                farm_id,
                fish_name,
                quantity_kg,
                price_per_kg,
                slot_today_morning,
                slot_today_evening,
                slot_next_morning,
                slot_next_evening,
                allow_delivery,
                allow_pickup,
                allow_live,
                allow_fresh,
                approx_time
            FROM listings
            ORDER BY id
            """
        ).fetchall()
    return [dict(row) for row in rows]


def get_listing(listing_id):
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT
                id,
                farm_id,
                fish_name,
                quantity_kg,
                price_per_kg,
                slot_today_morning,
                slot_today_evening,
                slot_next_morning,
                slot_next_evening,
                allow_delivery,
                allow_pickup,
                allow_live,
                allow_fresh,
                approx_time
            FROM listings
            WHERE id = ?
            """,
            (listing_id,),
        ).fetchone()
    return _row_to_dict(row)


def create_request(
    listing_id,
    restaurant_id,
    quantity_kg,
    preferred_size,
    fish_condition,
    time_slot,
    preferred_time_window,
    delivery_method,
    notes,
    status="Requested",
):
    with get_conn() as conn:
        cursor = conn.execute(
            """
            INSERT INTO requests (
                listing_id,
                restaurant_id,
                status,
                quantity_kg,
                preferred_size_text,
                fish_condition,
                time_slot,
                delivery_method,
                preferred_time_window,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                listing_id,
                restaurant_id,
                status,
                quantity_kg,
                preferred_size,
                fish_condition,
                time_slot,
                delivery_method,
                preferred_time_window,
                notes,
            ),
        )
    return cursor.lastrowid


def list_requests(restaurant_id=None, farm_id=None, status=None):
    sql = """
        SELECT
            requests.id,
            requests.listing_id,
            requests.restaurant_id,
            requests.status,
            requests.quantity_kg,
            requests.preferred_size_text,
            requests.fish_condition,
            requests.time_slot,
            requests.delivery_method,
            requests.preferred_time_window,
            requests.notes,
            requests.distance_km,
            requests.created_at,
            requests.updated_at
        FROM requests
        JOIN listings ON listings.id = requests.listing_id
    """
    conditions = []
    params = []
    if restaurant_id is not None:
        conditions.append("requests.restaurant_id = ?")
        params.append(restaurant_id)
    if farm_id is not None:
        conditions.append("listings.farm_id = ?")
        params.append(farm_id)
    if status is not None:
        conditions.append("requests.status = ?")
        params.append(status)
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    sql += " ORDER BY requests.updated_at DESC, requests.id DESC"
    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(row) for row in rows]


def update_request_status(request_id, new_status):
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE requests
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (new_status, request_id),
        )


def get_request(request_id):
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT
                id,
                listing_id,
                restaurant_id,
                status,
                quantity_kg,
                preferred_size_text,
                fish_condition,
                time_slot,
                delivery_method,
                preferred_time_window,
                notes,
                distance_km,
                created_at,
                updated_at
            FROM requests
            WHERE id = ?
            """,
            (request_id,),
        ).fetchone()
    return _row_to_dict(row)


def create_review(request_id, farm_id, restaurant_id, stars, comment):
    with get_conn() as conn:
        cursor = conn.execute(
            """
            INSERT INTO reviews (request_id, farm_id, restaurant_id, stars, comment)
            VALUES (?, ?, ?, ?, ?)
            """,
            (request_id, farm_id, restaurant_id, stars, comment),
        )
    return cursor.lastrowid


def avg_rating_for_farm(farm_id):
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT AVG(stars) AS avg_stars
            FROM reviews
            WHERE farm_id = ?
            """,
            (farm_id,),
        ).fetchone()
    if row is None or row["avg_stars"] is None:
        return None
    return float(row["avg_stars"])


def get_review_by_request(request_id):
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT id, request_id, farm_id, restaurant_id, stars, comment
            FROM reviews
            WHERE request_id = ?
            """,
            (request_id,),
        ).fetchone()
    return _row_to_dict(row)
