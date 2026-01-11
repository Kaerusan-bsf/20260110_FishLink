import math
import re
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
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
    avg_rating_for_farm,
    create_farm,
    create_listing,
    create_review,
    get_farm,
    get_listing,
    get_review_by_request,
    list_listings,
    list_requests,
    update_request_status,
    create_request,
    get_restaurant,
    upsert_restaurant,
)

ensure_latest_schema()

TRANSLATIONS = {
    "en": {
        "nav.restaurant_settings": "Restaurant Settings",
        "nav.todays_farms": "Today’s Farms",
        "nav.request_status": "Request Status",
        "nav.operations_monitor": "Operations Monitor",
        "nav.farmer_listing": "Farmer Listing",
        "nav.farmer_actions": "Farmer Accept / Reject / Ready (Farmer)",
        "nav.monitor": "Monitor",
        "btn.switch_role": "Switch role",
        "btn.reset_ui": "Reset UI",
        "btn.save_settings": "Save settings",
        "btn.publish_listing": "Publish listing",
        "btn.order_details": "Order / Details",
        "btn.close": "Close",
        "btn.accept": "Accept",
        "btn.reject": "Reject",
        "btn.start_preparing": "Start Preparing",
        "btn.ready": "Ready",
        "btn.complete": "Complete",
        "btn.submit_request": "Submit request",
        "btn.open_farm_map": "Open farm map",
        "btn.open_restaurant_map": "Open restaurant map",
        "btn.open_google_maps": "Open in Google Maps",
        "btn.leave_review": "Leave a review",
        "btn.submit_review": "Submit review",
        "lbl.restaurant": "Restaurant",
        "lbl.farm": "Farm",
        "lbl.address": "Address",
        "lbl.contact": "Contact",
        "lbl.fish": "Fish",
        "lbl.quantity": "Quantity (kg)",
        "lbl.price_per_kg": "Price per kg",
        "lbl.time_slot": "Time slot",
        "lbl.delivery_method": "Delivery method",
        "lbl.preferred_window": "Preferred delivery window (restaurant)",
        "lbl.notes": "Notes (optional)",
        "lbl.status": "Status",
        "lbl.requested_at": "Requested at",
        "lbl.last_updated": "Last updated",
        "lbl.review": "Review",
        "lbl.stars": "Stars",
        "lbl.comment": "Comment (optional)",
        "lbl.fish_condition": "Fish condition",
        "lbl.restaurant_name": "Restaurant name",
        "lbl.restaurant_address_full": (
            "Restaurant address (Village / Commune / District / Province)"
        ),
        "lbl.restaurant_maps_url_optional": "Restaurant maps URL (optional)",
        "lbl.farm_name": "Farm name",
        "lbl.farm_address_full": (
            "Farm address (Village / Commune / District / Province)"
        ),
        "lbl.farm_maps_url_optional": "Farm maps URL (optional)",
        "lbl.fish_name_optional": "Fish name (optional)",
        "lbl.time_slots": "Time slots",
        "lbl.delivery_methods": "Delivery methods",
        "lbl.fish_conditions": "Fish conditions",
        "lbl.approx_time_optional": "Approx. time (optional)",
        "ui.choose_options": "Choose options",
        "ph.address_example": "Village, Commune, District, Province",
        "lbl.farms_available_today": "Farms available today:",
        "msg.operations_monitor_desc": (
            "This page shows all requests across FishLink for operational monitoring."
        ),
        "sort.default": "Default",
        "sort.distance_if_available": "Distance (if available)",
        "opt.delivery": "Delivery",
        "opt.pickup": "Pickup",
        "opt.today_morning": "Today Morning",
        "opt.today_evening": "Today Evening",
        "opt.nextday_morning": "Next-day Morning",
        "opt.nextday_evening": "Next-day Evening",
        "opt.window_7_8": "7–8",
        "opt.window_8_9": "8–9",
        "opt.window_15_16": "15–16",
        "opt.window_16_17": "16–17",
        "opt.any_morning": "Any morning",
        "opt.any_evening": "Any evening",
        "opt.live": "Live",
        "opt.chilled": "Chilled",
        "opt.frozen": "Frozen",
        "status.Requested": "Requested",
        "status.Accepted": "Accepted",
        "status.Preparing": "Preparing",
        "status.Ready": "Ready",
        "status.Completed": "Completed",
        "status.Rejected": "Rejected",
        "msg.no_listings": (
            "No listings yet. Create your first listing from ‘Farmer Listing’."
        ),
        "msg.restaurant_not_set": "Restaurant: (not set)",
        "msg.request_sent": (
            "Request sent. Check status in ‘Request Status’."
        ),
        "msg.review_submitted": "Review submitted.",
    },
    "km": {
        "nav.restaurant_settings": "ការកំណត់ភោជនីយដ្ឋាន",
        "nav.todays_farms": "កសិដ្ឋានថ្ងៃនេះ",
        "nav.request_status": "ស្ថានភាពការបញ្ជាទិញ",
        "nav.operations_monitor": "ផ្ទាំងត្រួតពិនិត្យប្រតិបត្តិការ",
        "nav.farmer_listing": "ការបង្ហោះរបស់កសិករ",
        "nav.farmer_actions": "ការទទួល / បដិសេធ / រួចរាល់ (កសិករ)",
        "nav.monitor": "ត្រួតពិនិត្យ",
        "btn.switch_role": "ប្តូរតួនាទី",
        "btn.reset_ui": "កំណត់ឡើងវិញ UI",
        "btn.save_settings": "រក្សាទុកការកំណត់",
        "btn.publish_listing": "បង្ហោះការលក់",
        "btn.order_details": "បញ្ជាទិញ / ព័ត៌មានលម្អិត",
        "btn.close": "បិទ",
        "btn.accept": "ទទួលយក",
        "btn.reject": "បដិសេធ",
        "btn.start_preparing": "ចាប់ផ្តើមរៀបចំ",
        "btn.ready": "រួចរាល់",
        "btn.complete": "បញ្ចប់",
        "btn.submit_request": "ផ្ញើការបញ្ជាទិញ",
        "btn.open_farm_map": "បើកផែនទីកសិដ្ឋាន",
        "btn.open_restaurant_map": "បើកផែនទីភោជនីយដ្ឋាន",
        "btn.open_google_maps": "បើកក្នុង Google Maps",
        "btn.leave_review": "ទុកមតិយោបល់",
        "btn.submit_review": "ផ្ញើមតិយោបល់",
        "lbl.restaurant": "ភោជនីយដ្ឋាន",
        "lbl.farm": "កសិដ្ឋាន",
        "lbl.address": "អាសយដ្ឋាន",
        "lbl.contact": "ទំនាក់ទំនង",
        "lbl.fish": "ត្រី",
        "lbl.quantity": "បរិមាណ (គីឡូក្រាម)",
        "lbl.price_per_kg": "តម្លៃក្នុងមួយគីឡូក្រាម",
        "lbl.time_slot": "ពេលវេលា",
        "lbl.delivery_method": "វិធីដឹកជញ្ជូន",
        "lbl.preferred_window": "ពេលវេលាដឹកជញ្ជូនដែលភោជនីយដ្ឋានចង់បាន",
        "lbl.notes": "កំណត់ចំណាំ (ជាជម្រើស)",
        "lbl.status": "ស្ថានភាព",
        "lbl.requested_at": "បានស្នើនៅ",
        "lbl.last_updated": "បានធ្វើបច្ចុប្បន្នភាពចុងក្រោយ",
        "lbl.review": "មតិយោបល់",
        "lbl.stars": "ផ្កាយ",
        "lbl.comment": "មតិយោបល់ (ជាជម្រើស)",
        "lbl.fish_condition": "ស្ថានភាពត្រី",
        "lbl.restaurant_name": "ឈ្មោះភោជនីយដ្ឋាន",
        "lbl.restaurant_address_full": "អាសយដ្ឋានភោជនីយដ្ឋាន (ភូមិ / ឃុំ / ស្រុក / ខេត្ត)",
        "lbl.restaurant_maps_url_optional": "តំណផែនទីភោជនីយដ្ឋាន (ជាជម្រើស)",
        "lbl.farm_name": "ឈ្មោះកសិដ្ឋាន",
        "lbl.farm_address_full": "អាសយដ្ឋានកសិដ្ឋាន (ភូមិ / ឃុំ / ស្រុក / ខេត្ត)",
        "lbl.farm_maps_url_optional": "តំណផែនទីកសិដ្ឋាន (ជាជម្រើស)",
        "lbl.fish_name_optional": "ឈ្មោះត្រី (ជាជម្រើស)",
        "lbl.time_slots": "ពេលវេលា",
        "lbl.delivery_methods": "វិធីដឹកជញ្ជូន",
        "lbl.fish_conditions": "ស្ថានភាពត្រី",
        "lbl.approx_time_optional": "ពេលវេលាប៉ាន់ស្មាន (ជាជម្រើស)",
        "ui.choose_options": "ជ្រើសរើស",
        "ph.address_example": "ភូមិ, ឃុំ, ស្រុក, ខេត្ត",
        "lbl.farms_available_today": "កសិដ្ឋានដែលអាចរកបានថ្ងៃនេះ៖",
        "msg.operations_monitor_desc": (
            "ទំព័រនេះបង្ហាញការបញ្ជាទិញទាំងអស់ក្នុង FishLink សម្រាប់ត្រួតពិនិត្យប្រតិបត្តិការ។"
        ),
        "sort.default": "លំនាំដើម",
        "sort.distance_if_available": "ចម្ងាយ (ប្រសិនបើមាន)",
        "opt.delivery": "ដឹកជញ្ជូន",
        "opt.pickup": "ទៅយក",
        "opt.today_morning": "ព្រឹកថ្ងៃនេះ",
        "opt.today_evening": "ល្ងាចថ្ងៃនេះ",
        "opt.nextday_morning": "ព្រឹកថ្ងៃស្អែក",
        "opt.nextday_evening": "ល្ងាចថ្ងៃស្អែក",
        "opt.window_7_8": "07:00–08:00",
        "opt.window_8_9": "08:00–09:00",
        "opt.window_15_16": "15:00–16:00",
        "opt.window_16_17": "16:00–17:00",
        "opt.any_morning": "ព្រឹកណាក៏បាន",
        "opt.any_evening": "ល្ងាចណាក៏បាន",
        "opt.live": "រស់",
        "opt.chilled": "ត្រជាក់",
        "opt.frozen": "កក",
        "status.Requested": "បានស្នើ",
        "status.Accepted": "បានទទួលយក",
        "status.Preparing": "កំពុងរៀបចំ",
        "status.Ready": "រួចរាល់",
        "status.Completed": "បានបញ្ចប់",
        "status.Rejected": "បានបដិសេធ",
        "msg.no_listings": (
            "មិនទាន់មានការបង្ហោះទេ។ សូមបង្កើតការបង្ហោះដំបូងពី "
            "“ការបង្ហោះរបស់កសិករ”。"
        ),
        "msg.restaurant_not_set": "ភោជនីយដ្ឋាន៖ (មិនទាន់កំណត់)",
        "msg.request_sent": (
            "បានផ្ញើការបញ្ជាទិញ។ សូមពិនិត្យស្ថានភាពនៅ "
            "“ស្ថានភាពការបញ្ជាទិញ”。"
        ),
        "msg.review_submitted": "បានផ្ញើមតិយោបល់។",
    },
}


