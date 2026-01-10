import math
import re
from urllib.parse import quote

import streamlit as st

from db import ensure_latest_schema
from fishlink import (
    FarmerListing,
    Request,
    RequestStatus,
    _ALLOWED_TRANSITIONS,
)
from repo import (
    create_farm,
    create_listing,
    get_farm,
    get_listing,
    list_listings,
    list_requests,
    update_request_status,
    create_request,
    get_restaurant,
    upsert_restaurant,
)

ensure_latest_schema()


TIME_SLOTS = [
    "Today Morning",
    "Today Evening",
    "Next-day Morning",
    "Next-day Evening",
]
DELIVERY_METHODS = [
    "Delivery",
    "Pickup",
]
FISH_CONDITIONS = [
    "Live",
    "Chilled",
    "Frozen",
]
MORNING_WINDOWS = ["7–8", "8–9", "Any morning"]
EVENING_WINDOWS = ["15–16", "16–17", "Any evening"]


def get_demo_listing_seed():
    return [
        {
            "name": "Aiko Fisheries",
            "farm_location_text": "Port Town",
            "farm_lat": 35.6895,
            "farm_lng": 139.6917,
            "farm_maps_url": "",
            "fish_name": "Mackerel",
            "quantity_kg": 120.0,
            "price_per_kg": 14.5,
            "time_slots": ["Today Morning", "Next-day Evening"],
            "delivery_methods": ["Delivery", "Pickup"],
            "fish_conditions": ["Chilled", "Frozen"],
            "approx_time": "Ready by 9 AM",
        },
        {
            "name": "Blue Bay Co.",
            "farm_location_text": "Harbor City",
            "farm_lat": 34.6937,
            "farm_lng": 135.5023,
            "farm_maps_url": "",
            "fish_name": "Sea Bream",
            "quantity_kg": 200.0,
            "price_per_kg": 12.0,
            "time_slots": ["Today Evening", "Next-day Morning"],
            "delivery_methods": ["Delivery"],
            "fish_conditions": ["Live", "Chilled"],
            "approx_time": "",
        },
        {
            "name": "Sunrise Catch",
            "farm_location_text": "Coastal Village",
            "farm_lat": 33.5902,
            "farm_lng": 130.4017,
            "farm_maps_url": "",
            "fish_name": "Sardines",
            "quantity_kg": 80.0,
            "price_per_kg": 16.0,
            "time_slots": ["Today Morning", "Today Evening"],
            "delivery_methods": ["Pickup"],
            "fish_conditions": ["Chilled"],
            "approx_time": "After 3 PM",
        },
    ]


def ensure_state():
    if "reviews" not in st.session_state:
        st.session_state.reviews = {}
    if "demo_reset_message" not in st.session_state:
        st.session_state.demo_reset_message = False
    if "selected_listing_id" not in st.session_state:
        st.session_state.selected_listing_id = None
    if "nav" not in st.session_state:
        st.session_state.nav = "Farmer Listing"
    if "restaurant_name" not in st.session_state:
        st.session_state.restaurant_name = "Harbor Bistro"
    if "restaurant_location_text" not in st.session_state:
        st.session_state.restaurant_location_text = "Downtown"
    if "restaurant_lat" not in st.session_state:
        st.session_state.restaurant_lat = ""
    if "restaurant_lng" not in st.session_state:
        st.session_state.restaurant_lng = ""
    if "restaurant_maps_url" not in st.session_state:
        st.session_state.restaurant_maps_url = ""
    if "restaurant_contact" not in st.session_state:
        st.session_state.restaurant_contact = ""
    if "sort_option" not in st.session_state:
        st.session_state.sort_option = "Default"
    if "listing_conditions" not in st.session_state:
        st.session_state.listing_conditions = {}
    if "role" not in st.session_state:
        st.session_state.role = None


