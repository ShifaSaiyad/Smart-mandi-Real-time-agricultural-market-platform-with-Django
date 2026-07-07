from django.urls import path

from .views import feedback_view

app_name = "feedback_app"

urlpatterns = [
    path("", feedback_view, name="feedback"),
]