def t(key: str) -> str:
    lang = st.session_state.get("lang", "English")
    locale = "km" if lang == "ខ្មែរ" else "en"
    return TRANSLATIONS.get(locale, {}).get(
        key, TRANSLATIONS["en"].get(key, key)
    )


def translate_time_slot(value: str) -> str:
    mapping = {
        "Today Morning": "opt.today_morning",
        "Today Evening": "opt.today_evening",
        "Next-day Morning": "opt.nextday_morning",
        "Next-day Evening": "opt.nextday_evening",
    }
    return t(mapping.get(value, value))


def translate_delivery_method(value: str) -> str:
    mapping = {
        "Delivery": "opt.delivery",
        "Pickup": "opt.pickup",
    }
    return t(mapping.get(value, value))


def translate_preferred_window(value: str) -> str:
    mapping = {
        "Any morning": "opt.any_morning",
        "Any evening": "opt.any_evening",
        "7–8": "opt.window_7_8",
        "8–9": "opt.window_8_9",
        "15–16": "opt.window_15_16",
        "16–17": "opt.window_16_17",
    }
    return t(mapping.get(value, value))


def translate_fish_condition(value: str) -> str:
    mapping = {
        "Live": "opt.live",
        "Chilled": "opt.chilled",
        "Frozen": "opt.frozen",
    }
    return t(mapping.get(value, value))


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




