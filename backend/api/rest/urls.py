from django.urls import path

from . import views

urlpatterns = [
    path("health", views.HealthView.as_view(), name="health"),
    path("info", views.InfoView.as_view(), name="info"),
    path("echo", views.EchoView.as_view(), name="echo"),
]
