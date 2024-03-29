from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="home"),
    path("api/stocks/", views.stocks),
    path("api/test", views.test_end),
    path("api/clean", views.clean_end),
    path(
        "api/stocks/<str:symbol>/",
        views.get_security_info,
        name="security-info",
    ),
]