def ensure_state():
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
    if "request_submit_message" not in st.session_state:
        st.session_state.request_submit_message = ""
    if "lang" not in st.session_state:
        st.session_state.lang = "English"


def reset_demo_data():
    for key in ("listings", "requests", "listing_conditions"):
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


def format_status_badge(status):
    color_map = {
        RequestStatus.REQUESTED.value: "#d97706",
        RequestStatus.ACCEPTED.value: "#2563eb",
        RequestStatus.PREPARING.value: "#2563eb",
        RequestStatus.READY.value: "#16a34a",
        RequestStatus.COMPLETED.value: "#6b7280",
    }
    color = color_map.get(status, "#6b7280")
    label = t(f"status.{status}")
    return (
        f"<span style='color:{color};"
        f"border:1px solid {color};"
        "padding:2px 8px;border-radius:10px;font-size:0.85rem;'>"
        f"{label}</span>"
    )


def format_cambodia_time(value):
    if not value:
        return ""
    try:
        dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        dt = dt.replace(tzinfo=timezone.utc).astimezone(ZoneInfo("Asia/Phnom_Penh"))
        return dt.strftime("%Y-%m-%d %H:%M:%S (GMT+7)")
    except ValueError:
        return value




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
                "farm_id": listing["farm_id"],
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
    st.header(t("nav.farmer_listing"))
    st.subheader(t("btn.publish_listing"))
    with st.form("publish_listing"):
        name = st.text_input(t("lbl.farm_name"))
        farm_location_text = st.text_input(
            t("lbl.farm_address_full"),
            placeholder=t("ph.address_example"),
        )
        farm_maps_url = st.text_input(t("lbl.farm_maps_url_optional"))
        farm_contact = st.text_input(t("lbl.contact"))
        fish_name = st.text_input(t("lbl.fish_name_optional"))
        quantity_kg = st.number_input(t("lbl.quantity"), min_value=0.0, step=1.0)
        price_per_kg = st.number_input(t("lbl.price_per_kg"), min_value=0.0, step=0.5)
        time_slots = st.multiselect(
            t("lbl.time_slots"),
            TIME_SLOTS,
            format_func=translate_time_slot,
            placeholder=t("ui.choose_options"),
        )
        delivery_methods = st.multiselect(
            t("lbl.delivery_methods"),
            DELIVERY_METHODS,
            format_func=translate_delivery_method,
            placeholder=t("ui.choose_options"),
        )
        fish_conditions = st.multiselect(
            t("lbl.fish_conditions"),
            FISH_CONDITIONS,
            format_func=translate_fish_condition,
            placeholder=t("ui.choose_options"),
        )
        approx_time = st.text_input(t("lbl.approx_time_optional"))
        submitted = st.form_submit_button(t("btn.publish_listing"))

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
                None,
                None,
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
    if not farmer_listings:
        st.write(t("msg.no_listings"))
        return
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
                today.append(translate_time_slot("Today Morning"))
            if "Evening" in slot:
                today.append(translate_time_slot("Today Evening"))
        if "Next-day" in slot:
            if "Morning" in slot:
                next_day.append(translate_time_slot("Next-day Morning"))
            if "Evening" in slot:
                next_day.append(translate_time_slot("Next-day Evening"))
    parts = []
    if today:
        parts.append(f"Today: {', '.join(dict.fromkeys(today))}")
    if next_day:
        parts.append(f"Next-day: {', '.join(dict.fromkeys(next_day))}")
    return " | ".join(parts)


