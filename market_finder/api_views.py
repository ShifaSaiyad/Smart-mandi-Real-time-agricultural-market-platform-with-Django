"""
api_views.py
────────────
Simple JSON endpoint to manually trigger a CSV fetch from the browser or curl.

GET /fetch-now/  →  { "status": "...", "message": "...", "records_added": N }
"""

import json
from django.http import JsonResponse
from .data_manager import fetch_and_store


def fetch_now_view(request):
    result = fetch_and_store()
    return JsonResponse(result)
