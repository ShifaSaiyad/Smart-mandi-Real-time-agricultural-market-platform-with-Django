from django.contrib import admin

from .models import UserQuery


@admin.register(UserQuery)
class UserQueryAdmin(admin.ModelAdmin):
    list_display = ("subject", "name", "email", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("subject", "name", "email", "message")

# Register your models here.