def average_rating_for_farm(farm_id):
    return avg_rating_for_farm(farm_id)


def format_quantity_kg(value):
    if float(value).is_integer():
        return str(int(value))
    return str(value)


def format_price_per_kg(value):
    if float(value).is_integer():
        return f"${int(value)}/kg"
    return f"${value}/kg"


def render_farm_detail_inline(selected):
    st.write(f"{t('lbl.farm')}: {selected['name']}")
    st.write(f"{t('lbl.address')}: {selected['farm_location_text']}")
    if selected.get("farm_maps_url"):
        st.link_button(t("btn.open_google_maps"), selected["farm_maps_url"])
    if selected.get("farm_contact"):
        st.write(f"{t('lbl.contact')}: {selected['farm_contact']}")

    st.subheader(t("btn.submit_request"))
    with st.form(f"create_request_{selected['id']}"):
        quantity_kg = st.number_input(
            t("lbl.quantity"),
            min_value=0.0,
            step=1.0,
            key=f"quantity_{selected['id']}",
        )
        preferred_size = st.text_input(
            "Preferred size (g per head, optional)",
            placeholder="e.g. 600-800 or 700",
            key=f"preferred_size_{selected['id']}",
        )
        fish_condition = st.selectbox(
            t("lbl.fish_condition"),
            selected["fish_conditions"],
            key=f"fish_condition_{selected['id']}",
            format_func=translate_fish_condition,
        )
        time_slot = st.selectbox(
            t("lbl.time_slot"),
            selected["time_slots"],
            key=f"time_slot_{selected['id']}",
            format_func=translate_time_slot,
        )
        if "Morning" in time_slot:
            window_options = MORNING_WINDOWS
        else:
            window_options = EVENING_WINDOWS
        default_window = "Any morning" if "Morning" in time_slot else "Any evening"
        preferred_time_window = st.selectbox(
            t("lbl.preferred_window"),
            window_options,
            index=window_options.index(default_window),
            key=f"preferred_time_window_{selected['id']}",
            format_func=translate_preferred_window,
        )
        delivery_method = st.selectbox(
            t("lbl.delivery_method"),
            selected["delivery_methods"],
            key=f"delivery_method_{selected['id']}",
            format_func=translate_delivery_method,
        )
        notes = st.text_area(t("lbl.notes"), key=f"notes_{selected['id']}")
        submitted = st.form_submit_button(
            t("btn.submit_request"),
            key=f"submit_{selected['id']}",
        )

    if submitted:
        st.toast("Submitting...")
        restaurant = get_restaurant(1)
        if restaurant is None:
            upsert_restaurant(
                st.session_state.restaurant_name,
                st.session_state.restaurant_location_text,
                None,
                None,
                st.session_state.restaurant_maps_url,
                st.session_state.restaurant_contact.strip(),
            )
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
            try:
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
            except Exception as exc:
                st.error(f"Failed to submit request. {exc}")
                return
            st.session_state.pop("selected_listing_id", None)
            st.session_state.request_submit_message = t("msg.request_sent")
            st.rerun()


