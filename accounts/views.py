from django.shortcuts import render
from django.contrib.auth.models import User
from rest_framework.decorators import api_view
from django.http import JsonResponse
from rest_framework import status
from .serializer import *
from .models import Profile
from django.contrib.auth import authenticate, login, logout
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from datetime import timedelta
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.response import Response
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from django.utils import timezone


class CustomTokenRefreshView(TokenRefreshView):
    def get_token(self, serializer):
        refresh = serializer.validated_data['refresh']
        token = RefreshToken(refresh)

        # Set the expiration time for the new token
        token.set_exp(timedelta(days=2))  # Set to expire in 2 days

        return token
    
# class CustomTokenRefreshSerializer(TokenRefreshSerializer):
#     def validate(self, attrs):
#         data = super().validate(attrs)
#         data['refresh'] = str(self.context['request'].META.get('HTTP_AUTHORIZATION', ''))
#         return data
    
# Create your views here.

# make user creation only possible by admin
# show all users created by admin
# admin signup and users sign up

# class CustomTokenRefreshView(TokenRefreshView):
#     serializer_class = CustomTokenRefreshSerializer
#     def post(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)

#         try:
#             serializer.is_valid(raise_exception=True)
#         except Exception as e:
#             return Response({"error": str(e)}, status=400)

#         data = serializer.validated_data
#         refresh = data['refresh']

#         # Decode the refresh token to get its payload
#         payload = RefreshToken(refresh).payload

#         # Here you can add any additional validation if needed
#         # For example, check if the refresh token is valid or has expired

#         # Return the same refresh token
#         return Response({"refresh": refresh}, status=200)

@api_view(['GET'])
def get_auth_info(request):
    print('reqeust')
    print(request.user)
    # Verifies the authentication info using jwt_token
    # try:
    if request.user:
        user_data = {}
        user = UserSerializer(request.user).data
        profile_instance = Profile.objects.filter(user=request.user).first()
        content = {'user':user, 'profile': ProfileSerializer(profile_instance).data }
        for item in  content.values():
            for key, value in item.items():
                user_data[key] = value
            
        return JsonResponse({'data':user_data}, status=status.HTTP_200_OK)
        
    else:
        return JsonResponse({'message': f'Error: user with token not found, refresh', 'status': 400}, status=status.HTTP_400_BAD_REQUEST)
    # except Exception as e:
    #     # Handle unexpected errors and return a JSON response
    #     return JsonResponse({'message': f'An unexpected error occurred: {e}', 'status': 400}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET','POST'])
def sign_in(request):
    serializer = SignInSerializer(data=request.POST)
    if serializer.is_valid():
        serialized = serializer.data
        username = serialized['username'].lower()
        password = serialized['password']  
        authenticated_user = authenticate(request, username=username, password=password)      
        if authenticated_user:
            # Logs in the user and generates JWT tokens.
            login(request, authenticated_user)
            
            expiration_time = timezone.now() + timezone.timedelta(days=2)
            expiration_timestamp = int(expiration_time.timestamp())
            
            refresh_token = RefreshToken.for_user(authenticated_user)
            refresh_token.set_exp(expiration_timestamp)
            access_token = refresh_token.access_token
            access_token.set_exp(expiration_timestamp)
            
            return JsonResponse({'message': 'Welcome back! You are now logged in.',
                                    'response': {                     
                                        'jwt_token': str(access_token),
                                        'refresh_token': str(refresh_token)
                                        }, 
                                    'status': 200},
                                status=status.HTTP_200_OK)
        else:
            return JsonResponse({'message': 'Login failed', 'status': 400}, status=status.HTTP_400_BAD_REQUEST)            
        
    return JsonResponse({'message': f'Serailizer Error {serializer.errors}', 'status': 400}, status=status.HTTP_400_BAD_REQUEST)            

@api_view(['GET','POST'])        
def get_all_users(request):
    try: 
        if not request.user.is_superuser:
            return JsonResponse({'message': 'You do not have the permission to create a user'}, status=status.HTTP_200_OK)
        else:
            final_users_data = extract_all_user()
            return JsonResponse({'data':final_users_data}, status=status.HTTP_200_OK)
        
    except Exception as e:
        # Handle unexpected errors and return a JSON response
        return JsonResponse({'message': f'An unexpected error occurred: {e}', 'status': 400}, status=status.HTTP_400_BAD_REQUEST)
    
def extract_all_user():
    users_data = [{'user':UserSerializer(user_instance).data, 'profile': ProfileSerializer(Profile.objects.filter(user=user_instance).first()).data } for user_instance in User.objects.all()]
    final_users_data = []
    for item in users_data:
        full_dict = {}
        for content in  item.values():
            for key, value in content.items():
                full_dict[key] = value
        final_users_data.append(full_dict)

    return final_users_data

