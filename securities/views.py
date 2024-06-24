from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.decorators import api_view
from django.core.paginator import Paginator
from rest_framework import status
from django.db.models import F, Q
from django_redis import get_redis_connection
from django.utils import timezone as tz
from securities.models import Stock
from .models import Combination, Missing
from accounts.models import Strike, Profile, Transaction, Notification, tran_not_type
from accounts.serializer import StrikeSerializer, ProfileSerializer, TransactionSerializer, NotificationSerializer
from datetime import datetime, time, timedelta
import pytz, os
import pprint, random
from .utils import quick_run
# from .cronjob import new_calc, clean_comb
from .serializer import *   
from .assess import get_test_data, json_migrator, all_strikes, export_file, top_flow
import pandas as pd 

con = get_redis_connection("default")
info = {'previous_time': None, 'latest_time': None, "combs": [], "dji_value":0, 'loading' : False}
def index(request):
    return render(request, "securities/ranks.html")

def load_missing(request):
    data = sorted(list(set([item.data for item in Missing.objects.all()])))
    return JsonResponse({"data":data})
    
def quantify_strike(portfolio, price):
    unit_portfolio_size = portfolio / 50
    quantity = unit_portfolio_size / price
    final_portfolio_size = int(quantity) * price
    
    return {'unit':unit_portfolio_size, 'quantity': int(quantity), 'final':final_portfolio_size}

def process_strike_symbol(symbol, user):
    split_symbol = symbol.split('-')
    profile_instance = Profile.objects.filter(user=user).first()
    if profile_instance:
        portfolio = profile_instance.size
        data = []
        for item in split_symbol:
            stk = Stock.objects.filter(symbol=item).latest('date_time')
            price = stk.close
            # price = Stock.objects.filter(symbol=item).first().close
            portfolio_data = quantify_strike(portfolio, price)
            data.append({"title": item, "price": price, 'quantity': portfolio_data['quantity'], 'final': portfolio_data['final'], 'date_time': stk.date_time})
        return data
    return []
def get_correct_close(array, title):
    data = [item for item in array if item['title'] == title][0]
    return data

def get_long_dji_value(all_combs, isLong, long, timestamp):
    if isLong:
        data = [item for item in all_combs if item.date_time == timestamp and item.symbol == long]
        if len(data) > 0:
            return data[0].avg
        else:
            return None
    else:
        data = [item for item in all_combs if item.date_time == timestamp and item.symbol == "DJI"]
        if len(data) > 0:
            return data[0].avg
        else:
            return None
    
@api_view(['GET','POST'])
def get_chart(request):
    try:
        id = request.GET.get('id', "")
        dji_value = Combination.objects.filter(symbol="DJI").latest('date_time')
        last_24_hours = datetime.now() - timedelta(hours=24)
        strike_instance = Strike.objects.filter(id=id).first() 
        short = strike_instance.short_symbol
        long = strike_instance.long_symbol
        all_combs = Combination.objects.filter(
                            Q(symbol=short) | 
                            Q(symbol=long) | 
                            Q(symbol='DJI') ).filter(date_time__gte=strike_instance.open_time).all()
        # .filter(date_time__gte=max(last_24_hours,strike_instance.open_time)).all()
                                    # last_24_hours, date_time__gte=strike_instance.open_time)
        print('fetched all combs', len(all_combs))
        shorts = [item for item in all_combs if item.symbol == short]
        
        data = [
            {
                'time': comb.date_time,
                'svalue': comb.avg ,  #- get_long_dji_value(all_combs, False, '', comb.date_time),
                'lvalue': get_long_dji_value(all_combs, True, long, comb.date_time) , #[item for item in all_combs if item.date_time == comb.date_time and item.symbol == long][0].avg, - get_long_dji_value(all_combs, False, '', comb.date_time)
                'dji': get_long_dji_value(all_combs, False, '', comb.date_time) , #[item for item in all_combs if item.date_time == comb.date_time and item.symbol == 'DJI'][0].avg,
            }
            for comb in shorts
        ]   
        return JsonResponse({ 'message':"Chart loaded Succesfully", "data":data, "dji_value": dji_value.avg})
    except:
        return JsonResponse({ 'message':"Load Failed", "data":[], "dji_value": 0})

@api_view(['GET'])
def load_strikes(request):
    if not request.user.is_authenticated:
        return JsonResponse({'message': 'You need to login','status': 400}, status=status.HTTP_400_BAD_REQUEST)
    
    data = [StrikeSerializer(strike).data for strike in Strike.objects.filter(user=request.user).all()]
    return JsonResponse({ 'message':"Strike Loaded Succesfully", "data":data})


@api_view(['GET'])
def load_all_strikes(request):
    if not request.user.is_authenticated:
        return JsonResponse({'message': 'You need to login','status': 400}, status=status.HTTP_400_BAD_REQUEST)
    if not request.user.is_superuser:
        return JsonResponse({'message': 'You have no access to this action','status': 400}, status=status.HTTP_400_BAD_REQUEST)
    
    data = [StrikeSerializer(strike).data for strike in Strike.objects.all()]
    return JsonResponse({ 'message':"Strike Loaded Succesfully", "data":data})


### crud for earnings 

