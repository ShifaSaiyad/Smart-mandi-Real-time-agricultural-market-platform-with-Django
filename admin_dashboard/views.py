from datetime import timedelta

from django.contrib.auth.models import User
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Count
from django.shortcuts import render
from django.utils import timezone

from feedback_app.models import Feedback
from query_app.models import UserQuery

from .models import FindMandiPageVisit, MandiSearchLog

FILTER_OPTIONS = {
    "today": {"label": "Today", "days": 1},
    "last_7_days": {"label": "Last 7 Days", "days": 7},
    "last_month": {"label": "Last Month", "days": 30},
    "last_year": {"label": "Last Year", "days": 365},
}


def staff_required(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


def get_period_start(filter_key):
    selected = FILTER_OPTIONS.get(filter_key, FILTER_OPTIONS["today"])
    return timezone.now() - timedelta(days=selected["days"])


def dashboard_view(request):
    selected_filter = request.GET.get("range", "today")
    if selected_filter not in FILTER_OPTIONS:
        selected_filter = "today"

    period_start = get_period_start(selected_filter)

    feedback_qs = Feedback.objects.order_by("-created_at")
    query_qs = UserQuery.objects.order_by("-created_at")
    visit_qs = FindMandiPageVisit.objects.filter(visited_at__gte=period_start)
    search_qs = MandiSearchLog.objects.filter(searched_at__gte=period_start)

    status_summary = (
        query_qs.values("status")
        .annotate(total=Count("id"))
        .order_by("status")
    )

    top_searches = (
        search_qs.exclude(city="")
        .values("city")
        .annotate(total=Count("id"))
        .order_by("-total", "city")[:10]
    )

    recent_searches = search_qs[:12]

    context = {
        "selected_filter": selected_filter,
        "filter_choices": [(key, value["label"]) for key, value in FILTER_OPTIONS.items()],
        "period_label": FILTER_OPTIONS[selected_filter]["label"],
        "period_start": period_start,
        "total_feedback": feedback_qs.count(),
        "total_queries": query_qs.count(),
        "total_users": User.objects.count(),
        "find_mandi_page_views": visit_qs.count(),
        "mandi_search_count": search_qs.count(),
        "feedback_list": feedback_qs,
        "query_list": query_qs,
        "recent_searches": recent_searches,
        "top_searches": top_searches,
        "status_summary": status_summary,
    }
    return render(request, "admin_dashboard/dashboard.html", context)


dashboard_view = user_passes_test(staff_required)(dashboard_view)