def screen_todays_farms(farmer_listings):
    st.header(t("nav.todays_farms"))
    if st.session_state.request_submit_message:
        st.success(st.session_state.request_submit_message)
        st.session_state.request_submit_message = ""
    st.write(t("lbl.farms_available_today"))
    if not farmer_listings:
        st.write(t("msg.no_listings"))
        return
    restaurant = get_restaurant(1)
    restaurant_lat = restaurant.get("lat") if restaurant else None
    restaurant_lng = restaurant.get("lng") if restaurant else None
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
                st.caption(listing["farm_location_text"])
            avg_rating = average_rating_for_farm(listing["farm_id"])
            time_summary = summarise_time_slots(listing["time_slots"])
            fish_name = listing.get("fish_name") or "Fish"
            st.write(
                f"{fish_name} · "
                f"Available: {format_quantity_kg(listing['quantity_kg'])} kg · "
                f"{format_price_per_kg(listing['price_per_kg'])}"
            )
            if time_summary and listing["delivery_methods"]:
                st.write(
                    f"{time_summary} · "
                    f"{' / '.join(map(translate_delivery_method, listing['delivery_methods']))}"
                )
            elif time_summary:
                st.write(time_summary)
            elif listing["delivery_methods"]:
                st.write(" / ".join(map(translate_delivery_method, listing["delivery_methods"])))
            if index in distances:
                st.write(f"📏 {distances[index]:.1f} km")
            if listing.get("farm_maps_url"):
                st.link_button(t("btn.open_farm_map"), listing["farm_maps_url"])
            is_selected = st.session_state.selected_listing_id == listing["id"]
            button_label = (
                t("btn.close") if is_selected else t("btn.order_details")
            )
            if st.button(button_label, key=f"details_{listing['id']}"):
                if is_selected:
                    st.session_state.pop("selected_listing_id", None)
                else:
                    st.session_state.selected_listing_id = listing["id"]
                st.rerun()
            if is_selected:
                with st.expander("Details & Order", expanded=True):
                    render_farm_detail_inline(listing)
            st.divider()