@api_view(['POST','GET','PUT','DELETE','PATCH'])
def ManageEarning(request):
    if request.method == "POST" and request.method == "DELETE": 
        if not request.user.is_authenticated:
            return JsonResponse({'message': 'You need to login','status': 400}, status=status.HTTP_400_BAD_REQUEST)
        if not request.user.is_superuser:
            return JsonResponse({'message': 'You have no access to this action','status': 400}, status=status.HTTP_400_BAD_REQUEST)    
        
    if request.method == "POST":
        serializer = EarningForm(data=request.POST)
        if not serializer.is_valid():
            return JsonResponse({"data":[], 'errors': serializer.errors})    
        serializer = serializer.data
        
        symbol = serializer['symbol'] # unit stock
        datetimer = serializer['datetime']
        earning_instance = Earning.objects.filter(symbol=symbol).first()
        if earning_instance:
            earning_instance.date_time = datetimer
            earning_instance.save()
        else:
            earning_instance = Earning.objects.create(symbol=symbol, date_time=datetimer)
            
        all_data = Earning.objects.all()
        serialized_data = [ EarningSerializer(item).data for item in all_data ]             
        return JsonResponse({"data":serialized_data})    
    if request.method == "GET":
        all_data = Earning.objects.all()
        serialized_data = [ EarningSerializer(item).data for item in all_data ] 
        return JsonResponse({"data":serialized_data})
    
    if request.method == "PUT":
        return JsonResponse({ "data":Company.all_symbols})   
        
    if request.method == "PATCH":
        serializer = EarningForm(data=request.POST)
        if not serializer.is_valid():
            return JsonResponse({"data":[], 'errors': serializer.errors})    
        serializer = serializer.data
        
        symbol = serializer['symbol'] # unit strike
        datetimer = serializer['datetime']
        
        current_date = datetime.now().date()
        start_datetime = current_date - timedelta(days=1)
        start_date = datetime.combine(start_datetime, datetime.strptime("3:59", "%H:%M").time())
        end_date = current_date + timedelta(days=1)
        earnings_data = Earning.objects.filter(date_time__date__range=[start_date, end_date])

        valid_earnings_data = [item.symbol for item in earnings_data if start_date.date() <= item.date_time.date() <= end_date]
        
        if check_strike_symbol(symbol, valid_earnings_data):
            return JsonResponse({ "data":True})               
        else:
            return JsonResponse({ "data":False})               
        # filtered_combinations = [item for item in pre_filtered_combinations if not check_strike_symbol(item.symbol, valid_earnings_data)]
        
        return JsonResponse({ "data":Company.all_symbols})           
    
    if request.method =="DELETE":
        data = request.POST
        id = data['id'] 
        earning_instance = Earning.objects.filter(id=id).first()
        earning_instance.delete()
        all_data = Earning.objects.all()
        serialized_data = [ EarningSerializer(item).data for item in all_data ]             
        return JsonResponse({"data":serialized_data}) 
        
    
@api_view(['GET'])
def update_striker(request):
    
    id = request.GET.get('id', '0')
    strike_instance = Strike.objects.filter(id=id).first() 
    if not strike_instance:
        return JsonResponse({ 'message':"strike not found"})
        
    if not strike_instance.closed:
        long = strike_instance.long_symbol
        short = strike_instance.short_symbol
        
        long_data = process_strike_symbol(long, strike_instance.user)
        short_data = process_strike_symbol(short, strike_instance.user)
        
        sum_total = 0
        sum_total += sum([item['final'] for item in long_data])
        sum_total += sum([item['final'] for item in short_data])
        
        strike_instance.fls_close = get_correct_close(long_data, strike_instance.first_long_stock)['price']
        strike_instance.fls_close_price = get_correct_close(long_data, strike_instance.first_long_stock)['final']
        strike_instance.sls_close = get_correct_close(long_data, strike_instance.second_long_stock)['price']
        strike_instance.sls_close_price = get_correct_close(long_data, strike_instance.second_long_stock)['final']                
        strike_instance.tls_close = get_correct_close(long_data, strike_instance.third_long_stock)['price']
        strike_instance.tls_close_price = get_correct_close(long_data, strike_instance.third_long_stock)['final']                

        strike_instance.fss_close = get_correct_close(short_data, strike_instance.first_short_stock)['price']
        strike_instance.fss_close_price = get_correct_close(short_data, strike_instance.first_short_stock)['final']
        strike_instance.sss_close = get_correct_close(short_data, strike_instance.second_short_stock)['price']
        strike_instance.sss_close_price = get_correct_close(short_data, strike_instance.second_short_stock)['final']                
        strike_instance.tss_close = get_correct_close(short_data, strike_instance.third_short_stock)['price']
        strike_instance.tss_close_price = get_correct_close(short_data, strike_instance.third_short_stock)['final']             
        # process for exit signal             
        #signal_exit = models.BooleanField(default=False
        strike_instance.current_price = get_current_value(strike_instance)
        strike_instance.current_percentage = (strike_instance.current_price / strike_instance.total_open_price) * 100
        if strike_instance.max_percentage:
            strike_instance.max_percentage = strike_instance.current_percentage if strike_instance.current_percentage > strike_instance.max_percentage else strike_instance.max_percentage
        else:
            strike_instance.max_percentage = strike_instance.current_percentage 
            
        if strike_instance.min_percentage:
            strike_instance.min_percentage = strike_instance.current_percentage if strike_instance.current_percentage < strike_instance.min_percentage else strike_instance.min_percentage
        
        else:
            strike_instance.min_percentage = strike_instance.current_percentage        
                
        strike_instance.save()
        
        return JsonResponse({ 'message':"Trade loaded", "data":StrikeSerializer(strike_instance).data})
    else:
        return JsonResponse({ 'message':"Trade closed", "data":StrikeSerializer(strike_instance).data})


def get_current_value(data):
    resp = (-((data.fss_close - data.fss_open) * data.fss_quantity)
        -((data.sss_close - data.sss_open) * data.sss_quantity) 
        -((data.tss_close - data.tss_open) * data.tss_quantity) +

        ((data.fls_close - data.fls_open) * data.fls_quantity)+
        ((data.sls_close - data.sls_open) * data.sls_quantity)+
        ((data.tls_close - data.tls_open) * data.tls_quantity)
        )
    return resp

