from rest_framework import serializers
from .models import *

class StrikeManagementSerializer(serializers.Serializer):
    short = serializers.CharField() 
    long = serializers.CharField()
    
class FundSerializer(serializers.Serializer):
    fund = serializers.CharField() 

class EarningForm(serializers.Serializer):
    symbol = serializers.CharField() 
    datetime = serializers.CharField()
    
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