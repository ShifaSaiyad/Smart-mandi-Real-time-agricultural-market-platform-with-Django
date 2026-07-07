"""
management/commands/fetch_mandi.py
────────────────────────────────────
Run:  python manage.py fetch_mandi

Use this to manually trigger the daily API download,
or call it from a cron job / Windows Task Scheduler as a backup.
"""

from django.core.management.base import BaseCommand
from market_finder.csv_manager import fetch_and_store


class Command(BaseCommand):
    help = "Fetch today's Gujarat mandi prices from the API and store in rolling CSV"

    def handle(self, *args, **options):
        self.stdout.write("🌾 Fetching mandi data from API...")
        result = fetch_and_store()
        status = result["status"]
        message = result["message"]
        added = result["records_added"]

        if status == "success":
            self.stdout.write(self.style.SUCCESS(f"✅ {message}"))
        elif status == "skipped":
            self.stdout.write(self.style.WARNING(f"⏭  {message}"))
        else:
            self.stdout.write(self.style.ERROR(f"❌ {message}"))

        self.stdout.write(f"   Records added: {added}")