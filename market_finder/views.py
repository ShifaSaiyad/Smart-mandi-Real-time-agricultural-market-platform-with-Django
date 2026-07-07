import requests
import json
import os
from datetime import timedelta
from django.shortcuts import render
from django.utils import timezone
from math import radians, cos, sin, asin, sqrt
from .models import MandiLocation
from .data_manager import get_cached_data, get_live_data, get_available_dates


def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return R * c


def home(request):
    city = request.GET.get('city')
    lat, lon = None, None
    if city:
        url = f"https://nominatim.openstreetmap.org/search?format=json&q={city}, Gujarat, India"
        headers = {"User-Agent": "smart-mandi-app"}
        try:
            response = requests.get(url, headers=headers, timeout=10).json()
            if response:
                lat = float(response[0]['lat'])
                lon = float(response[0]['lon'])
        except Exception:
            pass
    return render(request, "market_finder/list.html", {
        "lat": lat, "lon": lon, "city": city, "mandis": []
    })


def get_mandis(request):
    lat = float(request.GET.get("lat"))
    lon = float(request.GET.get("lon"))
    city = request.GET.get("city")
    mandis = []
    for mandi in MandiLocation.objects.all():
        dist = calculate_distance(lat, lon, mandi.latitude, mandi.longitude)
        if dist <= 20:
            mandis.append({
                "name": mandi.market_name,
                "district": mandi.district,
                "state": "Gujarat",
                "distance": round(dist, 2),
                "lat": mandi.latitude,
                "lon": mandi.longitude
            })
    mandis.sort(key=lambda x: x["distance"])
    return render(request, "market_finder/list.html", {
        "mandis": mandis,
        "mandis_json": json.dumps(mandis),
        "lat": lat, "lon": lon, "city": city
    })


def clean_api_name(api_market_name):
    name = api_market_name.lower()
    name = name.replace("apmc", "")
    name = name.split("(")[0]
    return name.strip().strip("-").strip()


def mandi_detail(request, name):
    mode = request.GET.get("mode", "cached")
    date_filter = request.GET.get("date", "today")
    commodity_filter = request.GET.get("commodity", "")
    today = timezone.localdate()
    date_options = [
        {"value": "today", "label": f"Today ({today.strftime('%d/%m/%Y')})"},
        {"value": "yesterday", "label": f"Yesterday ({(today - timedelta(days=1)).strftime('%d/%m/%Y')})"},
        {"value": "2days", "label": f"2 Days Ago ({(today - timedelta(days=2)).strftime('%d/%m/%Y')})"},
    ]

    our_clean = name.split("(")[0].strip().lower()

    if mode == "live":
        # ── LIVE: fetch directly from API ─────────────────────────────
        records, source_label, error_msg = get_live_data(date_filter)  # ✅ FIXED
    else:
        # ── CACHED: read from rolling CSV ─────────────────────────────
        records, source_label, error_msg = get_cached_data(date_filter)

    def name_matches(r):
        api_clean = clean_api_name(r.get("market", ""))
        return (our_clean in api_clean) or (api_clean in our_clean)

    mandi_data = [r for r in records if name_matches(r)]

    if not mandi_data:
        our_words = set(our_clean.split())
        mandi_data = [
            r for r in records
            if our_words & set(clean_api_name(r.get("market", "")).split())
        ]

    all_matched = mandi_data.copy()

    if commodity_filter:
        mandi_data = [
            r for r in mandi_data
            if r.get("commodity", "").lower() == commodity_filter.lower()
        ]

    commodities = sorted(set(r.get("commodity", "") for r in all_matched if r.get("commodity")))

    available_dates = get_available_dates() if mode == "cached" else []

    return render(request, "market_finder/mandi_detail.html", {
        "data": mandi_data,
        "mandi": name,
        "commodities": commodities,
        "total_records": len(records),
        "matched": len(all_matched),
        "mode": mode,
        "date_filter": date_filter,
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
