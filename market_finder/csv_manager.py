"""
csv_manager.py
──────────────
Handles all CSV caching logic for Smart Mandi:
  • fetch_and_store()   – download today's Gujarat data from API → append to rolling CSV
  • get_cached_data()   – read records from CSV for a given date label
  • get_live_data()     – fetch records directly from API right now (no cache)
  • get_available_dates() – return list of date strings present in CSV
  • get_csv_stats()     – diagnostic info for the debug page
  • purge_old_rows()    – keep only last 7 days of data in CSV
"""

import os
import csv
import requests
from datetime import datetime, timedelta, date

# ── Config ────────────────────────────────────────────────────────────────────
API_KEY = "579b464db66ec23bdd0000015e2dedda167c4e717ac9c50d2bc3c2a0"
API_URL = (
    "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
    "?api-key={api_key}&format=json&limit={limit}&offset={offset}"
    "&filters[state.keyword]=Gujarat"
)

# Path to rolling CSV  (lives next to manage.py)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, "mandi_cache.csv")

# Columns we store in the CSV
CSV_COLUMNS = [
    "cached_date",      # date we downloaded this row  (YYYY-MM-DD)
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

KEEP_DAYS = 7           # rolling window
FETCH_LIMIT = 100       # records per API page


# ── Internal helpers ──────────────────────────────────────────────────────────

def _today_str() -> str:
    return date.today().isoformat()          # "2026-04-15"


def _date_label_to_str(label: str) -> str:
    """Convert 'today' / 'yesterday' / '2days' → 'YYYY-MM-DD'."""
    today = date.today()
    if label == "yesterday":
        return (today - timedelta(days=1)).isoformat()
    elif label == "2days":
        return (today - timedelta(days=2)).isoformat()
    else:                                    # default: today
        return today.isoformat()


def _fetch_from_api(timeout: int = 15):
    """
    Pull ALL Gujarat records from the API (paginated).
    Returns (list_of_dicts, error_message_or_None).
    """
    all_records = []
    offset = 0
    error = None

    while True:
        url = API_URL.format(api_key=API_KEY, limit=FETCH_LIMIT, offset=offset)
        try:
            resp = requests.get(url, timeout=timeout)
            data = resp.json()
            records = data.get("records", [])
            if not records:
                break
            all_records.extend(records)
            if len(records) < FETCH_LIMIT:
                break
            offset += FETCH_LIMIT
            if offset > 50_000:         # safety cap
                break
        except Exception as e:
            error = str(e)
            break

    return all_records, error


def _ensure_csv_exists():
    """Create CSV with header row if it does not exist yet."""
    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
            writer.writeheader()


def _read_all_rows() -> list:
    """Read every row from the CSV into a list of dicts."""
    _ensure_csv_exists()
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def _write_all_rows(rows: list):
    """Overwrite CSV with the given rows (preserves header)."""
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


# ── Public API ────────────────────────────────────────────────────────────────

def purge_old_rows():
    """
    Remove rows whose cached_date is older than KEEP_DAYS days.
    Called automatically after each fetch.
    """
    cutoff = (date.today() - timedelta(days=KEEP_DAYS - 1)).isoformat()
    rows = _read_all_rows()
    kept = [r for r in rows if r.get("cached_date", "") >= cutoff]
    _write_all_rows(kept)
    removed = len(rows) - len(kept)
    return removed


def fetch_and_store() -> dict:
    """
    Download today's Gujarat data from the API and append to CSV.
    Skips if today's data is already cached.
    Returns a status dict.
    """
    today = _today_str()

    # Check if today's data already exists
    existing = _read_all_rows()
    if any(r.get("cached_date") == today for r in existing):
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

    # Append new rows
    new_rows = []
    for r in records:
        new_rows.append({
            "cached_date": today,
            "state":        r.get("state", "Gujarat"),
            "district":     r.get("district", ""),
            "market":       r.get("market", ""),
            "commodity":    r.get("commodity", ""),
            "variety":      r.get("variety", ""),
            "grade":        r.get("grade", ""),
            "arrival_date": r.get("arrival_date", ""),
            "min_price":    r.get("min_price", ""),
            "max_price":    r.get("max_price", ""),
            "modal_price":  r.get("modal_price", ""),
        })

    _ensure_csv_exists()
    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writerows(new_rows)

    removed = purge_old_rows()

    return {
        "status": "success",
        "message": f"Fetched {len(new_rows)} records for {today}. Purged {removed} old rows.",
        "records_added": len(new_rows),
    }


def get_cached_data(date_label: str = "today"):
    """
    Return (records_list, source_label, error_msg) from local CSV
    for the given date label ('today', 'yesterday', '2days').
    records_list items are plain dicts compatible with the template.
    """
    target_date = _date_label_to_str(date_label)
    rows = _read_all_rows()
    matched = [r for r in rows if r.get("cached_date") == target_date]

    label_map = {
        "today": "Today",
        "yesterday": "Yesterday",
        "2days": "2 Days Ago",
    }
    source_label = f"📂 Cached — {label_map.get(date_label, date_label)} ({target_date})"
    error_msg = None

    if not matched:
        error_msg = (
            f"No cached data found for {target_date}. "
            "Run the daily fetch or choose a different date."
        )

    return matched, source_label, error_msg

def get_live_data(date_label: str = "today"):
    """
    Fetch records directly from the API right now (no CSV).
    Returns (records_list, source_label, error_msg).
    """
    records, error = _fetch_from_api(timeout=20)
    source_label = f"⚡ Live — fetched at {datetime.now().strftime('%H:%M:%S')}"
    error_msg = error if not records else None

    # ── Normalize field names (same as CSV) ──────────────────────────
    normalized = []
    for r in records:
        normalized.append({
            "cached_date":  _today_str(),
            "state":        r.get("state", "Gujarat"),
            "district":     r.get("district", ""),
            "market":       r.get("market", ""),
            "commodity":    r.get("commodity", ""),
            "variety":      r.get("variety", ""),
            "grade":        r.get("grade", ""),
            "arrival_date": r.get("arrival_date", ""),
            "min_price":    r.get("min_price", ""),
            "max_price":    r.get("max_price", ""),
            "modal_price":  r.get("modal_price", ""),
        })

    return normalized, source_label, error_msg

def get_available_dates() -> list:
    """
    Return sorted list of unique cached_date strings in the CSV
    (most recent first).
    """
    rows = _read_all_rows()
    dates = sorted(set(r.get("cached_date", "") for r in rows if r.get("cached_date")), reverse=True)
    return dates


def get_csv_stats() -> dict:
    """Return diagnostic info for the debug page."""
    rows = _read_all_rows()
    dates = sorted(set(r.get("cached_date", "") for r in rows if r.get("cached_date")))
    markets = sorted(set(r.get("market", "") for r in rows if r.get("market")))
    file_size_kb = round(os.path.getsize(CSV_PATH) / 1024, 1) if os.path.exists(CSV_PATH) else 0
    return {
        "total_rows": len(rows),
        "dates": dates,
        "markets": markets[:50],       # cap at 50 for display
        "file_size_kb": file_size_kb,
        "csv_path": CSV_PATH,
        "keep_days": KEEP_DAYS,
    }