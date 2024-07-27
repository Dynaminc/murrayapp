from rest_framework import serializers
from .models import *

class StrikeManagementSerializer(serializers.Serializer):
    short = serializers.CharField() 
    long = serializers.CharField()
    profit = serializers.CharField()
    
class FundSerializer(serializers.Serializer):
    fund = serializers.CharField() 

class EarningForm(serializers.Serializer):
    symbol = serializers.CharField() 
    datetime = serializers.CharField()

class NondayForm(serializers.Serializer):
    info = serializers.CharField() 
    datetime = serializers.CharField()
    half_day = serializers.CharField()
        
    
class NondaySerializer(serializers.ModelSerializer):
    class Meta:
            model = Nonday
            include = ['pk']
            fields = '__all__'    
class EarningSerializer(serializers.ModelSerializer):
    class Meta:
        model = Earning
        include = ['pk']
        fields = '__all__'
            
class StockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stock
        include = ['pk']
        fields = '__all__'