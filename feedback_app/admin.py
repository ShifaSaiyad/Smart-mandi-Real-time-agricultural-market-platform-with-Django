from django.contrib import admin

from .models import Feedback


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "rating", "created_at")
    search_fields = ("name", "email", "message")

# Register your models here.