def reset_demo_data():
    for key in ("listings", "requests", "reviews", "listing_conditions"):
        if key in st.session_state:
            del st.session_state[key]
    st.session_state.demo_reset_message = True
    ensure_state()


def valid_preferred_size(value: str) -> bool:
    if not value:
        return True
    if re.fullmatch(r"\d+(\.\d+)?", value):
        return float(value) > 0
    if re.fullmatch(r"\d+(\.\d+)?-\d+(\.\d+)?", value):
        low_text, high_text = value.split("-", maxsplit=1)
        low = float(low_text)
        high = float(high_text)
        return low > 0 and high > 0 and low < high
    return False


def parse_optional_float(text):
    if text is None:
        return None
    value = text.strip()
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def haversine_km(lat1, lng1, lat2, lng2):
    radius_km = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)
    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius_km * c


def build_maps_search_url(text):
    query = quote(text)
    return f"https://www.google.com/maps/search/?api=1&query={query}"


def ensure_demo_listings_in_db():
    if list_listings():
        return
    for listing in get_demo_listing_seed():
        farm_id = create_farm(
            listing["name"],
            listing["farm_location_text"],
            listing["farm_lat"],
            listing["farm_lng"],
            listing["farm_maps_url"],
            "",
        )
        listing_id = create_listing(
            farm_id,
            listing["fish_name"],
            listing["quantity_kg"],
            listing["price_per_kg"],
            "Today Morning" in listing["time_slots"],
            "Today Evening" in listing["time_slots"],
            "Next-day Morning" in listing["time_slots"],
            "Next-day Evening" in listing["time_slots"],
            "Delivery" in listing["delivery_methods"],
            "Pickup" in listing["delivery_methods"],
            "Live" in listing["fish_conditions"],
            any(
                condition in listing["fish_conditions"]
                for condition in ("Chilled", "Frozen")
            ),
            listing["approx_time"],
        )
        st.session_state.listing_conditions[listing_id] = listing["fish_conditions"]


def build_listings_for_ui():
    listings = []
    for listing in list_listings():
        farm = get_farm(listing["farm_id"])
        if not farm:
            continue
        time_slots = []
        if listing["slot_today_morning"]:
            time_slots.append("Today Morning")
        if listing["slot_today_evening"]:
            time_slots.append("Today Evening")
        if listing["slot_next_morning"]:
            time_slots.append("Next-day Morning")
        if listing["slot_next_evening"]:
            time_slots.append("Next-day Evening")
        delivery_methods = []
        if listing["allow_delivery"]:
            delivery_methods.append("Delivery")
        if listing["allow_pickup"]:
            delivery_methods.append("Pickup")
        conditions = st.session_state.listing_conditions.get(listing["id"])
        if conditions is None:
            conditions = []
            if listing["allow_live"]:
                conditions.append("Live")
            if listing["allow_fresh"]:
                conditions.append("Chilled")
        listings.append(
            {
                "id": listing["id"],
                "name": farm["name"],
                "farm_location_text": farm["location_text"],
                "farm_lat": farm["lat"],
                "farm_lng": farm["lng"],
                "farm_maps_url": farm["maps_url"],
                "farm_contact": farm.get("contact") or "",
                "fish_name": listing["fish_name"],
                "quantity_kg": listing["quantity_kg"],
                "price_per_kg": listing["price_per_kg"],
                "time_slots": time_slots,
                "delivery_methods": delivery_methods,
                "fish_conditions": conditions,
                "approx_time": listing["approx_time"] or "",
            }
        )
    return listings


