from django.urls import path, include
from . import views
from .views import CustomTokenRefreshView
from rest_framework_simplejwt import views as jwt_views

urlpatterns = [
    # path('auth/refresh_token', CustomTokenRefreshView.as_view(), name='token_refresh'),
    # path('auth/refresh_token', jwt_views.TokenRefreshView.as_view(), name='token_refresh'),# refreshes token
    path('refresh-token/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('auth/sign_in',  views.sign_in),
    path('auth/get_auth_info',  views.get_auth_info),
    path('auth/get_all_users',  views.get_all_users),
    path('auth/create_user_by_admin',  views.create_user_by_admin),
    path('auth/update_user_by_admin',  views.update_user_by_admin),
    path('auth/delete_user_by_admin',  views.delete_user_by_admin),
]