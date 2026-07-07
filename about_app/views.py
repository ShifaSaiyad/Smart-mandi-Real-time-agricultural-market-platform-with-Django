from django.shortcuts import render

from .models import AboutContent


def about_view(request):
    about_content = AboutContent.objects.first() or AboutContent(
        title="About Smart Mandi",
        hero_text="Smart Mandi helps farmers, traders, and buyers quickly discover mandi locations and track price data in a simple dashboard.",
        mission="Our mission is to make agricultural market information easier to access, easier to understand, and more useful in day-to-day decisions.",
        vision="Our vision is a modern mandi discovery platform with transparent data, easy communication, and a smooth user experience for every visitor.",
        highlight_one="Nearby mandi discovery with map support",
        highlight_two="User accounts for registration and profile management",
        highlight_three="Feedback and query collection directly inside the platform",
    )
    return render(request, "about_app/about.html", {"about_content": about_content})

# Create your views here.
