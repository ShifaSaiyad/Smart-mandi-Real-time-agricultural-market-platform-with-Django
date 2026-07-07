import csv
import json
import os
from math import radians, cos, sin, asin, sqrt

import requests
from django.db import DatabaseError
from django.shortcuts import render
from django.utils import timezone

from admin_dashboard.models import FindMandiPageVisit, MandiSearchLog
from .data_manager import (
    get_cached_data,
    get_live_data,
    get_available_dates,
    get_cached_date_options,
)
from .models import MandiLocation

DEFAULT_RADIUS_KM = 20
ALLOWED_RADIUS_OPTIONS = (20, 50)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANDI_CSV_PATH = os.path.join(BASE_DIR, "mandi.csv")


def ensure_session_key(request):
    try:
        if not request.session.session_key:
            request.session.save()
        return request.session.session_key or ""
    except DatabaseError:
        return ""


def get_client_ip(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def log_find_mandi_visit(request):
    try:
        FindMandiPageVisit.objects.create(
            user=request.user if request.user.is_authenticated else None,
            session_key=ensure_session_key(request),
            ip_address=get_client_ip(request),
        )
    except DatabaseError:
        pass


def log_mandi_search(request, *, city="", mandi_name="", search_source="manual", latitude=None, longitude=None, result_count=0):
    try:
        MandiSearchLog.objects.create(
            user=request.user if request.user.is_authenticated else None,
            session_key=ensure_session_key(request),
            city=city or "",
            mandi_name=mandi_name or "",
            search_source=search_source,
            latitude=latitude,
            longitude=longitude,
            result_count=result_count,
        )
    except DatabaseError:
        pass


def calculate_distance(lat1, lon1, lat2, lon2):
    radius = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return radius * c


def iter_mandi_locations():
    try:
        for mandi in MandiLocation.objects.all():
            yield {
                "market_name": mandi.market_name,
                "district": mandi.district,
                "latitude": mandi.latitude,
                "longitude": mandi.longitude,
            }
        return
    except DatabaseError:
        pass

    with open(MANDI_CSV_PATH, "r", encoding="utf-8") as file_obj:
        reader = csv.DictReader(file_obj)
        for row in reader:
            try:
                yield {
                    "market_name": row["GUJARAT MANDI'S MARKET"].strip(),
                    "district": row["District"].strip(),
                    "latitude": float(row["Latitude"]),
                    "longitude": float(row["Longitude"]),
                }
            except (KeyError, TypeError, ValueError):
                continue


def resolve_city_location(city: str):
    query = (city or "").strip().lower()
    if not query:
        return None, None

    locations = list(iter_mandi_locations())

    for mandi in locations:
        if mandi["market_name"].strip().lower() == query:
            return mandi["latitude"], mandi["longitude"]

    district_matches = [
        mandi for mandi in locations
        if mandi["district"].strip().lower() == query
    ]
    if district_matches:
        lat = sum(mandi["latitude"] for mandi in district_matches) / len(district_matches)
        lon = sum(mandi["longitude"] for mandi in district_matches) / len(district_matches)
        return lat, lon

    for mandi in locations:
        market_name = mandi["market_name"].strip().lower()
        if query in market_name or market_name in query:
            return mandi["latitude"], mandi["longitude"]

    return None, None


def home(request):
    return render(request, "market_finder/home.html")


def find_mandi(request):
    city = request.GET.get("city")
    lat, lon = None, None
    if city:
        lat, lon = resolve_city_location(city)
        if lat is None or lon is None:
            url = f"https://nominatim.openstreetmap.org/search?format=json&q={city}, Gujarat, India"
            headers = {"User-Agent": "smart-mandi-app"}
            try:
                response = requests.get(url, headers=headers, timeout=10).json()
                if response:
                    lat = float(response[0]["lat"])
                    lon = float(response[0]["lon"])
            except Exception:
                pass

    return render(request, "market_finder/list.html", {
        "lat": lat,
        "lon": lon,
        "city": city,
        "mandis": [],
        "nearby_radius_km": DEFAULT_RADIUS_KM,
        "radius_options": ALLOWED_RADIUS_OPTIONS,
    })


def get_mandis(request):
    lat = float(request.GET.get("lat"))
    lon = float(request.GET.get("lon"))
    city = request.GET.get("city", "")
    try:
        radius_km = int(request.GET.get("radius", DEFAULT_RADIUS_KM))
    except (TypeError, ValueError):
        radius_km = DEFAULT_RADIUS_KM
    if radius_km not in ALLOWED_RADIUS_OPTIONS:
        radius_km = DEFAULT_RADIUS_KM

    mandis = []
    for mandi in iter_mandi_locations():
        distance = calculate_distance(lat, lon, mandi["latitude"], mandi["longitude"])
        if distance <= radius_km:
            mandis.append({
                "name": mandi["market_name"],
                "district": mandi["district"],
                "state": "Gujarat",
                "distance": round(distance, 2),
                "lat": mandi["latitude"],
                "lon": mandi["longitude"],
            })
    mandis.sort(key=lambda item: item["distance"])

    return render(request, "market_finder/list.html", {
        "mandis": mandis,
        "mandis_json": json.dumps(mandis),
        "lat": lat,
        "lon": lon,
        "city": city,
        "nearby_radius_km": radius_km,
        "radius_options": ALLOWED_RADIUS_OPTIONS,
    })


def clean_api_name(api_market_name):
    name = api_market_name.lower()
    name = name.replace("apmc", "")
    name = name.split("(")[0]
    return name.strip().strip("-").strip()


def mandi_detail(request, name):
    mode = request.GET.get("mode", "cached")
    date_filter = request.GET.get("date", "")
    commodity_filter = request.GET.get("commodity", "")
    today = timezone.localdate()
    date_options = get_cached_date_options(limit=3)

    our_clean = name.split("(")[0].strip().lower()

    if mode == "live":
        records, source_label, error_msg = get_live_data()
    else:
        mode = "cached"
        valid_dates = {option["value"] for option in date_options}
        selected_date = date_filter if date_filter in valid_dates else (date_options[0]["value"] if date_options else "")
        records, source_label, error_msg = get_cached_data(selected_date)

    def name_matches(row):
        api_clean = clean_api_name(row.get("market", ""))
        return (our_clean in api_clean) or (api_clean in our_clean)

    mandi_data = [row for row in records if name_matches(row)]

    if not mandi_data:
        our_words = set(our_clean.split())
        mandi_data = [
            row for row in records
            if our_words & set(clean_api_name(row.get("market", "")).split())
        ]

    all_matched = mandi_data.copy()

    if commodity_filter:
        mandi_data = [
            row for row in mandi_data
            if row.get("commodity", "").lower() == commodity_filter.lower()
        ]

    commodities = sorted({row.get("commodity", "") for row in all_matched if row.get("commodity")})
    available_dates = get_available_dates() if mode == "cached" else []

    return render(request, "market_finder/mandi_detail.html", {
        "data": mandi_data,
        "mandi": name,
        "commodities": commodities,
        "total_records": len(records),
        "matched": len(all_matched),
        "mode": mode,
        "date_filter": selected_date if mode == "cached" else "",
        "commodity_filter": commodity_filter,
        "source_label": source_label,
        "error_msg": error_msg,
        "available_dates": available_dates,
        "date_options": date_options,
        "today_display": today.strftime("%d/%m/%Y"),
    })


def debug_api(request):
    from .data_manager import get_csv_stats

    stats = get_csv_stats()
    return render(request, "market_finder/debug.html", {"stats": stats})