def screen_farmer_actions(requests):
    st.header(t("nav.farmer_actions"))
    requests = list_requests()
    if not requests:
        st.write("No requests yet.")
        return

    for request in requests:
        st.write(
            f"Request {request['id']} for listing {request['listing_id']}"
        )
        st.markdown(
            f"{t('lbl.status')}: {format_status_badge(request['status'])}",
            unsafe_allow_html=True,
        )
        restaurant = get_restaurant(1)
        listing = get_listing(request["listing_id"])
        farm = get_farm(listing["farm_id"]) if listing else None
        restaurant_name = restaurant.get("name") if restaurant else ""
        if restaurant_name:
            st.write(f"{t('lbl.restaurant')}: {restaurant_name}")
            st.write(
                f"{t('lbl.address')}: {restaurant.get('location_text', '')}"
            )
            if restaurant.get("maps_url"):
                st.link_button(
                    t("btn.open_restaurant_map"),
                    restaurant["maps_url"],
                )
        else:
            st.write(t("msg.restaurant_not_set"))
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
        st.write(f"{t('lbl.quantity')}: {request['quantity_kg']}")
        st.write(f"{t('lbl.time_slot')}: {translate_time_slot(request['time_slot'])}")
        st.write(
            f"{t('lbl.delivery_method')}: "
            f"{translate_delivery_method(request['delivery_method'])}"
        )
        if restaurant and restaurant.get("contact"):
            st.write(f"{t('lbl.contact')}: {restaurant['contact']}")
        preferred_time_window = request.get("preferred_time_window") or ""
        if preferred_time_window:
            st.write(
                f"{t('lbl.preferred_window')}: "
                f"{translate_preferred_window(preferred_time_window)}"
            )
        if request["status"] == RequestStatus.REQUESTED.value:
            if st.button(f"{t('btn.accept')} {request['id']}"):
                try:
                    update_request_status(request["id"], RequestStatus.ACCEPTED.value)
                    st.rerun()
                except ValueError:
                    st.error("Unable to accept request.")
        elif request["status"] == RequestStatus.ACCEPTED.value:
            if st.button(f"{t('btn.start_preparing')} {request['id']}"):
                try:
                    update_request_status(
                        request["id"],
                        RequestStatus.PREPARING.value,
                    )
                    st.rerun()
                except ValueError:
                    st.error("Unable to start preparing.")
        elif request["status"] == RequestStatus.PREPARING.value:
            if st.button(f"{t('btn.ready')} {request['id']}"):
                try:
                    update_request_status(request["id"], RequestStatus.READY.value)
                    st.rerun()
                except ValueError:
                    st.error("Unable to mark ready.")
        elif request["status"] == RequestStatus.READY.value:
            if st.button(f"{t('btn.complete')} {request['id']}"):
                try:
                    update_request_status(request["id"], RequestStatus.COMPLETED.value)
                    st.rerun()
                except ValueError:
                    st.error("Unable to complete request.")
        if request["status"] == RequestStatus.COMPLETED.value:
            review = get_review_by_request(request["id"])
            if review:
                stars = "★" * review["stars"] + "☆" * (5 - review["stars"])
                st.write(f"{t('lbl.review')}: {stars}")
                if review.get("comment"):
                    st.write(f"{t('lbl.comment')}: {review['comment']}")
        st.divider()