def screen_farmer_listing(farmer_listings):
    st.header("Farmer Listing")
    st.subheader("Publish listing")
    with st.form("publish_listing"):
        name = st.text_input("Farm name")
        farm_location_text = st.text_input("Farm location text")
        farm_lat_text = st.text_input("Farm latitude (optional)")
        farm_lng_text = st.text_input("Farm longitude (optional)")
        farm_maps_url = st.text_input("Farm maps URL (optional)")
        farm_contact = st.text_input("Contact (optional)")
        fish_name = st.text_input("Fish name (optional)")
        quantity_kg = st.number_input("Quantity (kg)", min_value=0.0, step=1.0)
        price_per_kg = st.number_input("Price per kg", min_value=0.0, step=0.5)
        time_slots = st.multiselect("Time slots", TIME_SLOTS)
        delivery_methods = st.multiselect("Delivery methods", DELIVERY_METHODS)
        fish_conditions = st.multiselect("Fish conditions", FISH_CONDITIONS)
        approx_time = st.text_input("Approx. time (optional)")
        submitted = st.form_submit_button("Publish listing")

    if submitted:
        errors = []
        if quantity_kg <= 0:
            errors.append("Quantity must be greater than 0.")
        if price_per_kg <= 0:
            errors.append("Price per kg must be greater than 0.")
        if not time_slots:
            errors.append("Select at least one time slot.")
        if not delivery_methods:
            errors.append("Select at least one delivery method.")
        if not fish_conditions:
            errors.append("Select at least one fish condition.")

        if errors:
            st.error(" ".join(errors))
        else:
            farm_id = create_farm(
                name or "Unnamed Farm",
                farm_location_text or "Unknown",
                parse_optional_float(farm_lat_text),
                parse_optional_float(farm_lng_text),
                farm_maps_url.strip(),
                farm_contact.strip(),
            )
            listing_id = create_listing(
                farm_id,
                fish_name.strip(),
                quantity_kg,
                price_per_kg,
                "Today Morning" in time_slots,
                "Today Evening" in time_slots,
                "Next-day Morning" in time_slots,
                "Next-day Evening" in time_slots,
                "Delivery" in delivery_methods,
                "Pickup" in delivery_methods,
                "Live" in fish_conditions,
                any(condition in fish_conditions for condition in ("Chilled", "Frozen")),
                approx_time,
            )
            st.session_state.listing_conditions[listing_id] = list(fish_conditions)
            st.success(f"Listing {listing_id} published.")

    st.write("Available listings:")
    for listing in farmer_listings:
        st.write(
            f"- {listing['name']} ({listing['farm_location_text']}) "
            f"[{listing['id']}]"
        )


def summarise_time_slots(time_slots):
    today = []
    next_day = []
    for slot in time_slots:
        if "Today" in slot:
            if "Morning" in slot:
                today.append("Morning")
            if "Evening" in slot:
                today.append("Evening")
        if "Next-day" in slot:
            if "Morning" in slot:
                next_day.append("Morning")
            if "Evening" in slot:
                next_day.append("Evening")
    parts = []
    if today:
        parts.append(f"Today: {', '.join(dict.fromkeys(today))}")
    if next_day:
        parts.append(f"Next-day: {', '.join(dict.fromkeys(next_day))}")
    return " | ".join(parts)


def average_rating_for_listing(listing_id, reviews):
    stars = []
    for review in reviews.values():
        if review.get("listing_id") == listing_id:
            stars.append(review["stars"])
    if not stars:
        return None
    return sum(stars) / len(stars)


def format_quantity_kg(value):
    if float(value).is_integer():
        return str(int(value))
    return str(value)


def format_price_per_kg(value):
    return f"${value} / kg"