def update_strike(id):
    
    strike_instance = Strike.objects.filter(id=id).first() 
    if not strike_instance:
        return False
    if not strike_instance.closed:
        long = strike_instance.long_symbol
        short = strike_instance.short_symbol
        
        long_data = process_strike_symbol(long, strike_instance.user)
        short_data = process_strike_symbol(short, strike_instance.user)
        
        sum_total = 0
        sum_total += sum([item['final'] for item in long_data])
        sum_total += sum([item['final'] for item in short_data])
        
            
        strike_instance.fls_close = get_correct_close(long_data, strike_instance.first_long_stock)['price']
        strike_instance.fls_close_price = get_correct_close(long_data, strike_instance.first_long_stock)['final']
        strike_instance.sls_close = get_correct_close(long_data, strike_instance.second_long_stock)['price']
        strike_instance.sls_close_price = get_correct_close(long_data, strike_instance.second_long_stock)['final']                
        strike_instance.tls_close = get_correct_close(long_data, strike_instance.third_long_stock)['price']
        strike_instance.tls_close_price = get_correct_close(long_data, strike_instance.third_long_stock)['final']                

        strike_instance.fss_close = get_correct_close(short_data, strike_instance.first_short_stock)['price']
        strike_instance.fss_close_price = get_correct_close(short_data, strike_instance.first_short_stock)['final']
        strike_instance.sss_close = get_correct_close(short_data, strike_instance.second_short_stock)['price']
        strike_instance.sss_close_price = get_correct_close(short_data, strike_instance.second_short_stock)['final']                
        strike_instance.tss_close = get_correct_close(short_data, strike_instance.third_short_stock)['price']
        strike_instance.tss_close_price = get_correct_close(short_data, strike_instance.third_short_stock)['final']             
        
        
        
        strike_instance.current_price = get_current_value(strike_instance)
        strike_instance.current_percentage = (strike_instance.current_price /strike_instance.total_open_price) * 100
        
        
        if strike_instance.max_percentage:
            strike_instance.max_percentage = strike_instance.current_percentage if strike_instance.current_percentage > strike_instance.max_percentage else strike_instance.max_percentage
        else:
            strike_instance.max_percentage = strike_instance.current_percentage 
            
        if strike_instance.min_percentage:
            strike_instance.min_percentage = strike_instance.current_percentage if strike_instance.current_percentage < strike_instance.min_percentage else strike_instance.min_percentage
        
        else:
            strike_instance.min_percentage = strike_instance.current_percentage 
        strike_instance.save() 
        # process for exit signal             
        if strike_instance.current_percentage >= strike_instance.target_profit and not strike_instance.signal_exit:
            strike_instance.signal_exit = True
            strike_instance.save()
            Notification.objects.create(user=strike_instance.user, details=f"Strike has exceeded the profit mark", strike_id=strike_instance.id, notification_type=tran_not_type.EXIT_ALERT)   
            trigger_close_strike(strike_instance.id)
        else:
            if strike_instance.current_percentage > 1: 
                detail = f"Strike has exceeded the 1% mark"   
                if not Notification.objects.filter(strike_id=strike_instance.id).filter(details=detail).first():
                    Notification.objects.create(user=strike_instance.user, details=detail, strike_id=strike_instance.id, notification_type=tran_not_type.CUSTOM)   
            if strike_instance.current_percentage < -1:
                detail = f"Strike has exceeded the -1% mark"
                if not Notification.objects.filter(strike_id=strike_instance.id).filter(details=detail).first():
                    Notification.objects.create(user=strike_instance.user, details=detail, strike_id=strike_instance.id, notification_type=tran_not_type.CUSTOM)                       
            if strike_instance.current_percentage < -1.5:
                detail = f"Strike has exceeded the -1.5% mark"
                if not Notification.objects.filter(strike_id=strike_instance.id).filter(details=detail).first():
                    Notification.objects.create(user=strike_instance.user, details=detail, strike_id=strike_instance.id, notification_type=tran_not_type.CUSTOM)                     
                   
    
    return True

def trigger_close_strike(id):    
    close_time = str(Stock.objects.latest('date_time').date_time)
    
    strike_instance = Strike.objects.filter(id=id).first() 
    if not strike_instance:
        return JsonResponse({ 'message':"Strike not found"}, status=status.HTTP_400_BAD_REQUEST)     
    
    profile_instance = Profile.objects.filter(user=strike_instance.user).first()
    if not profile_instance:
        return JsonResponse({'message': 'Profile not found','status': 400}, status=status.HTTP_400_BAD_REQUEST)
    
    if not strike_instance.closed:
        long = strike_instance.long_symbol
        short = strike_instance.short_symbol
        
        long_data = process_strike_symbol(long, strike_instance.user)
        short_data = process_strike_symbol(short, strike_instance.user)
        
        stock_time = Stock.objects.latest('date_time').date_time
        
        sum_total = 0
        sum_total = get_current_value(strike_instance) + strike_instance.total_open_price
        strike_instance.total_close_price = sum_total
        
            
        strike_instance.close_time = stock_time
        strike_instance.fls_close = get_correct_close(long_data, strike_instance.first_long_stock)['price']
        strike_instance.fls_close_price = get_correct_close(long_data, strike_instance.first_long_stock)['final']
        strike_instance.sls_close = get_correct_close(long_data, strike_instance.second_long_stock)['price']
        strike_instance.sls_close_price = get_correct_close(long_data, strike_instance.second_long_stock)['final']                
        strike_instance.tls_close = get_correct_close(long_data, strike_instance.third_long_stock)['price']
        strike_instance.tls_close_price = get_correct_close(long_data, strike_instance.third_long_stock)['final']                

        strike_instance.fss_close = get_correct_close(short_data, strike_instance.first_short_stock)['price']
        strike_instance.fss_close_price = get_correct_close(short_data, strike_instance.first_short_stock)['final']
        strike_instance.sss_close = get_correct_close(short_data, strike_instance.second_short_stock)['price']
        strike_instance.sss_close_price = get_correct_close(short_data, strike_instance.second_short_stock)['final']                
        strike_instance.tss_close = get_correct_close(short_data, strike_instance.third_short_stock)['price']
        strike_instance.tss_close_price = get_correct_close(short_data, strike_instance.third_short_stock)['final']     
        strike_instance.closed = True
        
        strike_instance.save()
        
        previous_balance = profile_instance.balance
        profile_instance.balance = previous_balance  + get_current_value(strike_instance) + (strike_instance.total_open_price / profile_instance.margin)
        profile_instance.save()
        
        Transaction.objects.create(user=strike_instance.user, details=f'Your order has been closed for strike {strike_instance.long_symbol}/{strike_instance.short_symbol}', strike_id=strike_instance.id, previous_balance=previous_balance, new_balance=profile_instance.balance, amount=sum_total, transaction_type=tran_not_type.TRADE_CLOSED)     
        Notification.objects.create(user=strike_instance.user, details=f"Strike {strike_instance.id} has been closed", strike_id=strike_instance.id, notification_type=tran_not_type.TRADE_CLOSED)   
        
        return JsonResponse({ 'message':"Trade Closed Succesfully", "data":StrikeSerializer(strike_instance).data})
    else:
        return JsonResponse({ 'message':"Trade Closed Already", "data":StrikeSerializer(strike_instance).data})



