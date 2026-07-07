from django.contrib import admin

from .models import FindMandiPageVisit, MandiSearchLog


@admin.register(FindMandiPageVisit)
class FindMandiPageVisitAdmin(admin.ModelAdmin):
    list_display = ("page_name", "user", "ip_address", "visited_at")
    search_fields = ("page_name", "user__username", "session_key", "ip_address")
    list_filter = ("page_name", "visited_at")


@admin.register(MandiSearchLog)
class MandiSearchLogAdmin(admin.ModelAdmin):
    list_display = ("city", "mandi_name", "search_source", "result_count", "user", "searched_at")
    search_fields = ("city", "mandi_name", "user__username", "session_key")
    list_filter = ("search_source", "searched_at")