def screen_todays_farms(farmer_listings):
    st.header("Today’s Farms")
    st.write("Farms available today:")
    if not farmer_listings:
        st.write("No listings available.")
        return
    reviews = st.session_state.reviews
    restaurant_lat = parse_optional_float(st.session_state.restaurant_lat)
    restaurant_lng = parse_optional_float(st.session_state.restaurant_lng)
    restaurant_coords_missing = restaurant_lat is None or restaurant_lng is None

    indexed_listings = list(enumerate(farmer_listings))
    distances = {}
    for index, listing in indexed_listings:
        farm_lat = listing.get("farm_lat")
        farm_lng = listing.get("farm_lng")
        if (
            restaurant_lat is not None
            and restaurant_lng is not None
            and farm_lat is not None
            and farm_lng is not None
        ):
            distances[index] = haversine_km(
                restaurant_lat,
                restaurant_lng,
                farm_lat,
                farm_lng,
            )

    if st.session_state.sort_option == "Distance (if available)":
        sortable = []
        unsortable = []
        for index, listing in indexed_listings:
            if index in distances:
                sortable.append((distances[index], index, listing))
            else:
                unsortable.append((index, listing))
        sortable.sort(key=lambda item: item[0])
        ordered = [(index, listing) for _, index, listing in sortable] + unsortable
    else:
        ordered = indexed_listings

    for index, listing in ordered:
        with st.container():
            st.subheader(listing["name"])
            if listing["farm_location_text"]:
                st.write(listing["farm_location_text"])
            avg_rating = average_rating_for_listing(
                listing["id"],
                reviews,
            )
            if avg_rating is not None:
                st.write(f"Average rating: {avg_rating:.1f} / 5")
            time_summary = summarise_time_slots(listing["time_slots"])
            if time_summary:
                st.write(f"Time slots: {time_summary}")
            if listing["delivery_methods"]:
                st.write(
                    "Delivery methods: "
                    + " / ".join(listing["delivery_methods"])
                )
            if listing.get("fish_name"):
                st.write(f"Fish: {listing['fish_name']}")
            st.write(f"Available: {format_quantity_kg(listing['quantity_kg'])} kg")
            st.write(f"Price per kg: {format_price_per_kg(listing['price_per_kg'])}")
            if index in distances:
                st.write(f"📏 {distances[index]:.1f} km")
            else:
                farm_coords_missing = (
                    listing.get("farm_lat") is None or listing.get("farm_lng") is None
                )
                if restaurant_coords_missing:
                    st.write("📏 — (missing restaurant coords)")
                elif farm_coords_missing:
                    st.write("📏 — (missing farm coords)")
                else:
                    st.write("📏 —")
            if listing.get("farm_maps_url"):
                st.link_button("🗺 Open farm map", listing["farm_maps_url"])
            if st.button(f"View details: {listing['id']}"):
                st.session_state.selected_listing_id = listing["id"]
                st.success(
                    "Selected. Open “Farm Detail” from the sidebar to continue."
                )
            st.divider()


