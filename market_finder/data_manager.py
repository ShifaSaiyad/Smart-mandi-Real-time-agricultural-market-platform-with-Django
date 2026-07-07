"""Handles CSV caching and live API fetch logic for Smart Mandi."""

import csv
import os
from datetime import datetime, timedelta
from urllib.parse import urlparse

import requests
from django.utils import timezone

API_KEY = "579b464db66ec23bdd0000015e2dedda167c4e717ac9c50d2bc3c2a0"
API_URL = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
API_HEADERS = {
    "Accept": "application/json",
    "User-Agent": "SmartMandi/1.0 (+https://data.gov.in)",
}

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, "mandi_cache.csv")

CSV_COLUMNS = [
    "cached_date",
    "state",
    "district",
    "market",
    "commodity",
    "variety",
    "grade",
    "arrival_date",
    "min_price",
    "max_price",
    "modal_price",
]

KEEP_DAYS = 7
FETCH_LIMIT = 100
DISPLAY_CACHE_DAYS = 3
MAX_API_PAGES = 80


def _local_today():
    return timezone.localdate()


def _today_str() -> str:
    return _local_today().isoformat()


def _format_snapshot_label(snapshot_date: str) -> str:
    try:
        parsed = datetime.strptime(snapshot_date, "%Y-%m-%d").date()
    except ValueError:
        return snapshot_date

    today = _local_today()
    if parsed == today:
        prefix = "Today Snapshot"
    elif parsed == today - timedelta(days=1):
        prefix = "Yesterday Snapshot"
    else:
        prefix = "Snapshot"
    return f"{prefix} ({parsed.strftime('%d/%m/%Y')})"


def get_cached_date_options(limit: int = DISPLAY_CACHE_DAYS) -> list:
    rows = _read_all_rows()
    snapshot_dates = sorted(
        {row.get("cached_date", "") for row in rows if row.get("cached_date")},
        reverse=True,
    )[:limit]
    return [{"value": snapshot_date, "label": _format_snapshot_label(snapshot_date)} for snapshot_date in snapshot_dates]


def get_live_date_options(limit: int = 7) -> list:
    today = _local_today()
    options = []
    for offset in range(limit):
        target = today - timedelta(days=offset)
        value = target.strftime("%d/%m/%Y")
        if offset == 0:
            label = f"Today Market Date ({value})"
        elif offset == 1:
            label = f"Yesterday Market Date ({value})"
        else:
            label = f"Market Date ({value})"
        options.append({"value": value, "label": label})
    return options


def _fetch_from_api(timeout: int = 15):
    all_records = []
    offset = 0
    error = None
    session = requests.Session()

    while True:
        params = {
            "api-key": API_KEY,
            "format": "json",
            "limit": FETCH_LIMIT,
            "offset": offset,
            "filters[state]": "Gujarat",
        }
        try:
            resp = session.get(API_URL, params=params, headers=API_HEADERS, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
            records = data.get("records", [])
            if not records:
                break
            all_records.extend(records)
            if len(records) < FETCH_LIMIT:
                break
            offset += FETCH_LIMIT
            if offset >= FETCH_LIMIT * MAX_API_PAGES:
                break
        except Exception as exc:
            parsed = urlparse(API_URL)
            error = f"{parsed.netloc} did not respond correctly: {exc}"
            break

    return all_records, error


def _ensure_csv_exists():
    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, "w", newline="", encoding="utf-8") as file_obj:
            writer = csv.DictWriter(file_obj, fieldnames=CSV_COLUMNS)
            writer.writeheader()


def _read_all_rows() -> list:
    _ensure_csv_exists()
    with open(CSV_PATH, "r", encoding="utf-8") as file_obj:
        return list(csv.DictReader(file_obj))


def _write_all_rows(rows: list):
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def _latest_arrival_date(records: list) -> str:
    dates = sorted({row.get("arrival_date", "") for row in records if row.get("arrival_date")})
    return dates[-1] if dates else ""


def _latest_cached_date(records: list) -> str:
    dates = sorted({row.get("cached_date", "") for row in records if row.get("cached_date")})
    return dates[-1] if dates else ""


def _latest_snapshot_for_arrival(records: list, arrival_date: str) -> str:
    snapshots = sorted({
        row.get("cached_date", "")
        for row in records
        if row.get("arrival_date") == arrival_date and row.get("cached_date")
    })
    return snapshots[-1] if snapshots else ""