def screen_request_status(requests):
    st.header(t("nav.request_status"))
    requests = list_requests(restaurant_id=1)
    if not requests:
        st.write("No requests yet.")
        return
    active_statuses = {
        RequestStatus.REQUESTED.value,
        RequestStatus.PREPARING.value,
        RequestStatus.READY.value,
    }
    active_requests = [req for req in requests if req["status"] in active_statuses]
    completed_requests = [
        req for req in requests if req["status"] == RequestStatus.COMPLETED.value
    ]
    for label, bucket in (
        ("Active", active_requests),
        ("Completed", completed_requests),
    ):
        if label == "Completed":
            st.markdown("---")
        if not bucket:
            continue
        for request in bucket:
            with st.container():
                listing = get_listing(request["listing_id"])
                farm = get_farm(listing["farm_id"]) if listing else None
                st.subheader(farm.get("name") if farm else "Unknown farm")
                if listing and listing.get("fish_name"):
                    st.write(f"{t('lbl.fish')}: {listing['fish_name']}")
                st.write(f"{t('lbl.quantity')}: {request['quantity_kg']}")
                st.write(
                    f"{t('lbl.delivery_method')}: "
                    f"{translate_delivery_method(request['delivery_method'])}"
                )
                st.write(
                    f"{t('lbl.time_slot')}: "
                    f"{translate_time_slot(request['time_slot'])}"
                )
                st.markdown(
                    f"{t('lbl.status')}: {format_status_badge(request['status'])}",
                    unsafe_allow_html=True,
                )
                st.write(
                    f"{t('lbl.requested_at')}: "
                    f"{format_cambodia_time(request['created_at'])}"
                )
                st.write(
                    f"{t('lbl.last_updated')}: "
                    f"{format_cambodia_time(request['updated_at'])}"
                )
                if farm and farm.get("contact"):
                        st.write(f"{t('lbl.contact')}: {farm['contact']}")
                if request["status"] == RequestStatus.READY.value:
                    delivery_method = request.get("delivery_method", "")
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
                        st.link_button(t("btn.open_google_maps"), maps_url)
                if request["status"] == RequestStatus.COMPLETED.value:
                    existing_review = get_review_by_request(request["id"])
                    if existing_review:
                        st.write(t("lbl.review"))
                        st.write(f"{t('lbl.stars')}: {existing_review['stars']}")
                        if existing_review.get("comment"):
                            st.write(
                                f"{t('lbl.comment')}: "
                                f"{existing_review['comment']}"
                            )
                    else:
                        st.write(t("btn.leave_review"))
                        with st.form(f"review_{request['id']}"):
                            stars = st.radio(
                                t("lbl.stars"),
                                [1, 2, 3, 4, 5],
                                horizontal=True,
                            )
                            comment = st.text_area(t("lbl.comment"))
                            submitted = st.form_submit_button(t("btn.submit_review"))
                        if submitted:
                            listing_id = request["listing_id"]
                            listing = get_listing(listing_id)
                            farm_id = listing["farm_id"] if listing else None
                            if farm_id is None:
                                st.error("Failed to submit review.")
                                return
                            create_review(
                                request["id"],
                                farm_id,
                                1,
                                stars,
                                comment.strip(),
                            )
                            st.success(t("msg.review_submitted"))
                            st.rerun()
                st.divider()


def screen_monitor():
    st.header(t("nav.operations_monitor"))
    st.write(t("msg.operations_monitor_desc"))
    requests = list_requests()
    if not requests:
        st.write("No requests yet.")
        return
    for request in requests:
        listing = get_listing(request["listing_id"])
        farm = get_farm(listing["farm_id"]) if listing else None
        restaurant = get_restaurant(1)
        with st.container():
            st.markdown(
                f"{t('lbl.status')}: {format_status_badge(request['status'])}",
                unsafe_allow_html=True,
            )
            st.write(
                f"{t('lbl.requested_at')}: "
                f"{format_cambodia_time(request['created_at'])}"
            )
            st.write(
                f"{t('lbl.last_updated')}: "
                f"{format_cambodia_time(request['updated_at'])}"
            )
            st.write(f"Request ID: {request['id']}")
            st.write(f"{t('lbl.farm')}: {farm.get('name') if farm else ''}")
            st.write(
                f"{t('lbl.address')}: "
                f"{farm.get('location_text') if farm else ''}"
            )
            restaurant_name = restaurant.get("name") if restaurant else ""
            if restaurant_name:
                st.write(f"{t('lbl.restaurant')}: {restaurant_name}")
                st.write(
                    f"{t('lbl.address')}: "
                    f"{restaurant.get('location_text', '')}"
                )
            else:
                st.write(t("msg.restaurant_not_set"))
            st.write(
                f"{t('lbl.fish')}: {listing.get('fish_name') if listing else ''}"
            )
            st.write(f"{t('lbl.quantity')}: {request['quantity_kg']}")
            st.write(
                f"{t('lbl.delivery_method')}: "
                f"{translate_delivery_method(request['delivery_method'])}"
            )
            st.write(
                f"{t('lbl.time_slot')}: "
                f"{translate_time_slot(request['time_slot'])}"
            )
            st.write(
                f"{t('lbl.preferred_window')}: "
                f"{translate_preferred_window(request.get('preferred_time_window') or '')}"
            )
            st.write(
                f"{t('lbl.fish_condition')}: "
                f"{translate_fish_condition(request['fish_condition'])}"
            )
            if farm and farm.get("contact"):
                st.write(f"{t('lbl.contact')}: {farm['contact']}")
            if restaurant and restaurant.get("contact"):
                st.write(f"{t('lbl.contact')}: {restaurant['contact']}")
            st.divider()