def screen_farm_detail(farmer_listings, requests):
    st.header("Farm Detail")
    if not farmer_listings:
        st.write("No listings available.")
        return

    selected_index = 0
    selected_listing_id = st.session_state.selected_listing_id
    if selected_listing_id:
        for index, listing in enumerate(farmer_listings):
            if listing["id"] == selected_listing_id:
                selected_index = index
                break
    selected = st.selectbox(
        "Select a farm",
        farmer_listings,
        index=selected_index,
        key="farm_detail_selection",
        format_func=lambda item: (
            item["name"]
            if not item["farm_location_text"]
            else f"{item['name']} ({item['farm_location_text']})"
        ),
    )
    if selected_listing_id:
        st.session_state.selected_listing_id = None
    st.write(f"Farm ID: {selected['id']}")
    st.write(f"Name: {selected['name']}")
    st.write(f"Location: {selected['farm_location_text']}")
    if selected.get("farm_maps_url"):
        st.link_button("Open in Google Maps", selected["farm_maps_url"])
    if selected.get("farm_contact"):
        st.write(f"Contact: {selected['farm_contact']}")

    st.subheader("Create request")
    with st.form("create_request"):
        quantity_kg = st.number_input("Quantity (kg)", min_value=0.0, step=1.0)
        preferred_size = st.text_input(
            "Preferred size (g per head, optional)",
            placeholder="e.g. 600-800 or 700",
        )
        fish_condition = st.selectbox(
            "Fish condition",
            selected["fish_conditions"],
        )
        time_slot = st.selectbox(
            "Time slot",
            selected["time_slots"],
        )
        if "Morning" in time_slot:
            window_options = MORNING_WINDOWS
        else:
            window_options = EVENING_WINDOWS
        default_window = "Any morning" if "Morning" in time_slot else "Any evening"
        preferred_time_window = st.selectbox(
            "Preferred time window (optional)",
            window_options,
            index=window_options.index(default_window),
        )
        delivery_method = st.selectbox(
            "Delivery method",
            selected["delivery_methods"],
        )
        notes = st.text_area("Notes (optional)")
        submitted = st.form_submit_button("Submit request")

    if submitted:
        errors = []
        if quantity_kg <= 0:
            errors.append("Quantity must be greater than 0.")
        if preferred_size and not valid_preferred_size(preferred_size):
            errors.append(
                "Preferred size must be a positive number or range like 600-800."
            )
        if not fish_condition:
            errors.append("Select a fish condition.")
        if not time_slot:
            errors.append("Select a time slot.")
        if not delivery_method:
            errors.append("Select a delivery method.")

        if errors:
            st.error(" ".join(errors))
        else:
            request_id = create_request(
                selected["id"],
                1,
                quantity_kg,
                preferred_size,
                fish_condition,
                time_slot,
                preferred_time_window,
                delivery_method,
                notes,
                status=RequestStatus.REQUESTED.value,
            )
            st.success(f"Request {request_id} created.")
            st.rerun()


def screen_farmer_actions(requests):
    st.header("Farmer Accept / Reject / Ready")
    requests = list_requests()
    if not requests:
        st.write("No requests yet.")
        return

    for request in requests:
        st.write(
            f"Request {request['id']} for listing {request['listing_id']}"
        )
        st.write(f"Current status: {request['status']}")
        restaurant = None
        if request.get("restaurant_id") == 1:
            restaurant = get_restaurant(1)
        listing = get_listing(request["listing_id"])
        farm = get_farm(listing["farm_id"]) if listing else None
        if restaurant:
            st.write(f"Restaurant: {restaurant.get('name', '')}")
            st.write(f"Restaurant location: {restaurant.get('location_text', '')}")
        if restaurant and farm:
            restaurant_lat = restaurant.get("lat")
            restaurant_lng = restaurant.get("lng")
            farm_lat = farm.get("lat")
            farm_lng = farm.get("lng")
            if (
                restaurant_lat is not None
                and restaurant_lng is not None
                and farm_lat is not None
                and farm_lng is not None
            ):
                distance_km = haversine_km(
                    restaurant_lat,
                    restaurant_lng,
                    farm_lat,
                    farm_lng,
                )
                st.write(f"Distance: {distance_km:.1f} km")
        if request["delivery_method"] == "Pickup":
            if farm and farm.get("maps_url"):
                st.link_button("Open restaurant map", farm["maps_url"])
        else:
            if restaurant and restaurant.get("maps_url"):
                st.link_button("Open restaurant map", restaurant["maps_url"])
        st.write(f"Quantity: {request['quantity_kg']} kg")
        st.write(f"Time slot: {request['time_slot']}")
        st.write(f"Delivery: {request['delivery_method']}")
        if restaurant and restaurant.get("contact"):
            st.write(f"Restaurant contact: {restaurant['contact']}")
        preferred_time_window = request.get("preferred_time_window") or ""
        if preferred_time_window:
            st.write(f"Preferred window: {preferred_time_window}")
        if request["status"] == RequestStatus.REQUESTED.value:
            if st.button(f"Accept {request['id']}"):
                try:
                    update_request_status(request["id"], RequestStatus.ACCEPTED.value)
                    st.rerun()
                except ValueError:
                    st.error("Unable to accept request.")
        elif request["status"] == RequestStatus.ACCEPTED.value:
            if st.button(f"Start Preparing {request['id']}"):
                try:
                    update_request_status(
                        request["id"],
                        RequestStatus.PREPARING.value,
                    )
                    st.rerun()
                except ValueError:
                    st.error("Unable to start preparing.")
        elif request["status"] == RequestStatus.PREPARING.value:
            if st.button(f"Ready {request['id']}"):
                try:
                    update_request_status(request["id"], RequestStatus.READY.value)
                    st.rerun()
                except ValueError:
                    st.error("Unable to mark ready.")
        elif request["status"] == RequestStatus.READY.value:
            if st.button(f"Complete {request['id']}"):
                try:
                    update_request_status(request["id"], RequestStatus.COMPLETED.value)
                    st.rerun()
                except ValueError:
                    st.error("Unable to complete request.")
        st.divider()
        st.divider()