@api_view(['GET'])
def cronat(response):
    data = [ update_strike(item.id) for item in Strike.objects.filter(closed=False)]
    if False in data:
        Cronny.objects.create(symbol=f"{len(data)}: False")
    else:
        Cronny.objects.create(symbol=f"{len(data)}: True")
    return JsonResponse({'message': f'Updated', 'status': 400}, 
                                status=status.HTTP_200_OK)        
@api_view(['GET'])
def close_strike(request):
    id = request.GET.get('strike_id', 10)
    
    close_time = str(Stock.objects.latest('date_time').date_time)
    
    if not request.user.is_authenticated:
        return JsonResponse({'message': 'You need to login','status': 400}, status=status.HTTP_400_BAD_REQUEST)
    
    
    strike_instance = Strike.objects.filter(id=id).first() 
    if not strike_instance:
        return JsonResponse({ 'message':"Strike not found "}, status=status.HTTP_400_BAD_REQUEST)   
    
    if strike_instance.user != request.user :
        return JsonResponse({ 'message':"You have no permission to  close this trade"}, status=status.HTTP_400_BAD_REQUEST)   
        
    profile_instance = Profile.objects.filter(user=request.user).first()
    if not profile_instance:
        return JsonResponse({'message': 'Profile not found','status': 400}, status=status.HTTP_400_BAD_REQUEST)
    
    if not strike_instance.closed:
        long = strike_instance.long_symbol
        short = strike_instance.short_symbol
        
        long_data = process_strike_symbol(long, strike_instance.user)
        short_data = process_strike_symbol(short, strike_instance.user)
        
        stock_time = Stock.objects.latest('date_time').date_time
        
        sum_total = 0
        # sum_total += sum([item['final'] for item in long_data])
        # sum_total += sum([item['final'] for item in short_data])
        
        
        # strike_instance.total_close_price = sum_total
        sum_total = get_current_value(strike_instance) + strike_instance.total_open_price
        strike_instance.total_close_price = sum_total
        
            
        strike_instance.close_time = stock_time
        strike_instance.fls_close = get_correct_close(long_data, strike_instance.first_long_stock)['price']
        strike_instance.fls_close_price = get_correct_close(long_data, strike_instance.first_long_stock)['final']
        strike_instance.sls_close = get_correct_close(long_data, strike_instance.second_long_stock)['price']
        strike_instance.sls_close_price = get_correct_close(long_data, strike_instance.second_long_stock)['final']                
        strike_instance.tls_close = get_correct_close(long_data, strike_instance.third_long_stock)['price']
        strike_instance.tls_close_price = get_correct_close(long_data, strike_instance.third_long_stock)['final']                

        strike_instance.fss_close = get_correct_close(short_data, strike_instance.first_short_stock)['price']
        strike_instance.fss_close_price = get_correct_close(short_data, strike_instance.first_short_stock)['final']
        strike_instance.sss_close = get_correct_close(short_data, strike_instance.second_short_stock)['price']
        strike_instance.sss_close_price = get_correct_close(short_data, strike_instance.second_short_stock)['final']                
        strike_instance.tss_close = get_correct_close(short_data, strike_instance.third_short_stock)['price']
        strike_instance.tss_close_price = get_correct_close(short_data, strike_instance.third_short_stock)['final']     
        strike_instance.closed = True
        
        strike_instance.save()


        previous_balance = profile_instance.balance
        diff =  get_current_value(strike_instance) + (strike_instance.total_open_price / profile_instance.margin)
        profile_instance.balance = previous_balance  + get_current_value(strike_instance) + (strike_instance.total_open_price / profile_instance.margin)
        
        profile_instance.save()
        
        
        
        Transaction.objects.create(user=strike_instance.user, details=f'Your order has been closed for strike {strike_instance.long_symbol}/{strike_instance.short_symbol}', strike_id=strike_instance.id, previous_balance=previous_balance, new_balance=profile_instance.balance, amount=diff, transaction_type=tran_not_type.TRADE_CLOSED)       
        
        # previous_balance = profile_instance.balance
        # profile_instance.balance = previous_balance  - 10
        # profile_instance.save()
        
        # Transaction.objects.create(user=strike_instance.user, details=f"Broker's Commission for Strike:{strike_instance.long_symbol}/{strike_instance.short_symbol}", previous_balance=previous_balance, new_balance=profile_instance.balance, credit=False, amount=10, transaction_type=tran_not_type.COMMISSON_FEE)       
        Notification.objects.create(user=strike_instance.user, details=f"Strike {strike_instance.id} has been closed", strike_id=strike_instance.id, notification_type=tran_not_type.TRADE_CLOSED)   
        
        return JsonResponse({ 'message':"Trade Closed Succesfully", "data":StrikeSerializer(strike_instance).data})
    else:
        return JsonResponse({ 'message':"Trade Closed Already", "data":StrikeSerializer(strike_instance).data})



