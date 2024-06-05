from django.http import JsonResponse
from .models import Profile
from django.utils import timezone
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed

# from rest_framework_simplejwt.tokens import AccessToken


class JWTMiddleware(JWTAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return None
        auth_method, jwt_token = auth_header.split(' ')
        
        profile_instance = Profile.objects.filter(token=jwt_token).first()
        
        if not profile_instance:
            return JsonResponse({'error': 'Authentication failed, no profile'}, status=401)
        
        if profile_instance:
            if timezone.now() > profile_instance.token_expires:
                return JsonResponse({'error': 'Authentication failed, expired'}, status=401)        
            
        request.user = profile_instance.user
    
        return request.user, jwt_token
        