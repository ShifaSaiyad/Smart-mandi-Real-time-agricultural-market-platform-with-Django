import os
import sys
import django
import csv

sys.path.append(os.getcwd())

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_mandi.settings')
django.setup()

from market_finder.models import MandiLocation


def load_data():
    file_path = 'mandi.csv'

    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found!")
        return

    print("🧹 Cleaning old database...")
    MandiLocation.objects.all().delete()

    with open(file_path, mode='r', encoding='UTF-8') as f:
        reader = csv.DictReader(f)   # ✅ IMPORTANT CHANGE

        count = 0

        for row in reader:
            try:
                MandiLocation.objects.create(
                    market_name=row["GUJARAT MANDI'S MARKET"].strip(),
                    district=row["District"].strip(),
                    state="Gujarat",   # ✅ ADD THIS LINE
                    latitude=float(row["Latitude"]),
                    longitude=float(row["Longitude"])
                    )
                count += 1
            except Exception as e:
                print("⚠️ Skipped row:", row)
                print("Error:", e)

        print(f"✅ Success! {count} mandis are now in your database.")


if __name__ == "__main__":
    load_data()