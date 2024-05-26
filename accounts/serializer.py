from rest_framework import serializers
from .models import *
from django.contrib.auth.models import User
class StrikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Strike
        fields = '__all__'
        
class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        exclude = ['id']
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        # fields = '__all__'                
        exclude = ['password','date_joined','groups','user_permissions','is_staff','is_active','last_login']
class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'                
class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'                
    
class SignInSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()
    
class IdSerializer(serializers.Serializer):
    id = serializers.CharField()


class CreateUserSerializer(serializers.Serializer):
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    username = serializers.CharField()
    password = serializers.CharField()
    portfolio = serializers.CharField()
    margin  = serializers.CharField()
    
class EditUserSerializer(serializers.Serializer):
    id = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    # username = serializers.CharField()
    portfolio = serializers.CharField()
    margin  = serializers.CharField()    