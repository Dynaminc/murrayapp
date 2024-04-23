from rest_framework import serializers
from .models import *

class StrikeManagementSerializer(serializers.Serializer):
    short = serializers.CharField() 
    long = serializers.CharField()
    
class FundSerializer(serializers.Serializer):
    fund = serializers.CharField() 
    
class StockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stock
        include = ['pk']
        fields = '__all__'