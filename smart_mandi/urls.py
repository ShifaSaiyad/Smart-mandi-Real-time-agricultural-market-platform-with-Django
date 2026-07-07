from django.contrib import admin
from django.urls import include, path
from market_finder import views_ready as views
from market_finder.api_views import fetch_now_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('admin-dashboard/', include('admin_dashboard.urls')),
    path('users/', include('user_app.urls')),
    path('about/', include('about_app.urls')),
    path('feedback/', include('feedback_app.urls')),
    path('queries/', include('query_app.urls')),
    path('', views.home, name='home'),
    path('find_mandi/', views.find_mandi, name='find_mandi'),
    path('mandis/', views.get_mandis, name='get_mandis'),
    path('mandi/<str:name>/', views.mandi_detail, name='mandi_detail'),
    path('debug/', views.debug_api, name='debug_api'),

    # Manual trigger: GET /fetch-now/ → runs fetch_and_store() immediately
    path('fetch-now/', fetch_now_view, name='fetch_now'),
]