@api_view(['POST'])
def confirm_strike(request):
    serializer = StrikeManagementSerializer(data=request.POST)
    if not serializer.is_valid():
        return JsonResponse({'message': f'{serializer.errors}', 'status': 400}, 
                                status=status.HTTP_400_BAD_REQUEST)
    if not request.user.is_authenticated:
        return JsonResponse({'message': 'You need to login','status': 400}, status=status.HTTP_400_BAD_REQUEST)

    profile_instance = Profile.objects.filter(user=request.user).first()
    if not profile_instance:
        return JsonResponse({'message': 'Profile not found','status': 400}, status=status.HTTP_400_BAD_REQUEST)
    
    serialized = serializer.data
    short = serialized['short'] 
    long = serialized['long'] 
    profit = serialized['profit'] 
    stock_time = Stock.objects.latest('date_time').date_time

    long_data = process_strike_symbol(long, request.user)
    short_data = process_strike_symbol(short, request.user)
    
    sum_total = 0
    sum_total += sum([item['final'] for item in long_data])
    sum_total += sum([item['final'] for item in short_data])
    
    strike_instance = Strike.objects.create( 
            user = profile_instance.user,
            target_profit = profit,
            long_symbol = long,
            short_symbol = short,
            total_open_price = sum_total,
            open_time = stock_time,
            current_price = sum_total,
            
            first_long_stock = long_data[0]['title'],
            fls_quantity = long_data[0]['quantity'],
            fls_price = long_data[0]['final'],
            fls_open = long_data[0]['price'],
            
            second_long_stock = long_data[1]['title'],
            sls_quantity = long_data[1]['quantity'],
            sls_price = long_data[1]['final'],
            sls_open = long_data[1]['price'],
            
            third_long_stock = long_data[2]['title'],
            tls_quantity = long_data[2]['quantity'],
            tls_price = long_data[2]['final'],
            tls_open = long_data[2]['price'],
            
            first_short_stock = short_data[0]['title'],
            fss_quantity = short_data[0]['quantity'],
            fss_price = short_data[0]['final'],
            fss_open = short_data[0]['price'],
            
            second_short_stock = short_data[1]['title'],
            sss_quantity = short_data[1]['quantity'],
            sss_price = short_data[1]['final'],
    
            sss_open = short_data[1]['price'],
            
            third_short_stock = short_data[2]['title'],
            tss_quantity = short_data[2]['quantity'],
            tss_price = short_data[2]['final'],
            tss_open = short_data[2]['price'],
            )
    
    previous_balance = profile_instance.balance
    profile_instance.balance = previous_balance - sum_total / (profile_instance.margin)
    profile_instance.save()
    
    Transaction.objects.create(user=profile_instance.user, details=f'Your order has been placed for strike {strike_instance.long_symbol}/{strike_instance.short_symbol}', strike_id=strike_instance.id, previous_balance=previous_balance, new_balance=profile_instance.balance, credit=False, amount=sum_total, transaction_type=tran_not_type.TRADE_OPENED)

    # previous_balance = profile_instance.balance
    # profile_instance.balance = previous_balance  - 10
    # profile_instance.save()
    
    # Transaction.objects.create(user=strike_instance.user, details=f"Broker's Commission for Strike:{strike_instance.long_symbol}/{strike_instance.short_symbol}", previous_balance=previous_balance, new_balance=profile_instance.balance, credit=False, amount=10, transaction_type=tran_not_type.COMMISSON_FEE)       
            
    Notification.objects.create(user=strike_instance.user, details=f"Trade {strike_instance.id} has been opened", strike_id=strike_instance.id, notification_type=tran_not_type.TRADE_OPENED)   
    return JsonResponse({ 'message':"Strike Saved Succesfully", "data":StrikeSerializer(strike_instance).data})


@api_view(['POST'])
def remove_fund(request):
    try:
        if not request.user.is_authenticated:
            return JsonResponse({'message': 'You need to login','status': 400}, status=status.HTTP_400_BAD_REQUEST)

        serializer = FundSerializer(data=request.POST)
        if not serializer.is_valid():
            return JsonResponse({'message': f'{serializer.errors}', 'status': 400}, 
                                    status=status.HTTP_400_BAD_REQUEST)
    
        serialized = serializer.data
        fund = int(serialized['fund'])
        
        profile_instance = Profile.objects.filter(user=request.user).first()
        if not profile_instance:
            return JsonResponse({'message': 'Profile not found','status': 400}, status=status.HTTP_400_BAD_REQUEST)
                        
        # previous_balance = profile_instance.size
        profile_instance.balance = profile_instance.balance - fund
        profile_instance.size = profile_instance.size - fund
        profile_instance.save()
        
        Transaction.objects.create(user=profile_instance.user,  details=f"Wallet has been funded",
                                new_balance=profile_instance.size, 
                                credit=True, amount=fund, transaction_type=tran_not_type.WALLET_FUNDED)
        Notification.objects.create(user=profile_instance.user, details=f"Wallet has been funded with {fund}", notification_type=tran_not_type.WALLET_FUNDED)   
        
        return JsonResponse({'message':"Fund added Succesfully"})  
    except:
        return JsonResponse({'message':"Fund not added"})  
    
