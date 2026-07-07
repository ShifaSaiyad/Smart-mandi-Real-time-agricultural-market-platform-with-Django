from django.urls import path

from .views import query_view

app_name = "query_app"

urlpatterns = [
    path("", query_view, name="query"),
]