def screen_request_status(requests):
    st.header("Request Status")
    requests = list_requests(restaurant_id=1)
    if not requests:
        st.write("No requests yet.")
        return
    for request in requests:
        st.write(f"Request {request['id']}: {request['status']}")
        if request["status"] in {
            RequestStatus.ACCEPTED.value,
            RequestStatus.PREPARING.value,
            RequestStatus.READY.value,
        }:
            listing = get_listing(request["listing_id"])
            farm = get_farm(listing["farm_id"]) if listing else None
            if farm and farm.get("contact"):
                st.write(f"Farm contact: {farm['contact']}")
        if request["status"] == RequestStatus.READY.value:
            delivery_method = request.get("delivery_method", "")
            listing = get_listing(request["listing_id"])
            farm = get_farm(listing["farm_id"]) if listing else None
            maps_url = ""
            if delivery_method == "Delivery":
                if st.session_state.restaurant_maps_url:
                    maps_url = st.session_state.restaurant_maps_url
                else:
                    text = (
                        st.session_state.restaurant_location_text
                        or st.session_state.restaurant_name
                    )
                    if text:
                        maps_url = build_maps_search_url(text)
            if delivery_method == "Pickup":
                if farm and farm.get("maps_url"):
                    maps_url = farm["maps_url"]
                else:
                    text = ""
                    if farm:
                        text = farm.get("location_text") or farm.get("name")
                    if text:
                        maps_url = build_maps_search_url(text)
            if maps_url:
                st.link_button("Open in Google Maps", maps_url)
        if request["status"] == RequestStatus.COMPLETED.value:
            st.write("Leave a review")
            with st.form(f"review_{request['id']}"):
                stars = st.radio(
                    "Stars",
                    [1, 2, 3, 4, 5],
                    horizontal=True,
                )
                comment = st.text_area("Comment (optional)")
                submitted = st.form_submit_button("Submit review")
            if submitted:
                st.session_state.reviews[request["id"]] = {
                    "stars": stars,
                    "comment": comment.strip(),
                    "listing_id": request["listing_id"],
                }
                st.success("Review submitted.")


def screen_monitor():
    st.header("Monitor")
    requests = list_requests()
    if not requests:
        st.write("No requests yet.")
        return
    rows = []
    for request in requests:
        listing = get_listing(request["listing_id"])
        farm = get_farm(listing["farm_id"]) if listing else None
        restaurant = get_restaurant(request["restaurant_id"])
        rows.append(
            {
                "request_id": request["id"],
                "status": request["status"],
                "updated_at": request["updated_at"],
                "farm_name": farm.get("name") if farm else "",
                "farm_location_text": farm.get("location_text") if farm else "",
                "restaurant_name": restaurant.get("name") if restaurant else "",
                "fish_name": listing.get("fish_name") if listing else "",
                "quantity_kg": request["quantity_kg"],
                "delivery_method": request["delivery_method"],
                "time_slot": request["time_slot"],
                "preferred_time_window": request.get("preferred_time_window") or "",
                "fish_condition": request["fish_condition"],
                "farm_contact": farm.get("contact") if farm else "",
                "restaurant_contact": restaurant.get("contact") if restaurant else "",
            }
        )
    st.dataframe(rows, use_container_width=True)