@api_view(['POST'])
def add_fund(request):
    try:
        if not request.user.is_authenticated:
            return JsonResponse({'message': 'You need to login','status': 400}, status=status.HTTP_400_BAD_REQUEST)

        serializer = FundSerializer(data=request.POST)
        if not serializer.is_valid():
            return JsonResponse({'message': f'{serializer.errors}', 'status': 400}, 
                                    status=status.HTTP_400_BAD_REQUEST)
    
        serialized = serializer.data
        fund = int(serialized['fund'])
        
        profile_instance = Profile.objects.filter(user=request.user).first()
        if not profile_instance:
            return JsonResponse({'message': 'Profile not found','status': 400}, status=status.HTTP_400_BAD_REQUEST)
                        
        # previous_balance = profile_instance.size
        profile_instance.balance = profile_instance.balance + fund
        profile_instance.size = profile_instance.size + fund
        profile_instance.save()
        
        Transaction.objects.create(user=profile_instance.user,  details=f"Wallet has been funded",
                                new_balance=profile_instance.size, 
                                credit=True, amount=fund, transaction_type=tran_not_type.WALLET_FUNDED)
        Notification.objects.create(user=profile_instance.user, details=f"Wallet has been funded with {fund}", notification_type=tran_not_type.WALLET_FUNDED)   
        
        return JsonResponse({'message':"Fund added Succesfully"})  
    except:
        return JsonResponse({'message':"Fund not added"})  

@api_view(['GET'])
def load_transactions(request):
    data = {}
    if not request.user.is_authenticated:
        return JsonResponse({'message': 'You need to login','status': 400}, status=status.HTTP_400_BAD_REQUEST)

    profile_instance = Profile.objects.filter(user=request.user).first()
    if not profile_instance:
        return JsonResponse({'message': 'Profile not found','status': 400}, status=status.HTTP_400_BAD_REQUEST)

    transaction_instances = Transaction.objects.filter(user=profile_instance.user).all()
    data = [TransactionSerializer(item).data for item in transaction_instances]
    return JsonResponse({'data':data , 'message':"Trnasactions Loaded"})  


@api_view(['GET'])
def load_all_transactions(request):
    data = {}
    if not request.user.is_authenticated:
        return JsonResponse({'message': 'You need to login','status': 400}, status=status.HTTP_400_BAD_REQUEST)

    if not request.user.is_superuser:
        return JsonResponse({'message': 'You have no access to this action','status': 400}, status=status.HTTP_400_BAD_REQUEST)
        
    transaction_instances = Transaction.objects.all()
    data = [TransactionSerializer(item).data for item in transaction_instances]
    return JsonResponse({'data':data , 'message':"Trnasactions Loaded"})  

@api_view(['GET'])
def load_notifications(request):
    data = {}
    if not request.user.is_authenticated:
        return JsonResponse({'message': 'You need to login','status': 400}, status=status.HTTP_400_BAD_REQUEST)

    profile_instance = Profile.objects.filter(user=request.user).first()
    if not profile_instance:
        return JsonResponse({'message': 'Profile not found','status': 400}, status=status.HTTP_400_BAD_REQUEST)

    notification_instances = Notification.objects.filter(user=profile_instance.user).all()
    data = [NotificationSerializer(item).data for item in notification_instances]
    return JsonResponse({'data':data , 'message':"Notifations Loaded"})  

@api_view(['GET'])
def load_all_notifications(request):
    data = {}
    if not request.user.is_authenticated:
        return JsonResponse({'message': 'You need to login','status': 400}, status=status.HTTP_400_BAD_REQUEST)

    if not request.user.is_superuser:
        return JsonResponse({'message': 'You have no access to this action','status': 400}, status=status.HTTP_400_BAD_REQUEST)
    
    notification_instances = Notification.objects.all()
    data = [NotificationSerializer(item).data for item in notification_instances]
    return JsonResponse({'data':data , 'message':"Notifations Loaded"})  



def calculate_stats(data, profile_instance):
    
    strikes = Strike.objects.filter(user=profile_instance.user).all()
    profit_trades = [(strike.total_close_price - strike.total_open_price) for strike in strikes if strike.closed and strike.total_close_price > strike.total_open_price]
    data['total_profits'] = sum(profit_trades)
    data['win_rate'] =  0
    
    if len(strikes) > 0 and len([strike for strike in strikes if strike.closed]) > 0:
        data['win_rate'] = len(profit_trades) / len([strike for strike in strikes if strike.closed]) * 10
        
    
    data['total_loss'] = sum([(strike.total_open_price - strike.total_close_price  ) for strike in strikes if strike.closed and strike.total_close_price < strike.total_open_price])
    
    data['operating_balance'] = sum([strike.total_close_price if strike.total_close_price else 0 for strike in strikes if not strike.closed ]) 
    
    open_prices = sum([strike.total_open_price if strike.total_open_price else 0  for strike in strikes if not strike.closed ])
    close_prices = sum([strike.total_close_price if strike.total_close_price else 0   for strike in strikes if not strike.closed ])
    
    data['operating_percent'] = 0
    data['cent_color'] = 'gray'
    if open_prices > 0:
        data['operating_percent'] = (close_prices - open_prices) / open_prices * 100
        if data['operating_percent'] > 0:
            data['cent_color'] = 'green'
        else:
            data['cent_color'] = 'red'
    
    data['total_trades'] = len(strikes)
    
    data['open_trades'] = len([strike for strike in strikes if not strike.closed])
    data['closed_trades'] = len([strike for strike in strikes if strike.closed])
    
    data['exit_alerts'] = len([strikes for strike in strikes if strike.signal_exit])
    
    return data


@api_view(['GET'])
def load_all_stats(request):
    
    if not request.user.is_authenticated:
        return JsonResponse({'message': 'You need to login','status': 400}, status=status.HTTP_400_BAD_REQUEST)
    if not request.user.is_superuser:
        return JsonResponse({'message': 'You have no access to this action','status': 400}, status=status.HTTP_400_BAD_REQUEST)
    
    final_data = []
    for profile_instance in Profile.objects.all(): 
        print(profile_instance)
        data = {}
        for key, value in ProfileSerializer(profile_instance).data.items():    
            data[key] = value
            
        final_data.append(calculate_stats(data, profile_instance))   
        print(final_data)
    
    return JsonResponse({'data':final_data , 'message':"Loaded Succesfully"})  