@api_view(['GET','POST'])    
def create_user_by_admin(request):   
    try: 
        if not request.user.is_superuser:
            return JsonResponse({'message': 'You do not have the permission to create a user'}, status=status.HTTP_200_OK)
        
        serializer = CreateUserSerializer(data= request.POST)
        if not serializer.is_valid():
            return JsonResponse({'message': f'Please add the field, {serializer.errors}', 'status': 400}, status=status.HTTP_400_BAD_REQUEST)

        serialized = serializer.data
        
        username = serialized['username'].lower()
        password = serialized['password']  
        first_name  = serialized['first_name']  
        last_name  = serialized['last_name']  
        portfolio  = int(serialized['portfolio'])
        margin  = int(serialized['margin'])
        
        user = User.objects.create_user(username=username, password=password)
        user.set_password(password)
        user.save()

        profile_instance = Profile.objects.create(user=user, first_name=first_name, last_name=last_name, size = portfolio, margin= margin, balance = portfolio)
        profile_instance.save()
        
        users_data = extract_all_user()
        
        return JsonResponse({'message': 'User Creation successful!','data':users_data, 'status': 200}, status=status.HTTP_200_OK)
    
    except Exception as e:
        # Handle unexpected errors and return a JSON response
        return JsonResponse({'message': f'An unexpected error occurred: {e}', 'status': 400}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET','POST'])    
def delete_user_by_admin(request):
    try: 
        if not request.user.is_superuser:
            return JsonResponse({'message': 'You do not have the permission to delete a user'}, status=status.HTTP_200_OK)
        
        serializer = IdSerializer(data= request.POST)
        if not serializer.is_valid():
            return JsonResponse({'message': f'Please add the field, {serializer.errors}', 'status': 400}, status=status.HTTP_400_BAD_REQUEST)
        
        serialized = serializer.data
        id = int(serialized['id'])
        user_instance = User.objects.filter(pk=id).first()
        
        if not user_instance:
            return JsonResponse({'message': f'User not found', 'status': 400}, status=status.HTTP_400_BAD_REQUEST)
        
        profile_instance = Profile.objects.filter(user=user_instance).first()
        if profile_instance:
            profile_instance.delete()
            # return JsonResponse({'message': f'Profile not found', 'status': 400}, status=status.HTTP_400_BAD_REQUEST)        
        
        
        user_instance.delete()
        
        
        users_data = extract_all_user()
        
        return JsonResponse({'message': 'User Deletoin successful!','data':users_data, 'status': 200}, status=status.HTTP_200_OK)            
    except Exception as e:
        return  JsonResponse({'message': f'An unexpected error occurred: {e}', 'status': 400}, status=status.HTTP_400_BAD_REQUEST)
    
    
@api_view(['GET','POST'])    
def update_user_by_admin(request):
    try: 
        if not request.user.is_superuser:
            return JsonResponse({'message': 'You do not have the permission to create a user'}, status=status.HTTP_200_OK)
        
        serializer = EditUserSerializer(data= request.POST)
        if not serializer.is_valid():
            return JsonResponse({'message': f'Please add the field, {serializer.errors}', 'status': 400}, status=status.HTTP_400_BAD_REQUEST)

        serialized = serializer.data
        # username = serialized['username'].lower()
        id = int(serialized['id'])
        first_name  = serialized['first_name']  
        last_name  = serialized['last_name']  
        size  = int(serialized['portfolio'])
        margin  = int(serialized['margin'])
        
        user = User.objects.filter(pk=id).first()
        if not user:
            return JsonResponse({'message': f'User not found', 'status': 400}, status=status.HTTP_400_BAD_REQUEST)
        
        # user.set_password(password)
        # user.save()
        
        profile_instance = Profile.objects.filter(user=user).first()
        if not profile_instance:
            return JsonResponse({'message': f'Profile not found', 'status': 400}, status=status.HTTP_400_BAD_REQUEST)
        
        # profile_instance.first_name = username
        profile_instance.first_name = first_name
        profile_instance.last_name=last_name
        profile_instance.size = size
        profile_instance.margin= margin
        
        profile_instance.save()
        users_data = extract_all_user()    
        return JsonResponse({'message': 'Profile update successful!', 'data': users_data, 'status': 200}, status=status.HTTP_200_OK)
    
    except Exception as e:
        # Handle unexpected errors and return a JSON response
        return JsonResponse({'message': f'An unexpected error occurred: {e}', 'status': 400}, status=status.HTTP_400_BAD_REQUEST)
    
    
    
    