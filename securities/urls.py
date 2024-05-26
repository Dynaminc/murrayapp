from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="home"),
    path("api/managestrike", views.get_strike_breakdown),
    path("api/stocks/", views.stocks),
    path("api/test", views.test_end),
    path("api/confirmstrike", views.confirm_strike),
    path("api/loadstrikes", views.load_strikes),
    
    path("api/load_all_strikes", views.load_all_strikes),
    
    path("api/load_stats", views.load_stats),
    path("api/getchart", views.get_chart),
    path("api/closestrike", views.close_strike),
    
    path("api/add_fund", views.add_fund),
    path("api/load_stats", views.load_stats),
    path("api/load_all_stats", views.load_all_stats),
    
    path("api/load_notifs", views.load_notifications),
    path("api/load_transactions", views.load_transactions),
    path("api/load_all_notifs", views.load_all_notifications),
    path("api/load_all_transactions", views.load_all_transactions),
    
    path("api/testit", views.trigger_store),
    path("api/check", views.trigger_lens),
    path("api/earnings", views.ManageEarning),
    
   
    
    path("api/load_percent", views.cronat),
    path("api/clean", views.clean_end),
    path("api/missingdata", views.load_missing),
    path("api/cronny", views.update_striker),
    path(
        "api/stocks/<str:symbol>/",
        views.get_security_info,
        name="security-info",
    ),
]