@api_view(['GET'])
def load_stats(request):
    data = {}
    if not request.user.is_authenticated:
        return JsonResponse({'message': 'You need to login','status': 400}, status=status.HTTP_400_BAD_REQUEST)
    
    profile_instance = Profile.objects.filter(user=request.user).first()
    if not profile_instance:
        return JsonResponse({'message': 'Profile not found','status': 400}, status=status.HTTP_400_BAD_REQUEST)
    
    
    for key, value in ProfileSerializer(profile_instance).data.items():
        data[key] = value
        
    data = calculate_stats(data, profile_instance)

    return JsonResponse({'data':data , 'message':"Loaded Succesfully"})  


@api_view(['POST'])
def get_strike_breakdown(request):
    
    if not request.user.is_authenticated:
        return JsonResponse({'message': 'You need to login','status': 400}, status=status.HTTP_400_BAD_REQUEST)

    profile_instance = Profile.objects.filter(user=request.user).first()
    if not profile_instance:
        return JsonResponse({'message': 'Profile not found','status': 400}, status=status.HTTP_400_BAD_REQUEST)
    
    serializer = StrikeManagementSerializer(data=request.POST)
    if not serializer.is_valid():
        return JsonResponse({'message': f'{serializer.errors}', 'status': 400}, 
                                status=status.HTTP_400_BAD_REQUEST)    
    serialized = serializer.data
    short = serialized['short'] 
    long = serialized['long'] 
    stock_time = str(Stock.objects.latest('date_time').date_time)
    
    data = {'stock_time':stock_time, 'portfolio':profile_instance.balance, 'shortSymbol':short,'shortData':process_strike_symbol(short, request.user), 'longSymbol': long, 'longData': process_strike_symbol(long, request.user) }
    
    
    return JsonResponse({'data':data, 'message':"Loaded Succesfully"})  


def clean_comb():
    # clean_redis()
    return 'cleaned'

    count = 0 
    times = [datetime(2024, 4, 29, 11, 40)]
    for item in times:
        print('Running clean module ')
        data = Combination.objects.filter(date_time__gte=item).all()
        data.delete()
        print('cleaned combinations')
        data = Stock.objects.filter(date_time__gte=item).all()
        data.delete()
        print('cleaned stocks')
        con.set("combinations_data", "[]")
        con.set("comb_time", "[]")
        con.set("stock_data", "[]")
        print('cleaned redis')


@api_view(['GET', 'POST'])
def trigger_store(request):
    print("initiated")    
    # data = clean_comb()
    # print("Fetching")
    # data = get_test_data()
    print("Migrating")
    # json_migrator()
    # print("Getting all strikes ")
    # data = all_strikes()
    # print("Completed strikes")
    
    
    # data = new_calc()
    
    print("Exporting")
    # data = export_file()
    # now to export the last minute ranking
    
    # data = new_calc()
    
    # data = top_flow()
    
    print("Exported") 
    return JsonResponse({'message':"Loaded Succesfully",})  

            

        
@api_view(['GET', 'POST'])
def trigger_lens(request):
    item = datetime(2024, 4, 19, 12)
    
    combination_data = Combination.objects.filter(date_time__gte=item).all()
    stock_data = Stock.objects.filter(date_time__gte=item).all()
    return JsonResponse({'message':"Loaded Succesfully",'combs':len(combination_data), 'stocks': len(stock_data)})  
    
@api_view(['GET', 'POST'])
def clean_end(request):
    try:
        print('cleaning')
        id = int(request.GET.get('id', 10))
        delete = request.GET.get('delete',False)
        d = tz.now() - timedelta(days=id)
        print(d)
        count = 0
        paginator = Paginator(Combination.objects.filter(date_time__lt=d), 1000) # chunks of 1000
        print('paginated')
        for page_idx in range(1, paginator.num_pages):
            for row in paginator.page(page_idx).object_list:
                if delete:  
                    count += 1
                    print('deleteded, ', count, row.date_time)
                    row.delete()
        return JsonResponse({'message':f"Deleted Succesfully {count}"})    
    except Exception as E:
        return JsonResponse({'message':f"Exception {E}"})    
    
    
    

def check_market_hours(dat):
    eastern = pytz.timezone('US/Eastern')
    dt = eastern.localize(dat)
    print(dt)
    if dt.weekday() >= 5:  # Weekend
        return "red"
    elif dt.weekday() < 5 and (dt.time() < time(9, 30) or dt.time() > time(16, 0)):  # Weekday before 9:30 or after 4:00
        return "red"
    elif dt.time() >= time(9, 30) and dt.time() <= time(9, 45):  # 9:30 to 9:45
        return "yellow"
    elif dt.time() >= time(15, 45) and dt.time() <= time(16, 0):  # 15:45 to 16:00
        return "yellow"
    elif dt.time() >= time(9, 30) and dt.time() <= time(9, 45):  # 9:30 to 9:45
        return "yellow"
    elif dt.time() >= time(15, 45) and dt.time() <= time(16, 0):  # 15:45 to 16:00
        return "yellow"
    elif dt.time() >= time(9, 45) and dt.time() <= time(15, 45):  # 9:45 to 15:45
        return "green"
    else:
        return "red"
    
def check_strike_symbol(strike, earning_symbols):
    for item in earning_symbols:
        if item in strike:
            return True
    return False
        
    