def _normalize_records(records: list) -> list:
    today = _today_str()
    normalized = []
    for row in records:
        normalized.append({
            "cached_date": today,
            "state": row.get("state", "Gujarat"),
            "district": row.get("district", ""),
            "market": row.get("market", ""),
            "commodity": row.get("commodity", ""),
            "variety": row.get("variety", ""),
            "grade": row.get("grade", ""),
            "arrival_date": row.get("arrival_date", ""),
            "min_price": row.get("min_price", ""),
            "max_price": row.get("max_price", ""),
            "modal_price": row.get("modal_price", ""),
        })
    return normalized


def purge_old_rows():
    cutoff = (_local_today() - timedelta(days=KEEP_DAYS - 1)).isoformat()
    rows = _read_all_rows()
    kept = [row for row in rows if row.get("cached_date", "") >= cutoff]
    _write_all_rows(kept)
    return len(rows) - len(kept)


def fetch_and_store() -> dict:
    today = _today_str()
    existing = _read_all_rows()
    if any(row.get("cached_date") == today for row in existing):
        return {
            "status": "skipped",
            "message": f"Today's data ({today}) already cached.",
            "records_added": 0,
        }

    records, error = _fetch_from_api()
    if error and not records:
        return {
            "status": "error",
            "message": f"API fetch failed: {error}",
            "records_added": 0,
        }

    new_rows = _normalize_records(records)
    _ensure_csv_exists()
    with open(CSV_PATH, "a", newline="", encoding="utf-8") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=CSV_COLUMNS)
        writer.writerows(new_rows)

    return {
        "status": "success",
        "message": f"Fetched {len(new_rows)} records for {today}. Existing CSV history was kept.",
        "records_added": len(new_rows),
    }


def get_cached_data(snapshot_date: str | None = None):
    rows = _read_all_rows()
    snapshot_dates = sorted(
        {row.get("cached_date", "") for row in rows if row.get("cached_date")},
        reverse=True,
    )
    available_dates = snapshot_dates[:DISPLAY_CACHE_DAYS]
    selected_snapshot = snapshot_date if snapshot_date in available_dates else (available_dates[0] if available_dates else "")
    matched = [row for row in rows if row.get("cached_date") == selected_snapshot]

    if matched:
        latest_market_date = _latest_arrival_date(matched)
        source_label = (
            f"Showing cached data from saved date {selected_snapshot}."
            f" Latest market date inside the cache is {latest_market_date or 'not available'}."
        )
    else:
        source_label = "No cached mandi data found."

    error_msg = None
    if not matched:
        error_msg = f"No cached data found. Available saved days: {', '.join(snapshot_dates) if snapshot_dates else 'none'}."

    return matched, source_label, error_msg


def get_live_data():
    records, error = _fetch_from_api(timeout=20)
    normalized = _normalize_records(records)
    if error and not normalized:
        return [], "Live API request failed.", "Live API could not be reached right now. Please try again after some time or use cached data."

    latest_arrival = _latest_arrival_date(normalized)
    fetched_at = timezone.localtime().strftime("%d/%m/%Y %H:%M:%S")
    source_label = f"Live API fetched at {fetched_at}. Latest market date in this response is {latest_arrival or 'not available'}."
    error_msg = error if not normalized else None

    if not normalized and not error_msg:
        error_msg = "The live API returned no Gujarat mandi records."

    return normalized, source_label, error_msg


def get_available_dates() -> list:
    rows = _read_all_rows()
    return sorted({row.get("cached_date", "") for row in rows if row.get("cached_date")}, reverse=True)


def get_csv_stats() -> dict:
    rows = _read_all_rows()
    cached_dates = sorted({row.get("cached_date", "") for row in rows if row.get("cached_date")})
    arrival_dates = sorted({row.get("arrival_date", "") for row in rows if row.get("arrival_date")})
    markets = sorted({row.get("market", "") for row in rows if row.get("market")})
    file_size_kb = round(os.path.getsize(CSV_PATH) / 1024, 1) if os.path.exists(CSV_PATH) else 0
    return {
        "total_rows": len(rows),
        "dates": cached_dates,
        "arrival_dates": arrival_dates,
        "markets": markets[:50],
        "file_size_kb": file_size_kb,
        "csv_path": CSV_PATH,
        "keep_days": KEEP_DAYS,
        "latest_snapshot": _latest_cached_date(rows),
        "latest_arrival": _latest_arrival_date(rows),
    }