def screen_restaurant_settings():
    st.header(t("nav.restaurant_settings"))
    with st.form("restaurant_settings"):
        name = st.text_input(t("lbl.restaurant_name"), key="restaurant_name")
        location_text = st.text_input(
            t("lbl.restaurant_address_full"),
            key="restaurant_location_text",
            placeholder=t("ph.address_example"),
        )
        maps_url = st.text_input(
            t("lbl.restaurant_maps_url_optional"),
            key="restaurant_maps_url",
        )
        contact = st.text_input(t("lbl.contact"), key="restaurant_contact")
        submitted = st.form_submit_button(t("btn.save_settings"))
    if submitted:
        if not name.strip() or not location_text.strip():
            st.error("Restaurant name and address are required.")
            return
        existing = get_restaurant(1)
        existing_lat = existing.get("lat") if existing else None
        existing_lng = existing.get("lng") if existing else None
        upsert_restaurant(
            name,
            location_text,
            existing_lat,
            existing_lng,
            maps_url,
            contact.strip(),
        )
        st.success("Restaurant settings saved.")


def main():
    st.title("FishLink MVP")
    ensure_state()
    st.sidebar.selectbox("Language", ["English", "ខ្មែរ"], key="lang")
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
            "nav.farmer_listing",
            "nav.farmer_actions",
            "nav.operations_monitor",
        ]
    else:
        screens = [
            "nav.restaurant_settings",
            "nav.todays_farms",
            "nav.request_status",
            "nav.operations_monitor",
        ]
    if st.session_state.get("nav") not in screens:
        st.session_state.pop("nav", None)
    selection = st.sidebar.radio(
        "Navigate",
        screens,
        key="nav",
        index=0,
        format_func=t,
    )
    if st.sidebar.button(t("btn.switch_role")):
        st.session_state.role = None
        st.session_state.pop("nav", None)
        st.rerun()
    if st.session_state.role == "Restaurant":
        st.sidebar.markdown("### Sort")
        st.sidebar.selectbox(
            "Sort Today’s Farms",
            ["Default", "Distance (if available)"],
            key="sort_option",
            format_func=lambda value: (
                t("sort.default")
                if value == "Default"
                else t("sort.distance_if_available")
            ),
        )
    farmer_listings = build_listings_for_ui()
    st.session_state.listings = farmer_listings
    if st.session_state.demo_reset_message:
        st.sidebar.success("UI state reset.")
        st.session_state.demo_reset_message = False

    if selection == "nav.farmer_listing":
        screen_farmer_listing(farmer_listings)
    elif selection == "nav.restaurant_settings":
        screen_restaurant_settings()
    elif selection == "nav.todays_farms":
        screen_todays_farms(farmer_listings)
    elif selection == "nav.farmer_actions":
        screen_farmer_actions(None)
    elif selection == "nav.request_status":
        screen_request_status(None)
    elif selection == "nav.operations_monitor":
        screen_monitor()

    st.sidebar.markdown("---")
    if st.sidebar.button(t("btn.reset_ui")):
        reset_demo_data()
        st.rerun()
    st.sidebar.caption("Does not delete database records.")


if __name__ == "__main__":
    main()