def screen_restaurant_settings():
    st.header("Restaurant Settings")
    with st.form("restaurant_settings"):
        name = st.text_input("Restaurant name", key="restaurant_name")
        location_text = st.text_input(
            "Restaurant location text",
            key="restaurant_location_text",
        )
        lat_text = st.text_input("Restaurant latitude (optional)", key="restaurant_lat")
        lng_text = st.text_input(
            "Restaurant longitude (optional)",
            key="restaurant_lng",
        )
        maps_url = st.text_input(
            "Restaurant maps URL (optional)",
            key="restaurant_maps_url",
        )
        contact = st.text_input("Contact (optional)", key="restaurant_contact")
        submitted = st.form_submit_button("Save settings")
    if submitted:
        if not name.strip() or not location_text.strip():
            st.error("Restaurant name and location are required.")
            return
        upsert_restaurant(
            name,
            location_text,
            parse_optional_float(lat_text),
            parse_optional_float(lng_text),
            maps_url,
            contact.strip(),
        )
        st.success("Restaurant settings saved.")


def main():
    st.title("FishLink MVP")
    ensure_state()
    if not st.session_state.role:
        st.write("Select your role:")
        if st.button("Restaurant"):
            st.session_state.role = "Restaurant"
            st.rerun()
        if st.button("Farmer"):
            st.session_state.role = "Farmer"
            st.rerun()
        return
    if st.session_state.role == "Farmer":
        screens = [
            "Farmer Listing",
            "Farmer Accept / Reject / Ready",
            "Monitor",
        ]
    else:
        screens = [
            "Restaurant Settings",
            "Today’s Farms",
            "Farm Detail",
            "Request Status",
            "Monitor",
        ]
    if st.session_state.get("nav") not in screens:
        st.session_state.pop("nav", None)
    selection = st.sidebar.radio("Navigate", screens, key="nav", index=0)
    if st.sidebar.button("Switch role"):
        st.session_state.role = None
        st.session_state.pop("nav", None)
        st.rerun()
    if st.session_state.role == "Restaurant":
        st.sidebar.markdown("### Sort")
        st.sidebar.selectbox(
            "Sort Today’s Farms",
            ["Default", "Distance (if available)"],
            key="sort_option",
        )
    if st.session_state.role == "Restaurant":
        upsert_restaurant(
            st.session_state.restaurant_name,
            st.session_state.restaurant_location_text,
            parse_optional_float(st.session_state.restaurant_lat),
            parse_optional_float(st.session_state.restaurant_lng),
            st.session_state.restaurant_maps_url,
            st.session_state.restaurant_contact.strip(),
        )
    ensure_demo_listings_in_db()
    farmer_listings = build_listings_for_ui()
    st.session_state.listings = farmer_listings
    if st.session_state.demo_reset_message:
        st.sidebar.success("UI state reset.")
        st.session_state.demo_reset_message = False

    if selection == "Farmer Listing":
        screen_farmer_listing(farmer_listings)
    elif selection == "Restaurant Settings":
        screen_restaurant_settings()
    elif selection == "Today’s Farms":
        screen_todays_farms(farmer_listings)
    elif selection == "Farm Detail":
        screen_farm_detail(farmer_listings, None)
    elif selection == "Farmer Accept / Reject / Ready":
        screen_farmer_actions(None)
    elif selection == "Request Status":
        screen_request_status(None)
    elif selection == "Monitor":
        screen_monitor()

    st.sidebar.markdown("---")
    if st.sidebar.button("Reset UI"):
        reset_demo_data()
        st.rerun()
    st.sidebar.caption("Does not delete database records.")


if __name__ == "__main__":
    main()
