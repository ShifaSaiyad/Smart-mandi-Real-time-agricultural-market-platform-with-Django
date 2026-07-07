from django.conf import settings
from django.db import models


class FindMandiPageVisit(models.Model):
    page_name = models.CharField(max_length=100, default="find_mandi")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="find_mandi_page_visits",
    )
    session_key = models.CharField(max_length=40, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    visited_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-visited_at"]

    def __str__(self):
        return f"{self.page_name} visit at {self.visited_at:%Y-%m-%d %H:%M}"


class MandiSearchLog(models.Model):
    SEARCH_SOURCE_CHOICES = [
        ("city", "City"),
        ("gps", "GPS"),
        ("manual", "Manual"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="mandi_search_logs",
    )
    session_key = models.CharField(max_length=40, blank=True)
    city = models.CharField(max_length=150, blank=True)
    mandi_name = models.CharField(max_length=255, blank=True)
    search_source = models.CharField(max_length=20, choices=SEARCH_SOURCE_CHOICES, default="manual")
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    result_count = models.PositiveIntegerField(default=0)
    searched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-searched_at"]

    def __str__(self):
        label = self.city or self.mandi_name or "Search"
        return f"{label} ({self.search_source})"