@api_view(['GET', 'POST'])
def test_end(request):
    combs = []
    market_state = "off"
    if 'loading.txt' not in os.listdir(os.getcwd()):
        f = open(os.path.join(os.getcwd(),'loading.txt'), 'w')
        f.write('loading')
        f.close()
    else:
        f = open(os.path.join(os.getcwd(),'loading.txt'), 'r')
        content = f.read()
        f.close()
        if content == 'loading':
            info['loading'] = True
        else:
            info['loading'] = False
            f = open(os.path.join(os.getcwd(),'loading.txt'), 'w')
            f.write('loading')
            f.close()  
            
    # try:
    initial_time = datetime.now()
    start_time = datetime.now()
    market_state = check_market_hours(datetime.now())
    ad = Combination.objects.latest('date_time')
    end_time = datetime.now()
    time_difference = end_time - start_time
    print(f'fetched combination for {initial_time} ', time_difference)
    if info['loading']:
        print('loading combs')
        combs =  info['combs']
        print(combs, 'combs fetched')
        return JsonResponse({"top_5": combs[:20], "low_5":combs[-20:], "market": market_state,"dji_value":info['dji_value']}, status=status.HTTP_200_OK)
    
    # print("Checking time: ",ad.date_time.replace(second=0, microsecond=0), ' - ', info['latest_time'], ' - ', len(info['combs']) )                    
    # if ad.date_time.replace(second=0, microsecond=0) == info['latest_time'] and len(info['combs']) > 0:
    #     print('fetching saved combs')
    #     combs =  info['combs']
    #     return JsonResponse({"top_5": combs[:20], "low_5":combs[-20:], "market": market_state,"dji_value":info['dji_value']}, status=status.HTTP_200_OK)
    
    start_time = datetime.now()
    
    info['loading'] = True
    info['latest_time'] = ad.date_time.replace(second=0, microsecond=0)
    try:
        dji_value = Combination.objects.filter(symbol="DJI").latest('date_time')
        info['dji_value'] = dji_value.avg
    except:
        dji_value = 0
        info['dji_value'] = 0
    
    
    end_time = datetime.now()
    time_difference = end_time - start_time
    print(f'fetched dji {initial_time} ', time_difference)
    
    display_time = datetime.now()
    current_time = str(display_time).split('.')[0]
    
    eastern = pytz.timezone('US/Eastern')
    dt = eastern.localize(datetime.now())
    if dt.weekday() < 5 and (dt.time() >= time(9, 30) and dt.time() <= time(16, 0)):
        display_time = datetime.now()
        current_time = str(display_time).split('.')[0]
        
        
    
    
    latest_data = info['latest_time']
    print(latest_data, 'latest')
    if latest_data:
        start_time = datetime.now()
        
        latest_time = latest_data
        # pre_peri_filtered_combinations = Combination.objects.filter(date_time__gte = latest_time )
    
        pre_filtered_combinations = Combination.objects.filter(
            date_time__gte=latest_time
        ).order_by('symbol', '-date_time').distinct('symbol')
        pre_filtered_combinations = list(pre_filtered_combinations)
        # done = []
        # pre_filtered_combinations = []
        # for item in pre_peri_filtered_combinations:
        #     if item.symbol not in done:
        #         pre_filtered_combinations.append(item)
        #         done.append(item.symbol)
        
        end_time = datetime.now()
        time_difference = end_time - start_time
        print(f'Fetched and processed combs {initial_time} ', time_difference) 
        
        
        start_time = datetime.now()
        
        combs = [{'symbol':item.symbol,'stdev':item.stdev,'score':item.avg,'date':str(latest_time)} for item in pre_filtered_combinations ]
        combs.sort(key=lambda x: x['score'], reverse=True)
        info['combs'] = combs[:20]+combs[-20:]
        print('saved combs fr min', info['latest_time'])
        # info['loading'] = False
        
        f = open(os.path.join(os.getcwd(),'loading.txt'), 'w')
        f.write('done')
        f.close()
        
        end_time = datetime.now()
        time_difference = end_time - start_time
        print(f'final  sort {initial_time} ', time_difference) 
                
                
        end_time = datetime.now()
        time_difference = end_time - initial_time
        print(f'Total Time {initial_time} ', time_difference)        
        return JsonResponse({"top_5": combs[:20], "low_5":combs[-20:], "market": market_state, "dji_value": dji_value.avg }, status=status.HTTP_200_OK )
    else:
        return JsonResponse({"top_5": combs[:20], "low_5":combs[-20:], "market": market_state,"dji_value":dji_value.avg}, status=status.HTTP_200_OK)
    # except Exception as E:
    #     info['loading'] = False
    #     return JsonResponse({"top_5": combs[:20], "low_5":combs[-20:], "market": "red", 'error':str(E), "dji_value":0}, status=status.HTTP_200_OK)
    

        # # Get earnings data for the relevant period
        # current_date = datetime.now().date()
        # start_datetime = current_date - timedelta(days=1)
        # start_date = datetime.combine(start_datetime, datetime.strptime("3:59", "%H:%M").time())
        # end_date = current_date + timedelta(days=1)
        # earnings_data = Earning.objects.filter(date_time__date__range=[start_date, end_date])
        
        # valid_earnings_data = [item.symbol for item in earnings_data if start_date.date() <= item.date_time.date() <= end_date]
        # filtered_combinations = [item for item in pre_filtered_combinations if not check_strike_symbol(item.symbol, valid_earnings_data)]
        
        # combs = [{'symbol':item.symbol,'stdev':item.stdev,'score':item.avg,'date':str(latest_time)} for item in filtered_combinations ]    
def stocks(request):
    combo = Combination.objects.filter(symbol__icontains='CSCO')
    print(len(combo))
    combinations = con.get("last_120").decode("utf-8")
    pprint.pprint(combinations)
    stocks_list = con.get("last_30").decode("utf-8")

    return JsonResponse({"stocks": stocks_list, "combinations": combinations})


def get_security_info(request, symbol):
    page_num = request.GET.get("page", 1)
    paginator = Paginator(
        Stock.objects.filter(symbol=symbol).order_by("-id"), 10
    )
    stock_result = paginator.page(page_num).object_list
    stock_info = []
    for stock in stock_result:
        stock_info.append(
            {
                "open": stock.open,
                "close": stock.close,
                "low": stock.low,
                "high": stock.high,
                "previous_close": stock.previous_close,
                "date_time": stock.date_time.strftime("%G-%m-%d %H:%M:%S"),
            }
        )

    return JsonResponse(
        {
            "data": stock_info,
            "num_of_pages": paginator.num_pages,
            "total_items": paginator.count,
        }
    )
