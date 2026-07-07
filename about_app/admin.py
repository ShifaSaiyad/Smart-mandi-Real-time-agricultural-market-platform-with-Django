from django.contrib import admin

from .models import AboutContent


@admin.register(AboutContent)
class AboutContentAdmin(admin.ModelAdmin):
    list_display = ("title", "updated_at")

# Register your models here.
