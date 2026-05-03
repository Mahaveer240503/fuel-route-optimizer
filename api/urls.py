from django.urls import path
from .views import RouteView

app_name = "api"

urlpatterns = [
    path("route/", RouteView.as_view(), name="route"),
]
